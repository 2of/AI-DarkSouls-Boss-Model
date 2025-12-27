import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from datetime import datetime
import vgamepad as vg
import json
from pathlib import Path
from CV import *
from CE import DarkSoulsCheatWrapper
from Controller import * 

class ThingUI:
    def __init__(self, root):
        self.root = root
        self.root.title("DS AI Trainer")
        self.root.geometry("600x680")
        self.root.resizable(False, False)

        self.root.attributes("-topmost", True)

        self.positions_file = Path("positions.json")
        self.positions = self.load_positions()
        self.controller = Controller() 
        try:
            self.GameWrapper = DarkSoulsCheatWrapper()
        except Exception as e:
            print("CE INIT ERROR:", e)
            self.GameWrapper = None

        self.gamepad = vg.VX360Gamepad()

        self.create_widgets()

    def load_positions(self):
        if self.positions_file.exists():
            try:
                with open(self.positions_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading positions.json: {e}")
                return {}
        else:
            default_positions = {
                "asylum_boss": {
                    "name": "Asylum Demon",
                    "x": 0.0,
                    "y": 0.0,
                    "z": 0.0,
                    "description": "Boss fog gate (update coordinates)"
                }
            }
            self.save_positions(default_positions)
            return default_positions
    def MISC_BUTTON_DO(self):
        print("TEST")

        boss_info = self.positions["asylum_boss"]

        # Use float coordinates instead of byte array
        x, y, z = boss_info["x"], boss_info["y"], boss_info["z"]

        self.GameWrapper.teleport(x, y, z)



    def processFrame(self):
        img = get_screencap()
        cropped_img, health_bar, stamina_bar, boss_hp_bar = img_ingest(img)
        stamina_pct = get_fill_from_img(stamina_bar)
        health_pct = get_fill_from_img(health_bar)
        print(f" Stamina: {stamina_pct}% | HP: {health_pct} * 10 %")

    def showHealthStaminaSrc(self):
        img = get_screencap()
        cropped_img, health_bar, stamina_bar, boss_hp_bar = img_ingest(img)
        show_augmented_view(cropped_img)

    def RandomMoveToggleOn():
        pass

    def start_randow_inputs_XINPUT(self):
        pass

    def save_positions(self, positions=None):
        if positions is None:
            positions = self.positions
        
        try:
            with open(self.positions_file, 'w') as f:
                json.dump(positions, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving positions.json: {e}")
            return False

    def create_widgets(self):
        ttk.Label(
            self.root,
            text="DS AI Thing Tool",
            font=("Arial", 16, "bold")
        ).pack(pady=10)

        status_frame = ttk.Frame(self.root)
        status_frame.pack(fill="x", padx=10)

        ttk.Label(status_frame, text="Status:").pack(side="left")
        self.status_var = tk.StringVar(value="Idle")
        ttk.Label(
            status_frame,
            textvariable=self.status_var,
            foreground="blue"
        ).pack(side="left", padx=5)

        ctrl_frame = ttk.Frame(self.root)
        ctrl_frame.pack(pady=10)

        ttk.Button(ctrl_frame, text="Start AI", command=self.start_ai).grid(row=0, column=0, padx=5)
        ttk.Button(ctrl_frame, text="Stop AI", command=self.stop_ai).grid(row=0, column=1, padx=5)

        mem_frame = ttk.LabelFrame(self.root, text="Game Control")
        mem_frame.pack(fill="x", padx=10, pady=10)

        ttk.Label(mem_frame, text="Game Speed:").grid(
            row=0, column=0, sticky="e", padx=5
        )

        self.speed_var = tk.DoubleVar(value=1.0)

        speed_slider = ttk.Scale(
            mem_frame,
            from_=0.0,
            to=3.0,
            orient="horizontal",
            variable=self.speed_var
        )
        speed_slider.grid(row=0, column=1, padx=5, sticky="we")

        self.speed_label = ttk.Label(mem_frame, text="1.00x")
        self.speed_label.grid(row=0, column=2, padx=5)

        ttk.Button(
            mem_frame,
            text="Set Speed",
            command=lambda: self.set_speed(self.speed_var.get())
        ).grid(row=0, column=3, padx=5)

        self.speed_var.trace_add(
            "write",
            lambda *_: self.speed_label.config(
                text=f"{self.speed_var.get():.2f}x"
            )
        )

        ttk.Button(mem_frame, text="Freeze Game", command=self.freeze_game).grid(row=1, column=0, pady=5)
        ttk.Button(mem_frame, text="Resume Game", command=self.resume_game).grid(row=1, column=1, pady=5)
        ttk.Button(mem_frame, text="MISC", command=self.MISC_BUTTON_DO).grid(row=1, column=3, pady=5)




        CV_frame = ttk.LabelFrame(self.root, text="CV ")
        CV_frame.pack(fill="x", padx=10, pady=10)

     
        ttk.Button(CV_frame, text="Capture and process screen cap", command=self.processFrame).grid(row=1, column=0, pady=5)
 
        ttk.Button(CV_frame, text="display src aug", command=self.showHealthStaminaSrc).grid(row=2, column=0, pady=5)
 













        
        teleport_frame = ttk.LabelFrame(self.root, text="Teleport")
        teleport_frame.pack(fill="x", padx=10, pady=10)

        ttk.Label(teleport_frame, text="Saved Position:").grid(row=0, column=0, sticky="e", padx=5, pady=5)
        
        self.position_dropdown_var = tk.StringVar()
        self.position_dropdown = ttk.Combobox(
            teleport_frame,
            textvariable=self.position_dropdown_var,
            state="readonly",
            width=25
        )
        self.position_dropdown.grid(row=0, column=1, columnspan=2, padx=5, pady=5, sticky="we")
        self.update_position_dropdown()

        ttk.Button(
            teleport_frame,
            text="Teleport to Selected",
            command=self.teleport_to_dropdown_position
        ).grid(row=0, column=3, padx=5, pady=5)

        ttk.Label(teleport_frame, text="Manual XYZ:").grid(row=1, column=0, sticky="e", padx=5, pady=5)
        
        coord_frame = ttk.Frame(teleport_frame)
        coord_frame.grid(row=1, column=1, columnspan=2, sticky="we", padx=5)
        
        self.x_var = tk.StringVar(value="0.0")
        self.y_var = tk.StringVar(value="0.0")
        self.z_var = tk.StringVar(value="0.0")
        
        ttk.Label(coord_frame, text="X:").pack(side="left", padx=2)
        ttk.Entry(coord_frame, textvariable=self.x_var, width=8).pack(side="left", padx=2)
        ttk.Label(coord_frame, text="Y:").pack(side="left", padx=2)
        ttk.Entry(coord_frame, textvariable=self.y_var, width=8).pack(side="left", padx=2)
        ttk.Label(coord_frame, text="Z:").pack(side="left", padx=2)
        ttk.Entry(coord_frame, textvariable=self.z_var, width=8).pack(side="left", padx=2)
        
        ttk.Button(
            teleport_frame,
            text="Teleport to XYZ",
            command=self.teleport_to_manual_coords
        ).grid(row=1, column=3, padx=5, pady=5)

        ttk.Button(
            teleport_frame,
            text="Refresh List",
            command=self.refresh_positions
        ).grid(row=2, column=0, columnspan=4, pady=5)

        teleport_frame.columnconfigure(1, weight=1)

        controller = ttk.LabelFrame(self.root, text="Controller Actions")
        controller.pack(padx=10, pady=10)
        self.make_button_CONTROLLER(controller, "Attack", self.controller.attack, 0, 1)
        # self.make_button_CONTROLLER(controller, "Roll", self.controller.roll, 0, 2)
        self.make_button_CONTROLLER(controller, "Guard", self.controller.guard, 0, 3)

        self.make_button_CONTROLLER(controller, "Forward", self.controller.forward, 1, 1)
        self.make_button_CONTROLLER(controller, "Back", self.controller.back, 2, 1)
        self.make_button_CONTROLLER(controller, "Left", self.controller.strafe_left, 1, 0)
        self.make_button_CONTROLLER(controller, "Right", self.controller.strafe_right, 1, 2)

        # Random controls (own row)
        self.make_button_CONTROLLER(controller, "Random Once", self.controller.performRandom, 3, 0)
        self.make_button_CONTROLLER(controller, "Start Random", self.controller.loopRandom, 3, 1)
        self.make_button_CONTROLLER(controller, "Stop Random", self.controller.killrandomLoop, 3, 2)


        log_frame = ttk.LabelFrame(self.root, text="Log")
        log_frame.pack(fill="both", expand=True, padx=10, pady=10)

        self.log_text = tk.Text(log_frame, height=8, state="disabled")
        self.log_text.pack(fill="both", expand=True)

    def make_button_CONTROLLER(self, parent, text, action, r, c):
        btn = ttk.Button(parent, text=text, width=8, command=action)
        btn.grid(row=r, column=c, padx=5, pady=5)


    def press(self, button):
        self.gamepad.press_button(button)
        self.gamepad.update()

    def release(self, button):
        self.gamepad.release_button(button)
        self.gamepad.update()

    def log(self, msg):
        ts = datetime.now().strftime("%H:%M:%S")
        self.log_text.config(state="normal")
        self.log_text.insert("end", f"[{ts}] {msg}\n")
        self.log_text.see("end")
        self.log_text.config(state="disabled")

    def update_position_dropdown(self):
        display_names = []
        for key, data in self.positions.items():
            name = data.get('name', key)
            desc = data.get('description', '')
            display_names.append(f"{key} - {name}")
        
        self.position_dropdown['values'] = display_names
        if display_names:
            self.position_dropdown.current(0)

    def refresh_positions(self):
        self.positions = self.load_positions()
        self.update_position_dropdown()
        self.log(f"✓ Loaded {len(self.positions)} positions from JSON")

    def teleport_to_dropdown_position(self):
        if self.GameWrapper is None:
            self.log("❌ CE not connected")
            return

        selected = self.position_dropdown_var.get()
        if not selected:
            self.log("❌ No position selected")
            return

        position_key = selected.split(' - ')[0]
        
        if position_key not in self.positions:
            self.log(f"❌ Position '{position_key}' not found")
            return

        pos_data = self.positions[position_key]
        x, y, z = pos_data['x'], pos_data['y'], pos_data['z']
        
        self.log(f"📍 Teleporting to {position_key}...")



        boss_info = self.positions[position_key]

        # Use float coordinates instead of byte array
        x, y, z = boss_info["x"], boss_info["y"], boss_info["z"]

        self.GameWrapper.teleport(x, y, z)

        return


        try:
            if self.GameWrapper.teleport(x, y, z):
                self.log(f"✓ Teleported to {position_key}!")
            else:
                self.log("❌ Teleport failed")
        except Exception as e:
            self.log(f"❌ Error: {e}")

    def teleport_to_manual_coords(self):
        if self.GameWrapper is None:
            self.log("❌ CE not connected")
            return

        try:
            x = float(self.x_var.get())
            y = float(self.y_var.get())
            z = float(self.z_var.get())
            
            self.log(f"📍 Teleporting to X={x:.2f}, Y={y:.2f}, Z={z:.2f}...")
            if self.GameWrapper.teleport(x, y, z):
                self.log("✓ Teleported!")
            else:
                self.log("❌ Teleport failed")
        except ValueError:
            self.log("❌ Invalid coordinates - please enter numbers")
        except Exception as e:
            self.log(f"❌ Error: {e}")

    def set_speed(self, speed=None):
        if self.GameWrapper is None:
            self.log("❌ CE not connected")
            return

        try:
            if speed is None:
                speed = float(self.speed_var.get())

            self.GameWrapper.set_speed(speed)
            self.log(f"✓ Game speed set to {speed:.2f}x")
        except ValueError:
            self.log("❌ Invalid speed value")
        except Exception as e:
            self.log(f"❌ CE error: {e}")

    def freeze_game(self):
        self.log("Freezing game...")
        self.set_speed(0.0)

    def resume_game(self):
        self.log("Resuming game...")
        self.set_speed(1.0)

    def start_ai(self):
        self.status_var.set("Running")
        self.log("AI started (placeholder)")

    def stop_ai(self):
        self.status_var.set("Stopped")
        self.log("AI stopped")


if __name__ == "__main__":
    root = tk.Tk()
    ThingUI(root)
    root.mainloop()