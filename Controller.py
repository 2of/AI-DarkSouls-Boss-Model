import time
import threading
import random
import vgamepad as vg


class Controller:
    def __init__(self):
        self.gamepad = vg.VX360Gamepad()
        self.pressTime = 1.5
        self.loop_delay = 0.6
        self._looping = False
        self._loop_thread = None

        # Random action pool
        self.actionpool = {
            "attack": self.attack,
            "guard": self.guard,
            "roll_forward": self.roll_forward,
            "roll_back": self.roll_back,
            "roll_left": self.roll_left,
            "roll_right": self.roll_right,
            "strafe_left": self.strafe_left,
            "strafe_right": self.strafe_right,
            "forward": self.forward,
            "back": self.back,
        }

    # All actions as a list of tuples (action_name, action_method)
    def get_all_actions(self):
        return list(self.actionpool.keys())

    # ------------------
    # Perform actions (directed)
    # ------------------

    def perform(self, movename):
        movename = movename.strip().lower()

        if movename not in self.actionpool:
            print("Invalid move:", movename)
            return

        print("NOW DOING ACTION:", movename)
        self.actionpool[movename]()

    # ------------------
    # Basic actions (non-directional)
    # ------------------

    def attack(self):
        self.gamepad.press_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_SHOULDER)
        self.gamepad.update()
        time.sleep(self.pressTime)
        self.gamepad.release_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_SHOULDER)
        self.gamepad.update()

    def guard(self):
        self.gamepad.press_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_LEFT_SHOULDER)
        self.gamepad.update()
        time.sleep(self.pressTime * 2)
        self.gamepad.release_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_LEFT_SHOULDER)
        self.gamepad.update()

    # ------------------
    # Movement actions (non-roll)
    # ------------------

    def strafe_right(self):
        self.gamepad.left_joystick(x_value=32767, y_value=0)
        self.gamepad.update()
        time.sleep(self.pressTime)
        self._reset_stick()

    def strafe_left(self):
        self.gamepad.left_joystick(x_value=-32768, y_value=0)
        self.gamepad.update()
        time.sleep(self.pressTime)
        self._reset_stick()

    def forward(self):
        self.gamepad.left_joystick(x_value=0, y_value=32767)
        self.gamepad.update()
        time.sleep(self.pressTime)
        self._reset_stick()

    def back(self):
        self.gamepad.left_joystick(x_value=0, y_value=-32768)
        self.gamepad.update()
        time.sleep(self.pressTime)
        self._reset_stick()

    def _reset_stick(self):
        self.gamepad.left_joystick(x_value=0, y_value=0)
        self.gamepad.update()

    # ------------------
    # Directional Roll Actions
    # ------------------

    def _roll_with_direction(self, x, y):
        # Set direction (left joystick)
        self.gamepad.left_joystick(x_value=x, y_value=y)
        self.gamepad.update()

        # Small delay to register the direction before pressing roll
        time.sleep(0.05)

        # Press roll (B button)
        self.gamepad.press_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_B)
        self.gamepad.update()

        time.sleep(self.pressTime)

        self.gamepad.release_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_B)
        self._reset_stick()

    def roll_forward(self):
        self._roll_with_direction(0, 32767)

    def roll_back(self):
        self._roll_with_direction(0, -32768)

    def roll_left(self):
        self._roll_with_direction(-32768, 0)

    def roll_right(self):
        self._roll_with_direction(32767, 0)
    

    # ------------------
    # Random behavior (choosing random actions)
    # ------------------

    def performRandom(self):
        action = random.choice(list(self.actionpool.values()))
        action()

    def loopRandom(self):
        if self._looping:
            return

        self._looping = True

        def loop():
            while self._looping:
                self.performRandom()
                time.sleep(self.loop_delay)

        self._loop_thread = threading.Thread(target=loop, daemon=True)
        self._loop_thread.start()

    def killrandomLoop(self):
        self._looping = False


