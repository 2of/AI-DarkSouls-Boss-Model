import cv2
import numpy as np
from CV import * 

def get_stamina_from_image(img):
    return 2


def get_hp_from_image(img):
    gray_img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Apply a threshold to segment the filled health bar
    _, thresh = cv2.threshold(gray_img, 100, 255, cv2.THRESH_BINARY)

    # Find the contour of the filled area (this assumes the health bar is filled left to right)
    # Get the width of the health bar
    total_width = gray_img.shape[1]

    # Count the number of filled pixels in the health bar
    filled_pixels = np.sum(thresh == 255)

    # Calculate the percentage of health remaining
    health_percentage = (filled_pixels / (total_width * gray_img.shape[0])) * 100

    # Return the health percentage (rounded to 2 decimal places)
    return round(health_percentage, 2)


def get_boss_hp_from_image(img):
    return 3







