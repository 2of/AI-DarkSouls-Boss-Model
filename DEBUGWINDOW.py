import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from datetime import datetime
import vgamepad as vg
import json
import threading
from pathlib import Path
from CV import *
from CE import DarkSoulsCheatWrapper
from Controller import * 
from OpticalFlow import OpticalFlowTracker
from BossDetection import ColorTracker, TemplateTracker, FeatureTracker


class ThingUI:
    def __init__(self, root):
        self.root = root
        self.root.title("DS AI Trainer")
        self.root.geometry("650x950")
        self.root.resizable(True, True)


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



        self.flow_tracker = OpticalFlowTracker(buffer_size=15)
        self.flow_running = False
        self.flow_thread = None
        
        # New trackers
        self.color_tracker = ColorTracker()
        self.template_tracker = TemplateTracker()
        self.feature_tracker = FeatureTracker()
        self.show_template_view = False  # Toggle for viewing current template

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

    def startOpticalFlowCapture(self):
        """Start continuous optical flow capture and display."""
        if self.flow_running:
            return
        
        self.flow_running = True
        self.flow_tracker.reset()
        self.log("🔄 Starting optical flow capture...")
        
        def capture_loop():
            while self.flow_running:
                try:
                    img = get_screencap()
                    cropped_img = clip_window_bar_and_crop(img)
                    
                    # Add frame to tracker
                    self.flow_tracker.add_frame(cropped_img)
                    
                    # Get ML features
                    ml_features = self.flow_tracker.get_ml_features()
                    feature_names = self.flow_tracker.get_feature_names()
                    
                    # Visualize flow on frame
                    vis_frame = self.flow_tracker.visualize_flow(cropped_img)
                    
                    # Draw ML features overlay (compact view)
                    y_pos = 25
                    cv2.putText(vis_frame, "ML FEATURES:", 
                               (10, y_pos), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)
                    y_pos += 20
                    
                    # Row 1: Motion direction/magnitude
                    cv2.putText(vis_frame, 
                               f"X:{ml_features[0]:+.2f} Y:{ml_features[1]:+.2f} Mag:{ml_features[2]:.2f}", 
                               (10, y_pos), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 255, 0), 1)
                    y_pos += 18
                    
                    # Row 2: Quadrant motion
                    cv2.putText(vis_frame, 
                               f"T:{ml_features[5]:.2f} B:{ml_features[6]:.2f} L:{ml_features[7]:.2f} R:{ml_features[8]:.2f}", 
                               (10, y_pos), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 255, 0), 1)
                    y_pos += 18
                    
                    # Row 3: Other features
                    cv2.putText(vis_frame, 
                               f"Area:{ml_features[4]:.2f} Accel:{ml_features[10]:+.2f} Var:{ml_features[11]:.2f}", 
                               (10, y_pos), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 255, 0), 1)
                    
                    
                    # Show the flow visualization
                    if self.show_flow_window_var.get():
                        cv2.imshow("Optical Flow", vis_frame)
                    else:
                        try: 
                            cv2.destroyWindow("Optical Flow")
                        except: 
                            pass

                    # Show boss estimate on the actual game screenshot
                    show_motion = self.show_motion_var.get()
                    boss_vis = self.flow_tracker.draw_boss_estimate(
                        cropped_img, 
                        show_centroid=show_motion, 
                        show_bbox=show_motion, 
                        show_direction=show_motion,
                        label="MOTION"
                    )
                    
                    # 1. Color Tracker
                    if self.color_tracker.active:
                        bbox, mask = self.color_tracker.detect(cropped_img)
                        if bbox and self.show_color_var.get():
                            x, y, w, h = bbox
                            cv2.rectangle(boss_vis, (x, y), (x+w, y+h), (0, 165, 255), 2) # Orange
                            cv2.putText(boss_vis, "COLOR", (x, y-5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 165, 255), 2)
                        
                        if self.show_mask_var.get() and mask is not None:
                            cv2.imshow("Color Mask", mask)
                    elif cv2.getWindowProperty("Color Mask", cv2.WND_PROP_VISIBLE) >= 1:
                         cv2.destroyWindow("Color Mask")

                    # 2. Template Tracker
                    if self.template_tracker.active:
                        bbox, conf = self.template_tracker.detect(cropped_img)
                        if bbox and self.show_template_var.get():
                            x, y, w, h = bbox
                            cv2.rectangle(boss_vis, (x, y), (x+w, y+h), (255, 0, 255), 2) # Pink
                            cv2.putText(boss_vis, f"TMPL ({conf:.2f})", (x, y-5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 255), 2)

                    # 3. Feature Tracker (ORB)
                    if self.feature_tracker.active:
                        bbox, conf = self.feature_tracker.detect(cropped_img)
                        if bbox and self.show_feature_var.get():
                            x, y, w, h = bbox
                            cv2.rectangle(boss_vis, (x, y), (x+w, y+h), (255, 255, 0), 2) # Cyan
                            cv2.putText(boss_vis, f"FEAT ({conf:.2f})", (x, y-5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 2)
                            
                    # Show detailed composite window
                    cv2.imshow("All Detections", boss_vis)
                    
                    # Add position info (Motion)
                    centroid, confidence = self.flow_tracker.get_motion_centroid()
                    if centroid and show_motion:
                        cv2.putText(boss_vis, f"Motion Pos: ({centroid[0]}, {centroid[1]})", 
                                   (10, boss_vis.shape[0] - 40), cv2.FONT_HERSHEY_SIMPLEX, 
                                   0.6, (255, 255, 255), 2)
                        cv2.putText(boss_vis, f"Motion Conf: {confidence:.0%}", 
                                   (10, boss_vis.shape[0] - 15), cv2.FONT_HERSHEY_SIMPLEX, 
                                   0.6, (255, 255, 255), 2)
                    
                    
                    # Also show HSV flow visualization if enabled
                    if self.show_hsv_window_var.get():
                        hsv_vis = self.flow_tracker.visualize_flow_hsv(cropped_img)
                        if hsv_vis.size > 0:
                            cv2.imshow("Flow HSV", hsv_vis)
                    else:
                        try: 
                            cv2.destroyWindow("Flow HSV")
                        except: 
                            pass
                    
                    # Check for quit key
                    key = cv2.waitKey(30) & 0xFF
                    if key == ord('q') or key == 27:  # q or ESC
                        self.flow_running = False
                        break
                        
                except Exception as e:
                    print(f"Optical flow error: {e}")
                    import traceback
                    traceback.print_exc()
                    break
                    
            try: 
                cv2.destroyWindow("Optical Flow")
            except: 
                pass
            try: 
                cv2.destroyWindow("Flow HSV")
            except: 
                pass
            try: 
                cv2.destroyWindow("All Detections")
            except: 
                pass
            try: cv2.destroyWindow("Boss Tracker") # Cleanup old name just in case
            except: pass
            try: cv2.destroyWindow("Color Mask")
            except: pass
            try: cv2.destroyWindow("Current Template")
            except: pass
            self.flow_running = False

        
        self.flow_thread = threading.Thread(target=capture_loop, daemon=True)
        self.flow_thread.start()

    def stopOpticalFlowCapture(self):
        """Stop the optical flow capture loop."""
        self.flow_running = False
        self.log("⏹️ Stopped optical flow capture")

    def captureOneFlowFrame(self):
        """Capture a single frame and show flow analysis."""
        img = get_screencap()
        cropped_img = clip_window_bar_and_crop(img)
        
        self.flow_tracker.add_frame(cropped_img)
        
        motion = self.flow_tracker.get_motion_summary()
        motion_vec = self.flow_tracker.get_motion_vector()
        
        self.log(f"📊 Motion: dir={motion['direction']}°, mag={motion['magnitude']}, vec={motion_vec}")
        
        # Show visualization if we have enough frames
        if self.flow_tracker.get_latest_flow() is not None:
            vis_frame = self.flow_tracker.visualize_flow(cropped_img)
            cv2.imshow("Single Frame Flow", vis_frame)
            cv2.waitKey(0)
            cv2.destroyWindow("Single Frame Flow")

    def _update_flow_param(self, param_name):
        """Update optical flow parameter from slider and refresh label."""
        try:
            if param_name == "buffer_size":
                val = int(self.buffer_size_var.get())
                self.flow_tracker.set_buffer_size(val)
                self.buffer_label.config(text=str(val))
            elif param_name == "winsize":
                val = int(self.winsize_var.get())
                self.flow_tracker.set_winsize(val)
                # Winsize must be odd
                actual = self.flow_tracker.flow_params['winsize']
                self.winsize_label.config(text=str(actual))
            elif param_name == "levels":
                val = int(self.levels_var.get())
                self.flow_tracker.set_levels(val)
                self.levels_label.config(text=str(val))
            elif param_name == "iterations":
                val = int(self.iterations_var.get())
                self.flow_tracker.set_iterations(val)
                self.iter_label.config(text=str(val))
            elif param_name == "motion_threshold":
                val = float(self.motion_thresh_var.get())
                self.flow_tracker.set_motion_threshold(val)
                self.thresh_label.config(text=f"{val:.1f}")
            elif param_name == "vis_scale":
                val = int(self.vis_scale_var.get())
                self.flow_tracker.set_vis_scale(val)
                self.vis_scale_label.config(text=str(val))
            elif param_name == "vis_step":
                val = int(self.vis_step_var.get())
                self.flow_tracker.set_vis_step(val)
                self.vis_step_label.config(text=str(val))
            elif param_name == "resize_scale":
                val = float(self.resize_scale_var.get())
                self.flow_tracker.set_resize_scale(val)
                self.resize_scale_label.config(text=f"{val:.1f}")
            elif param_name == "blur_size":
                val = int(self.blur_size_var.get())
                # Ensure odd
                if val % 2 == 0: val += 1
                self.flow_tracker.set_blur_size(val)
                self.blur_size_label.config(text=str(val))
            elif param_name == "preprocessing":
                val = bool(self.enable_prep_var.get())
                self.flow_tracker.set_enable_preprocessing(val)
        except Exception as e:
            print(f"Error updating flow param {param_name}: {e}")

    # ==========================
    # Boss Detection Callbacks
    # ==========================

    def _update_color_active(self):
        self.color_tracker.active = self.color_active_var.get()

    def _update_hsv_params(self):
        h_min = self.hsv_vars["h_min"].get()
        s_min = self.hsv_vars["s_min"].get()
        v_min = self.hsv_vars["v_min"].get()
        h_max = self.hsv_vars["h_max"].get()
        s_max = self.hsv_vars["s_max"].get()
        v_max = self.hsv_vars["v_max"].get()
        self.color_tracker.set_hsv_range(h_min, s_min, v_min, h_max, s_max, v_max)

    def _update_template_active(self):
        self.template_tracker.active = self.template_active_var.get()
        
    def _update_feature_active(self):
        self.feature_tracker.active = self.feature_active_var.get()

    def capture_template(self):
        """Capture the center of the current screen as a template."""
        try:
            img = get_screencap()
            cropped = clip_window_bar_and_crop(img)
            
            # Take center crop (e.g., 200x200 or smaller)
            h, w = cropped.shape[:2]
            cx, cy = w // 2, h // 2
            size = 100 # 200x200 box
            
            x1 = max(0, cx - size)
            y1 = max(0, cy - size)
            x2 = min(w, cx + size)
            y2 = min(h, cy + size)
            
            template = cropped[y1:y2, x1:x2]
            self.template_tracker.set_template(template)
            self.feature_tracker.set_reference_image(template)
            
            # Show the template in the GUI instead of a cv2 window (prevents freeze)
            # Resize for display thumbnail
            display_h = 100
            scale = display_h / template.shape[0]
            display_w = int(template.shape[1] * scale)
            
            thumb = cv2.resize(template, (display_w, display_h))
            # Convert to RGB for Tkinter
            thumb = cv2.cvtColor(thumb, cv2.COLOR_BGR2RGB)
            from PIL import Image, ImageTk
            img_pil = Image.fromarray(thumb)
            img_tk = ImageTk.PhotoImage(image=img_pil)
            
            # Update label (create if doesn't exist)
            if not hasattr(self, 'template_display_label'):
                self.template_display_label = ttk.Label(self.template_tab)
                self.template_display_label.grid(row=2, column=0, columnspan=2, pady=5)
                
            self.template_display_label.configure(image=img_tk)
            self.template_display_label.image = img_tk # Keep ref
            
            self.show_template_view = True
            print("Template captured.")
            
        except Exception as e:
            print(f"Error capturing template: {e}")
            import traceback
            traceback.print_exc()

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

        # Optical Flow controls
        flow_frame = ttk.LabelFrame(self.root, text="Optical Flow")
        flow_frame.pack(fill="x", padx=10, pady=10)
        
        ttk.Button(flow_frame, text="Start Flow Capture", 
                  command=self.startOpticalFlowCapture).grid(row=0, column=0, padx=5, pady=5)
        ttk.Button(flow_frame, text="Stop Flow Capture", 
                  command=self.stopOpticalFlowCapture).grid(row=0, column=1, padx=5, pady=5)
        ttk.Button(flow_frame, text="Single Frame", 
                  command=self.captureOneFlowFrame).grid(row=0, column=2, padx=5, pady=5)
 
        # Optical Flow Parameters
        flow_params_frame = ttk.LabelFrame(self.root, text="Optical Flow Parameters")
        flow_params_frame.pack(fill="x", padx=10, pady=5)
        
        # Row 0: Buffer Size
        ttk.Label(flow_params_frame, text="Buffer Size:").grid(row=0, column=0, sticky="e", padx=5, pady=2)
        self.buffer_size_var = tk.IntVar(value=15)
        buffer_slider = ttk.Scale(flow_params_frame, from_=2, to=30, orient="horizontal", 
                                  variable=self.buffer_size_var)
        buffer_slider.grid(row=0, column=1, padx=5, sticky="we")
        self.buffer_label = ttk.Label(flow_params_frame, text="15")
        self.buffer_label.grid(row=0, column=2, padx=5)
        self.buffer_size_var.trace_add("write", lambda *_: self._update_flow_param("buffer_size"))
        
        # Row 1: Window Size
        ttk.Label(flow_params_frame, text="Win Size:").grid(row=1, column=0, sticky="e", padx=5, pady=2)
        self.winsize_var = tk.IntVar(value=15)
        winsize_slider = ttk.Scale(flow_params_frame, from_=5, to=51, orient="horizontal",
                                   variable=self.winsize_var)
        winsize_slider.grid(row=1, column=1, padx=5, sticky="we")
        self.winsize_label = ttk.Label(flow_params_frame, text="15")
        self.winsize_label.grid(row=1, column=2, padx=5)
        self.winsize_var.trace_add("write", lambda *_: self._update_flow_param("winsize"))
        
        # Row 2: Pyramid Levels
        ttk.Label(flow_params_frame, text="Pyr Levels:").grid(row=2, column=0, sticky="e", padx=5, pady=2)
        self.levels_var = tk.IntVar(value=3)
        levels_slider = ttk.Scale(flow_params_frame, from_=1, to=10, orient="horizontal",
                                  variable=self.levels_var)
        levels_slider.grid(row=2, column=1, padx=5, sticky="we")
        self.levels_label = ttk.Label(flow_params_frame, text="3")
        self.levels_label.grid(row=2, column=2, padx=5)
        self.levels_var.trace_add("write", lambda *_: self._update_flow_param("levels"))
        
        # Row 3: Iterations
        ttk.Label(flow_params_frame, text="Iterations:").grid(row=3, column=0, sticky="e", padx=5, pady=2)
        self.iterations_var = tk.IntVar(value=3)
        iter_slider = ttk.Scale(flow_params_frame, from_=1, to=10, orient="horizontal",
                                variable=self.iterations_var)
        iter_slider.grid(row=3, column=1, padx=5, sticky="we")
        self.iter_label = ttk.Label(flow_params_frame, text="3")
        self.iter_label.grid(row=3, column=2, padx=5)
        self.iterations_var.trace_add("write", lambda *_: self._update_flow_param("iterations"))
        
        # Row 4: Motion Threshold
        ttk.Label(flow_params_frame, text="Motion Thresh:").grid(row=4, column=0, sticky="e", padx=5, pady=2)
        self.motion_thresh_var = tk.DoubleVar(value=1.0)
        thresh_slider = ttk.Scale(flow_params_frame, from_=0.1, to=10.0, orient="horizontal",
                                  variable=self.motion_thresh_var)
        thresh_slider.grid(row=4, column=1, padx=5, sticky="we")
        self.thresh_label = ttk.Label(flow_params_frame, text="1.0")
        self.thresh_label.grid(row=4, column=2, padx=5)
        self.motion_thresh_var.trace_add("write", lambda *_: self._update_flow_param("motion_threshold"))
        
        # Row 5: Visualization Scale
        ttk.Label(flow_params_frame, text="Arrow Scale:").grid(row=5, column=0, sticky="e", padx=5, pady=2)
        self.vis_scale_var = tk.IntVar(value=3)
        vis_scale_slider = ttk.Scale(flow_params_frame, from_=1, to=10, orient="horizontal",
                                     variable=self.vis_scale_var)
        vis_scale_slider.grid(row=5, column=1, padx=5, sticky="we")
        self.vis_scale_label = ttk.Label(flow_params_frame, text="3")
        self.vis_scale_label.grid(row=5, column=2, padx=5)
        self.vis_scale_var.trace_add("write", lambda *_: self._update_flow_param("vis_scale"))
        
        # Row 6: Arrow Grid Step
        ttk.Label(flow_params_frame, text="Arrow Step:").grid(row=6, column=0, sticky="e", padx=5, pady=2)
        self.vis_step_var = tk.IntVar(value=16)
        vis_step_slider = ttk.Scale(flow_params_frame, from_=4, to=64, orient="horizontal",
                                    variable=self.vis_step_var)
        vis_step_slider.grid(row=6, column=1, padx=5, sticky="we")
        self.vis_step_label = ttk.Label(flow_params_frame, text="16")
        self.vis_step_label.grid(row=6, column=2, padx=5)
        self.vis_step_var.trace_add("write", lambda *_: self._update_flow_param("vis_step"))

        flow_params_frame.columnconfigure(1, weight=1)

        # Preprocessing Controls
        prep_frame = ttk.LabelFrame(self.root, text="Preprocessing")
        prep_frame.pack(fill="x", padx=10, pady=5)
        
        # Checkbox for Enable/Disable
        self.enable_prep_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(prep_frame, text="Enable Preprocessing", 
                       variable=self.enable_prep_var,
                       command=lambda: self._update_flow_param("preprocessing")).grid(row=0, column=0, columnspan=3, padx=5, pady=5)
                       
        # Resize Scale
        ttk.Label(prep_frame, text="Resize Scale:").grid(row=1, column=0, sticky="e", padx=5, pady=2)
        self.resize_scale_var = tk.DoubleVar(value=0.5)
        resize_slider = ttk.Scale(prep_frame, from_=0.1, to=1.0, orient="horizontal",
                                  variable=self.resize_scale_var)
        resize_slider.grid(row=1, column=1, padx=5, sticky="we")
        self.resize_scale_label = ttk.Label(prep_frame, text="0.5")
        self.resize_scale_label.grid(row=1, column=2, padx=5)
        self.resize_scale_var.trace_add("write", lambda *_: self._update_flow_param("resize_scale"))
        
        # Blur Size
        ttk.Label(prep_frame, text="Blur Size:").grid(row=2, column=0, sticky="e", padx=5, pady=2)
        self.blur_size_var = tk.IntVar(value=5)
        blur_slider = ttk.Scale(prep_frame, from_=1, to=15, orient="horizontal",
                                variable=self.blur_size_var)
        blur_slider.grid(row=2, column=1, padx=5, sticky="we")
        self.blur_size_label = ttk.Label(prep_frame, text="5")
        self.blur_size_label.grid(row=2, column=2, padx=5)
        self.blur_size_var.trace_add("write", lambda *_: self._update_flow_param("blur_size"))
        
        prep_frame.columnconfigure(1, weight=1)

        # Boss Detection Controls
        detect_frame = ttk.LabelFrame(self.root, text="Boss Detection Methods")
        detect_frame.pack(fill="x", padx=10, pady=5)
        
        # Notebook for different trackers
        notebook = ttk.Notebook(detect_frame)
        notebook.pack(fill="x", padx=5, pady=5)
        
        # Tab 1: Color Tracker
        color_tab = ttk.Frame(notebook)
        notebook.add(color_tab, text="Color Tracker")
        
        # Active Toggle
        self.color_active_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(color_tab, text="Active", variable=self.color_active_var,
                       command=self._update_color_active).pack(anchor="w")
        self.show_mask_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(color_tab, text="Show Mask", variable=self.show_mask_var).pack(anchor="w")
        
        # HSV Sliders
        hsv_frame = ttk.Frame(color_tab)
        hsv_frame.pack(fill="x")
        
        self.hsv_vars = {}
        labels = ["H Min", "S Min", "V Min", "H Max", "S Max", "V Max"]
        keys = ["h_min", "s_min", "v_min", "h_max", "s_max", "v_max"]
        limits = [179, 255, 255, 179, 255, 255]
        
        for i, (key, label, limit) in enumerate(zip(keys, labels, limits)):
            row = i // 2
            col = (i % 2) * 3
            
            ttk.Label(hsv_frame, text=label).grid(row=row, column=col, padx=2)
            var = tk.IntVar(value=0 if "min" in key else limit)
            self.hsv_vars[key] = var
            scale = ttk.Scale(hsv_frame, from_=0, to=limit, variable=var, orient="horizontal")
            scale.grid(row=row, column=col+1, sticky="we", padx=2)
            lbl = ttk.Label(hsv_frame, text=str(var.get()))
            lbl.grid(row=row, column=col+2, padx=2)
            
            # Update label trace
            def make_update(l=lbl, v=var):
                return lambda *_: l.config(text=str(int(v.get())))
            var.trace_add("write", make_update())
            # Update tracker trace
            var.trace_add("write", lambda *_: self._update_hsv_params())
            
        hsv_frame.columnconfigure(1, weight=1)
        hsv_frame.columnconfigure(4, weight=1)

        # Tab 2: Template Tracker
        self.template_tab = ttk.Frame(notebook)
        notebook.add(self.template_tab, text="Template Match")
        
        # Active Toggle
        self.template_active_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(self.template_tab, text="Active", variable=self.template_active_var,
                       command=self._update_template_active).grid(row=0, column=0, sticky="w")
                       
        ttk.Button(self.template_tab, text="Capture Center as Template", 
                  command=self.capture_template).grid(row=0, column=1, padx=5)
                  
        # Threshold
        ttk.Label(self.template_tab, text="Match Thresh:").grid(row=1, column=0, sticky="e")
        self.template_thresh_var = tk.DoubleVar(value=0.6)
        ttk.Scale(self.template_tab, from_=0.1, to=1.0, variable=self.template_thresh_var,
                  command=lambda v: self.template_tracker.__setattr__('threshold', float(v))).grid(row=1, column=1, sticky="we")

        # Tab 3: Feature Tracker (ORB)
        feature_tab = ttk.Frame(notebook)
        notebook.add(feature_tab, text="Feature Match (ORB)")
        
        ttk.Label(feature_tab, text="Uses same template as Template Match tab").grid(row=0, column=0, columnspan=2, pady=5)
        
        self.feature_active_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(feature_tab, text="Active", variable=self.feature_active_var,
                       command=self._update_feature_active).grid(row=1, column=0, sticky="w")
        
        ttk.Label(feature_tab, text="Min Matches:").grid(row=2, column=0, sticky="e")
        self.feature_match_var = tk.IntVar(value=10)
        ttk.Scale(feature_tab, from_=4, to=50, variable=self.feature_match_var,
                 command=lambda v: self.feature_tracker.__setattr__('min_matches', int(float(v)))).grid(row=2, column=1, sticky="we")

        # Overlay/Visualization Settings
        vis_frame = ttk.LabelFrame(self.root, text="Visualization Controls")
        vis_frame.pack(fill="x", padx=10, pady=5)
        
        # Detection Overlays
        self.show_motion_var = tk.BooleanVar(value=True)
        self.show_color_var = tk.BooleanVar(value=True)
        self.show_template_var = tk.BooleanVar(value=True)
        self.show_feature_var = tk.BooleanVar(value=True)
        
        ttk.Checkbutton(vis_frame, text="Show Motion (Green)", variable=self.show_motion_var).grid(row=0, column=0, sticky="w", padx=5)
        ttk.Checkbutton(vis_frame, text="Show Color (Orange)", variable=self.show_color_var).grid(row=0, column=1, sticky="w", padx=5)
        ttk.Checkbutton(vis_frame, text="Show Template (Pink)", variable=self.show_template_var).grid(row=1, column=0, sticky="w", padx=5)
        ttk.Checkbutton(vis_frame, text="Show Feature (Cyan)", variable=self.show_feature_var).grid(row=1, column=1, sticky="w", padx=5)

        # Window Toggles
        self.show_flow_window_var = tk.BooleanVar(value=False)
        self.show_hsv_window_var = tk.BooleanVar(value=False)
        
        ttk.Checkbutton(vis_frame, text="Show Raw Flow Window", variable=self.show_flow_window_var).grid(row=2, column=0, sticky="w", padx=5)
        ttk.Checkbutton(vis_frame, text="Show Flow HSV Window", variable=self.show_hsv_window_var).grid(row=2, column=1, sticky="w", padx=5)










        
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