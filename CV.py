import cv2
import numpy as np
import mss
import pygetwindow as gw


'''

IMPORTANT
THis is ALL done with the idea that the source image is 1280x720.
If you change this the CV stuff will still work but reporting for stamina / bars/ ui stuff will break


'''

def get_screencap():
    # Find the window
    windows = [w for w in gw.getAllWindows() if "DARK SOULS" in w.title.upper()]
    if not windows:
        raise Exception("Could not find Dark Souls window!")
    window = windows[0]

    # Window geometry
    left, top = window.left, window.top
    width, height = window.width, window.height

    # Capture the full window first
    with mss.mss() as sct:
        monitor = {"top": top, "left": left, "width": width, "height": height}
        screenshot = sct.grab(monitor)
        img = np.array(screenshot)
        img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)

    return img  # Return the full OpenCV image


def clip_window_bar_and_crop(img, top=36, bottom=0, left=24, right=24):
    """Crop pixels from each side."""
    return img[top: img.shape[0]-bottom, left: img.shape[1]-right, :]


def get_health_bar_area(img):
    # Example coordinates: y1:y2, x1:x2
    return img[42:54, 95:271]


def get_stamina_bar_area(img):
    return img[80:100, 20:320]


def get_boss_hp_area(img):
    return img[50:70, 600:1200]  # adjust x coords based on resolution/UI


def soften(img):
    """Remove small noise using median blur."""
    return cv2.medianBlur(img, 15)


def show_img(img, window_name="Image"):
    """Display an image using OpenCV."""
    cv2.imshow(window_name, img)
    cv2.waitKey(0)
    cv2.destroyAllWindows()


if __name__ == "__main__":
    # Get the screenshot
    img = get_screencap()

    # Crop out the Windows title bar and edges
    cropped_img = clip_window_bar_and_crop(img)
    cropped_img = soften(cropped_img)

    # Extract bars
    health_bar = get_health_bar_area(cropped_img)
    stamina_bar = get_stamina_bar_area(cropped_img)
    boss_hp_bar = get_boss_hp_area(cropped_img)

    # Show them individually
    show_img(health_bar, "Player Health")
    show_img(stamina_bar, "Player Stamina")
    show_img(boss_hp_bar, "Boss HP")
