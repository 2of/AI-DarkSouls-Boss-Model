import cv2
import numpy as np
from CV import get_fill_from_img


def get_stamina_from_image(img):
    """Get stamina percentage from the stamina bar image."""
    return get_fill_from_img(img)


def get_hp_from_image(img):
    """Get HP percentage from the health bar image."""
    return get_fill_from_img(img)


def get_boss_hp_from_image(img):
    """Get boss HP percentage from the boss HP bar image."""
    return get_fill_from_img(img)



