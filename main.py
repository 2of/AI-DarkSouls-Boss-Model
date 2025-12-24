from CV import *
from CE import *
from helpers import * 
FREQ = 1


def get_images():
    img = get_screencap()

    cropped_img = clip_window_bar_and_crop(img)
    cropped_img = soften(cropped_img)

    # Extract bars
    health_bar = get_health_bar_area(cropped_img)
    stamina_bar = get_stamina_bar_area(cropped_img)
    boss_hp_bar = get_boss_hp_area(cropped_img)




    return (cropped_img,health_bar,stamina_bar,boss_hp_bar)


def mainloop(GameWrapper):
    """
    Main loop to capture Dark Souls UI and read player/boss stats.
    """

    frame  = 0 
    while True:
        # Pause the game to safely capture the screen
        GameWrapper.pause()
        frame += 1
        print("[INFO] Game paused for capture...")

        # Grab all relevant images (full screen + bars)
        cropped_img, health_bar, stamina_bar, boss_hp_bar = get_images()

        # Extract numeric values from each bar
        stamina_pct = get_stamina_from_image(stamina_bar)
        hp_pct = get_hp_from_image(health_bar)
        boss_hp_pct = get_boss_hp_from_image(boss_hp_bar)

        # Pretty print the results
        print(
             f"[FRAME] {frame}% | "
            f"[STATUS] Player HP: {hp_pct}% | "
              f"Stamina: {stamina_pct}% | "
              f"Boss HP: {boss_hp_pct}%")

        # Optional: show the bar images for debugging
        show_img(health_bar, "Health")
        show_img(cropped_img)
        # show_img(stamina_bar, "Stamina")
        # show_img(boss_hp_bar, "Boss HP")
        time.sleep(FREQ) # JUST HERE FOR DEBUGGGS

        # Resume the game
        GameWrapper.resume()
        print("[INFO] Game resumed.")

        # Wait a bit before the next iteration
        time.sleep(FREQ)

if __name__ == "__main__":
    GameWrapper = DarkSoulsCheatWrapper()


    mainloop(GameWrapper)
