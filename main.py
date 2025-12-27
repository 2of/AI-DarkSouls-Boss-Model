from CV import *
from CE import *
from helpers import * 
from ML import * 
from Controller import * 
FREQ = 2


import time
import threading
from queue import Queue


class GameController:
    def __init__(self, GameWrapper, Controller, MLWrapper):
        self.GameWrapper = GameWrapper
        self.Controller = Controller
        self.MLWrapper = MLWrapper
        self.command_queue = Queue()
        self.running = True

    def get_img(self):
        img = get_screencap()

        return img

    def process_frame(self, frame):
        """
        Capture the screen, process bars, and extract stats.
        """
        img = self.get_img()


        cropped_img, health_bar, stamina_bar, boss_hp_bar = img_ingest(img)

        # Extract numeric values from each bar
        stamina_pct = get_stamina_from_image(stamina_bar)
        # hp_pct = get_hp_from_image(health_bar)
        # boss_hp_pct = get_boss_hp_from_image(boss_hp_bar)

        print(f"[FRAME {frame}] Player HP: {1}% | Stamina: {stamina_pct}% | Boss HP: {1}%")



        # BUGGER FRAMES IDK 
        nextMove = self.MLWrapper.getmove(v=[stamina_pct, 1, 1])

        self.command_queue.put(nextMove)

    def action_executor(self):
        """
        Thread for executing queued actions in parallel.
        """
        while self.running:
            if not self.command_queue.empty():
                nextMove = self.command_queue.get()
                print(f"Executing move: {nextMove}")
                self.Controller.perform(nextMove)
                time.sleep(FREQ) 
            else:
                time.sleep(0.05)  
    def mainloop(self):
        """
        Main loop to capture Dark Souls UI and read player/boss stats.
        """
        frame = 0
        action_thread = threading.Thread(target=self.action_executor, daemon=True)
        action_thread.start()

        while self.running:
            self.GameWrapper.pause()

            frame += 1
            print(f"[INFO] Frame {frame}: Capturing screen...")


            self.process_frame(frame)

            self.GameWrapper.resume()
            print("[INFO] Game resumed.")


            time.sleep(0.1)  # Some latency to let the move play

    def stop(self):
        """
        Gracefully stop the main loop and any active threads.
        """
        self.running = False


if __name__ == "__main__":
    # Initialize GameWrapper, Controller, MLWrapper
    GameWrapper = DarkSoulsCheatWrapper()
    Controller = Controller()
    MLWrapper = MLWrapper(Controller)

    game_controller = GameController(GameWrapper, Controller, MLWrapper)
    try:
        game_controller.mainloop()
    except KeyboardInterrupt:
        print("Stopping game controller...")
        game_controller.stop()
