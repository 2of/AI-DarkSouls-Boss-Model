"""
OpticalFlow.py - Optical flow tracking for Dark Souls boss movement analysis

Uses Farneback dense optical flow to track movement between frames.
Maintains a frame buffer to enable multi-frame flow analysis.
"""

import cv2
import numpy as np
from collections import deque

class OpticalFlowTracker:
    def __init__(self, buffer_size=15):
        self.buffer_size = buffer_size
        self.frame_buffer = deque(maxlen=buffer_size)
        self.flow_buffer = deque(maxlen=buffer_size - 1)
        
        # Parameters
        self.flow_params = dict(pyr_scale=0.5, levels=3, winsize=15, iterations=3, 
                                poly_n=5, poly_sigma=1.2, flags=0)
        
        self.vis_scale = 3
        self.vis_step = 16
        self.motion_threshold = 1.0
        
        self.resize_scale = 0.5
        self.blur_size = 5
        self.enable_preprocessing = True
        
        self.original_size = None
        self.roi = None
        self.processed_size = None

    # --- Concise Setters ---
    def set_buffer_size(self, size): 
        self.buffer_size = max(2, size)
        self.frame_buffer = deque(maxlen=self.buffer_size)
        self.flow_buffer = deque(maxlen=self.buffer_size - 1)
        
    def set_pyr_scale(self, v): self.flow_params['pyr_scale'] = max(0.1, min(0.99, v))
    def set_levels(self, v): self.flow_params['levels'] = max(1, min(10, int(v)))
    def set_winsize(self, v): self.flow_params['winsize'] = v + 1 if (v := max(5, int(v))) % 2 == 0 else v
    def set_iterations(self, v): self.flow_params['iterations'] = max(1, min(10, int(v)))
    def set_poly_n(self, v): self.flow_params['poly_n'] = 7 if v >= 6 else 5
    def set_poly_sigma(self, v): self.flow_params['poly_sigma'] = max(0.5, min(2.0, v))
    def set_motion_threshold(self, v): self.motion_threshold = max(0.1, v)
    def set_vis_scale(self, v): self.vis_scale = max(1, v)
    def set_vis_step(self, v): self.vis_step = max(4, min(64, int(v)))
    def set_resize_scale(self, v): self.resize_scale = max(0.1, min(1.0, float(v)))
    def set_blur_size(self, v): self.blur_size = v + 1 if (v := max(1, int(v))) % 2 == 0 else v
    def set_enable_preprocessing(self, v): self.enable_preprocessing = bool(v)
    def set_roi(self, x1, y1, x2, y2): self.roi = (x1, y1, x2, y2)
    def clear_roi(self): self.roi = None

    def get_params(self):
        return {**self.flow_params, 'buffer_size': self.buffer_size, 
                'motion_threshold': self.motion_threshold, 'vis_scale': self.vis_scale, 
                'vis_step': self.vis_step, 'resize_scale': self.resize_scale, 'blur_size': self.blur_size}

    # --- Internals ---
    def _scale(self, v): return int(v / self.resize_scale) if self.resize_scale not in (1.0, 0) else v
    
    def map_to_original_coords(self, x, y):
        """Map coordinates from processed (resized) space back to original frame."""
        return self._scale(x), self._scale(y)

    def _process_frame(self, frame):
        self.original_size = frame.shape[:2][::-1]
        proc = frame
        
        if self.enable_preprocessing:
            if self.resize_scale != 1.0:
                h, w = proc.shape[:2]
                proc = cv2.resize(proc, (int(w * self.resize_scale), int(h * self.resize_scale)), 
                                interpolation=cv2.INTER_AREA)
        
        if len(proc.shape) == 3:
            proc = cv2.cvtColor(proc, cv2.COLOR_BGR2GRAY)
            
        if self.enable_preprocessing and self.blur_size > 1:
            k = self.blur_size
            proc = cv2.GaussianBlur(proc, (k, k), 0)
            
        if self.roi:
            x1, y1, x2, y2 = self.roi
            if self.resize_scale != 1.0:
                x1, y1, x2, y2 = [int(v * self.resize_scale) for v in (x1, y1, x2, y2)]
            proc = proc[y1:y2, x1:x2]
            
        self.processed_size = proc.shape[:2][::-1]
        return proc

    def add_frame(self, frame):
        """Add frame to buffer and compute flow."""
        gray = self._process_frame(frame)
        self.frame_buffer.append(gray)
        
        if len(self.frame_buffer) >= 2:
            prev, curr = self.frame_buffer[-2], self.frame_buffer[-1]
            if prev.shape != curr.shape:
                self.frame_buffer.clear(); self.frame_buffer.append(gray)
                return None
            
            flow = cv2.calcOpticalFlowFarneback(prev, curr, None, **self.flow_params)
            self.flow_buffer.append(flow)
            return flow
        return None
    
    def get_latest_flow(self):
        return self.flow_buffer[-1] if self.flow_buffer else None
    
    def reset(self):
        self.frame_buffer.clear()
        self.flow_buffer.clear()

    # --- Analysis & Visualization ---
    def get_motion_summary(self):
        flow = self.get_latest_flow()
        if flow is None: return {'direction': 0, 'magnitude': 0, 'max_magnitude': 0, 'motion_area': 0}
            
        mag, ang = cv2.cartToPolar(flow[..., 0], flow[..., 1])
        mask = mag > self.motion_threshold
        
        if np.any(mask):
            avg_dir = np.mean(ang[mask] * 180 / np.pi)
            avg_mag = np.mean(mag[mask])
        else:
            avg_dir = avg_mag = 0
            
        return {
            'direction': round(avg_dir, 1),
            'magnitude': round(avg_mag, 2),
            'max_magnitude': round(np.max(mag), 2),
            'motion_area': round((np.sum(mask) / mag.size) * 100, 1)
        }
    
    def get_motion_vector(self):
        flow = self.get_latest_flow()
        if flow is None: return (0, 0)
        
        mag = np.sqrt(flow[..., 0]**2 + flow[..., 1]**2)
        mask = mag > self.motion_threshold
        
        if np.any(mask):
            return (round(np.mean(flow[..., 0][mask]), 2), round(np.mean(flow[..., 1][mask]), 2))
        return (0, 0)
    
    def get_ml_features(self):
        """Extract a 12-dim feature vector for ML."""
        flow = self.get_latest_flow()
        if flow is None: return np.zeros(12, dtype=np.float32)
        
        h, w = flow.shape[:2]
        mag = np.sqrt(flow[..., 0]**2 + flow[..., 1]**2)
        mask = mag > self.motion_threshold
        
        # Features 0-4
        if np.any(mask):
            mx, my, mm = np.mean(flow[..., 0][mask]), np.mean(flow[..., 1][mask]), np.mean(mag[mask])
        else:
            mx, my, mm = 0, 0, 0
            
        max_m = 50.0
        f0_2 = [np.clip(mx/max_m, -1, 1), np.clip(my/max_m, -1, 1), np.clip(mm/max_m, 0, 1)]
        f3 = (np.arctan2(my, mx) + np.pi) / (2 * np.pi) if mm > 0 else 0
        f4 = np.sum(mask) / mask.size
        
        # Quadrants 5-9
        mid_h, mid_w, q_h, q_w = h // 2, w // 2, h // 4, w // 4
        quads = [
            np.mean(mag[:mid_h, :]), np.mean(mag[mid_h:, :]), # Top, Bot
            np.mean(mag[:, :mid_w]), np.mean(mag[:, mid_w:]), # Left, Right
            np.mean(mag[q_h:3*q_h, q_w:3*q_w]) # Center
        ]
        f5_9 = [np.clip(q/max_m, 0, 1) for q in quads]
        
        # Acceleration (10)
        acc = 0
        if len(self.flow_buffer) >= 2:
            prev = self.flow_buffer[-2]
            pm = np.sqrt(prev[..., 0]**2 + prev[..., 1]**2)
            p_avg = np.mean(pm[pm > self.motion_threshold]) if np.any(pm > self.motion_threshold) else 0
            acc = np.clip((mm - p_avg) / max_m, -1, 1)
            
        # Variance (11)
        var = np.clip(np.std(mag[mask]), 0, 1) if np.any(mask) else 0
        
        return np.array([*f0_2, f3, f4, *f5_9, acc, var], dtype=np.float32)
    
    def get_feature_names(self):
        return ['motion_x', 'motion_y', 'motion_mag', 'motion_dir', 'motion_area', 
                'top', 'bottom', 'left', 'right', 'center', 'accel', 'var']

    def get_motion_centroid(self):
        """Weighted centroid of motion."""
        flow = self.get_latest_flow()
        if flow is None: return None, 0
        
        h, w = flow.shape[:2]
        mag = np.sqrt(flow[..., 0]**2 + flow[..., 1]**2)
        mask = mag > self.motion_threshold
        
        if np.sum(mask) < 10: return None, 0
        
        y_coords, x_coords = np.mgrid[0:h, 0:w]
        weights = mag ** 2
        weights[~mask] = 0
        total = np.sum(weights)
        if total == 0: return None, 0
        
        cx = np.sum(x_coords * weights) / total
        cy = np.sum(y_coords * weights) / total
        
        if self.roi: cx += self.roi[0]; cy += self.roi[1]
        
        conf = max(0, 1 - (np.sum(mask)/mask.size) * 5)
        return (int(cx), int(cy)), conf
    
    def get_motion_bounding_box(self, padding=20):
        flow = self.get_latest_flow()
        if flow is None: return None
        
        h, w = flow.shape[:2]
        mask = np.sum(flow**2, axis=2) > self.motion_threshold**2
        
        if np.sum(mask) < 10: return None
        
        rows = np.any(mask, axis=1)
        cols = np.any(mask, axis=0)
        y1, y2 = np.where(rows)[0][[0, -1]]
        x1, x2 = np.where(cols)[0][[0, -1]]
        
        # Add ROI offset
        off_x, off_y = self.roi[:2] if self.roi else (0, 0)
        
        return (max(0, x1 - padding) + off_x, max(0, y1 - padding) + off_y, 
                min(w - 1, x2 + padding) + off_x, min(h - 1, y2 + padding) + off_y)
    
    def draw_boss_estimate(self, frame, show_centroid=True, show_bbox=True, 
                           show_direction=True, label="BOSS?"):
        vis = frame.copy()
        cent, conf = self.get_motion_centroid()
        bbox = self.get_motion_bounding_box()
        mvec = self.get_motion_vector()
        
        col = (0, int(255 * conf), int(255 * (1 - conf)))
        
        if bbox and show_bbox:
            x1, y1, x2, y2 = bbox
            if self.resize_scale != 1.0:
                x1, y1 = self._scale(x1), self._scale(y1)
                x2, y2 = self._scale(x2), self._scale(y2)
            cv2.rectangle(vis, (x1, y1), (x2, y2), col, 2)
            cv2.putText(vis, f"{label} ({conf:.0%})", (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, col, 2)
        
        if cent and show_centroid:
            cx, cy = cent
            if self.resize_scale != 1.0: cx, cy = self._scale(cx), self._scale(cy)
            
            # Crosshair
            cv2.line(vis, (cx - 15, cy), (cx + 15, cy), col, 2)
            cv2.line(vis, (cx, cy - 15), (cx, cy + 15), col, 2)
            cv2.circle(vis, (cx, cy), 8, col, 2)
            
            if show_direction and (mvec[0] or mvec[1]):
                mx, my = mvec
                if self.resize_scale != 1.0: mx /= self.resize_scale; my /= self.resize_scale
                cv2.arrowedLine(vis, (cx, cy), (int(cx + mx * 5), int(cy + my * 5)), (255, 255, 0), 3, tipLength=0.3)
                
        return vis

    def visualize_flow(self, frame, scale=None, step=None):
        flow = self.get_latest_flow()
        if flow is None: return frame.copy()
        
        scale = scale or self.vis_scale
        step = step or self.vis_step
        vis = frame.copy()
        h, w = flow.shape[:2]
        off_x, off_y = self.roi[:2] if self.roi else (0, 0)
        
        # Grid loop
        y_grid, x_grid = np.mgrid[0:h:step, 0:w:step]
        for y, x in zip(y_grid.flatten(), x_grid.flatten()):
            fx, fy = flow[y, x]
            if fx*fx + fy*fy > self.motion_threshold**2:
                sx, sy = x + off_x, y + off_y
                if self.resize_scale != 1.0:
                    sx, sy = self._scale(sx), self._scale(sy)
                    fx /= self.resize_scale; fy /= self.resize_scale
                
                # HSV color
                hue = int((np.arctan2(fy, fx) + np.pi) * 90 / np.pi)
                col = tuple(map(int, cv2.cvtColor(np.uint8([[[hue, 255, 255]]]), cv2.COLOR_HSV2BGR)[0][0]))
                
                cv2.arrowedLine(vis, (sx, sy), (int(sx + fx * scale), int(sy + fy * scale)), col, 1, tipLength=0.3)
        return vis

    def visualize_flow_hsv(self, frame):
        flow = self.get_latest_flow()
        if flow is None: return np.zeros_like(frame)
        
        mag, ang = cv2.cartToPolar(flow[..., 0], flow[..., 1])
        hsv = np.zeros((*flow.shape[:2], 3), dtype=np.uint8)
        hsv[..., 0] = ang * 180 / np.pi / 2
        hsv[..., 1] = 255
        hsv[..., 2] = cv2.normalize(mag, None, 0, 255, cv2.NORM_MINMAX)
        return cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)

# Test/Utility
def compute_optical_flow(prev, curr):
    if len(prev.shape) == 3: prev = cv2.cvtColor(prev, cv2.COLOR_BGR2GRAY)
    if len(curr.shape) == 3: curr = cv2.cvtColor(curr, cv2.COLOR_BGR2GRAY)
    return cv2.calcOpticalFlowFarneback(prev, curr, None, 0.5, 3, 15, 3, 5, 1.2, 0)

if __name__ == "__main__":
    print("OpticalFlow module loaded.")
