import cv2
import numpy as np

class ColorTracker:
    def __init__(self):
        # Default to a broad range, can be tuned via UI
        # Asylum Demon is grayish/brownish
        self.lower_hsv = np.array([0, 0, 0]) 
        self.upper_hsv = np.array([179, 255, 255])
        self.kernel_size = 5
        self.min_area = 500
        self.active = False

    def set_hsv_range(self, h_min, s_min, v_min, h_max, s_max, v_max):
        self.lower_hsv = np.array([h_min, s_min, v_min])
        self.upper_hsv = np.array([h_max, s_max, v_max])

    def detect(self, frame):
        if not self.active:
            return None, None
            
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        mask = cv2.inRange(hsv, self.lower_hsv, self.upper_hsv)
        
        # Morphological ops to clean up noise
        kernel = np.ones((self.kernel_size, self.kernel_size), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
        
        # Find largest contour
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if not contours:
            return None, mask
            
        c = max(contours, key=cv2.contourArea)
        if cv2.contourArea(c) < self.min_area:
            return None, mask
            
        x, y, w, h = cv2.boundingRect(c)
        return (x, y, w, h), mask

class TemplateTracker:
    def __init__(self):
        self.template = None
        self.template_h = 0
        self.template_w = 0
        self.threshold = 0.6
        self.scales = [0.5, 0.75, 1.0, 1.25, 1.5] # Multiscale matching
        self.active = False
        
    def set_template(self, image_patch):
        if image_patch is None or image_patch.size == 0:
            return
        
        # Convert to grayscale for matching
        if len(image_patch.shape) == 3:
            self.template = cv2.cvtColor(image_patch, cv2.COLOR_BGR2GRAY)
        else:
            self.template = image_patch
            
        self.template_h, self.template_w = self.template.shape[:2]
        print(f"Template set: {self.template_w}x{self.template_h}")

    def detect(self, frame):
        if not self.active or self.template is None:
            return None, None

        if len(frame.shape) == 3:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        else:
            gray = frame

        found = None
        
        # Loop over scales
        for scale in self.scales:
            # Resize image according to scale
            resized = cv2.resize(gray, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA)
            r = gray.shape[1] / float(resized.shape[1])

            # If resized image is smaller than template, break
            if resized.shape[0] < self.template_h or resized.shape[1] < self.template_w:
                break
                
            # Match template
            result = cv2.matchTemplate(resized, self.template, cv2.TM_CCOEFF_NORMED)
            (_, maxVal, _, maxLoc) = cv2.minMaxLoc(result)

            # Check if this scale is the best so far
            if found is None or maxVal > found[0]:
                found = (maxVal, maxLoc, r)

        if found is None:
            return None, None

        (maxVal, maxLoc, r) = found
        
        if maxVal < self.threshold:
            return None, None

        # Compute bounding box in original image coords
        (startX, startY) = (int(maxLoc[0] * r), int(maxLoc[1] * r))
        return (startX, startY, endX - startX, endY - startY), maxVal

class FeatureTracker:
    def __init__(self):
        self.orb = cv2.ORB_create(nfeatures=1000)
        self.bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=False) # Use ratio test, so crossCheck=False
        self.kp_ref = None
        self.des_ref = None
        self.ref_h = 0
        self.ref_w = 0
        self.min_matches = 10
        self.active = False
        
    def set_reference_image(self, image_patch):
        if image_patch is None or image_patch.size == 0:
            return
            
        # Convert to grayscale
        if len(image_patch.shape) == 3:
            gray = cv2.cvtColor(image_patch, cv2.COLOR_BGR2GRAY)
        else:
            gray = image_patch
        
        # Detect features
        self.kp_ref, self.des_ref = self.orb.detectAndCompute(gray, None)
        self.ref_h, self.ref_w = gray.shape[:2]
        
        print(f"Feature Tracker: {len(self.kp_ref)} features in reference.")
        
    def detect(self, frame):
        if not self.active or self.des_ref is None or len(self.kp_ref) < self.min_matches:
            return None, 0
            
        if len(frame.shape) == 3:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        else:
            gray = frame
            
        # Detect features in current frame
        kp_curr, des_curr = self.orb.detectAndCompute(gray, None)
        
        if des_curr is None or len(kp_curr) < self.min_matches:
            return None, 0
            
        # Match descriptors
        matches = self.bf.knnMatch(self.des_ref, des_curr, k=2)
        
        # Apply ratio test
        good = []
        for m, n in matches:
            if m.distance < 0.75 * n.distance:
                good.append(m)
                
        if len(good) < self.min_matches:
            return None, len(good)
            
        # Homography to find object
        src_pts = np.float32([ self.kp_ref[m.queryIdx].pt for m in good ]).reshape(-1,1,2)
        dst_pts = np.float32([ kp_curr[m.trainIdx].pt for m in good ]).reshape(-1,1,2)
        
        M, mask = cv2.findHomography(src_pts, dst_pts, cv2.RANSAC, 5.0)
        
        if M is None:
            return None, len(good)
            
        h, w = self.ref_h, self.ref_w
        pts = np.float32([ [0,0], [0,h-1], [w-1,h-1], [w-1,0] ]).reshape(-1,1,2)
        dst = cv2.perspectiveTransform(pts, M)
        
        # Get bounding rect from warped points
        x, y, w, h = cv2.boundingRect(dst)
        
        # Simple confidence based on match count vs min req
        confidence = min(1.0, len(good) / (self.min_matches * 3))
        
        return (x, y, w, h), confidence
