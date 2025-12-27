import cv2
import numpy as np
import mss
import pygetwindow as gw


'''
IMPORTANT
This assumes 1280x720 AFTER window cropping.
'''



WINDOW_CROP = {
    "top": 36,
    "bottom": 0,
    "left": 24,
    "right": 24
}

HEALTH_BAR_BOX = (44, 45, 95, 271)      # y1, y2, x1, x2
STAMINA_BAR_BOX = (56, 61, 96, 204)
BOSS_HP_BAR_BOX = (50, 70, 600, 1200)




def get_screencap():
    windows = [w for w in gw.getAllWindows() if "DARK SOULS" in w.title.upper()]
    if not windows:
        raise Exception("Could not find Dark Souls window!")

    window = windows[0]

    with mss.mss() as sct:
        monitor = {
            "top": window.top,
            "left": window.left,
            "width": window.width,
            "height": window.height
        }
        screenshot = sct.grab(monitor)
        img = np.array(screenshot)
        img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)

    return img



def clip_window_bar_and_crop(img):
    return img[
        WINDOW_CROP["top"]: img.shape[0] - WINDOW_CROP["bottom"],
        WINDOW_CROP["left"]: img.shape[1] - WINDOW_CROP["right"],
        :
    ]


def soften(img):
    return cv2.medianBlur(img, 15)


def show_img(img, window_name="Image"):
    cv2.imshow(window_name, img)
    cv2.waitKey(0)
    cv2.destroyAllWindows()




def get_health_bar_area(img):
    y1, y2, x1, x2 = HEALTH_BAR_BOX
    return img[y1:y2, x1:x2]


def get_stamina_bar_area(img):
    y1, y2, x1, x2 = STAMINA_BAR_BOX
    return img[y1:y2, x1:x2]


def get_boss_hp_area(img):
    y1, y2, x1, x2 = BOSS_HP_BAR_BOX
    return img[y1:y2, x1:x2]







def img_ingest(img):
    # show_img(img, "Full Image")
    cropped_img = clip_window_bar_and_crop(img)
    # show_img(cropped_img, "Cropped Image")
    # cropped_img = soften(cropped_img)
    
    health_bar = get_health_bar_area(cropped_img)
    stamina_bar = get_stamina_bar_area(cropped_img)
    boss_hp_bar = get_boss_hp_area(cropped_img)
    
    # show_img(health_bar, "Health Bar")
    # show_img(stamina_bar, "Stamina Bar")
    # show_img(boss_hp_bar, "Boss HP Bar")
    # show_augmented_view(cropped_img)

    return cropped_img, health_bar, stamina_bar, boss_hp_bar



def show_augmented_view(img):
    overlay = img.copy()

    def draw_box(box, color, label):
        y1, y2, x1, x2 = box
        cv2.rectangle(overlay, (x1, y1), (x2, y2), color, 2)
        cv2.putText(
            overlay,
            label,
            (x1, y1 - 6),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.4,
            color,
            1,
            cv2.LINE_AA
        )

    draw_box(HEALTH_BAR_BOX, (0, 0, 255), "Health")
    draw_box(STAMINA_BAR_BOX, (0, 255, 0), "Stamina")
    draw_box(BOSS_HP_BAR_BOX, (255, 0, 0), "Boss HP")

    cv2.imshow("Augmented View", overlay)
    cv2.waitKey(0)
    cv2.destroyAllWindows()



def get_fill_from_img(img,show = False):
    """
    Returns the percentage of the health bar that is filled.
    Expects 'img' to be the cropped health bar area.
    """

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    if show: 
        show_img(gray)
    _, thresh = cv2.threshold(gray, 90, 255, cv2.THRESH_BINARY)
    if show: 
        show_img(thresh)
    filled_pixels = np.sum(thresh == 255)


    total_pixels = gray.shape[0] * gray.shape[1]
    health_pct = (filled_pixels / total_pixels) * 100

    return round(health_pct, 2)


if __name__ == "__main__":
    img = get_screencap()
    cropped = clip_window_bar_and_crop(img)
    cropped = soften(cropped)

    health_bar = get_fill_from_img(cropped)
    stamina_bar = get_stamina_bar_area(cropped)
    boss_hp_bar = get_boss_hp_area(cropped)

    # Debug / analysis
    stamina_pct = img_get_stamina(stamina_bar)
    print("Stamina %:", stamina_pct)

    # Visual validation
    show_augmented_view(cropped)
