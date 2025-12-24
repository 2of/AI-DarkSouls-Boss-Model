# ML Model for Beating the Asylum Demon in Dark Souls Remastered

This repo is a WIP. The goal is to beat the Asylum demon in dark souls remastered. 

if you havent' played before, the asylum demon doesn't require the same complex timing, rolling, iframe or stamina management of other bosses in Dark Souls remastered. Essentially, a player should be able to beat the asylum demon by strafing left or right when the boss is 'attacking' and attacking immediately after and then retreating.  This *should* be a relatively trivial pattern for the model to learn.

This model is not intended to be scalable to any other enemy character in the game. There's Cheat Engine integration to reset to the steps in front of the asylum demon only.

See below for status of this project


**Status:** WIP – Currently just boilerplate and support libraries, Must be run on win, CE 7.6 & latest dark souls remastered

TODO:

1. implement training
2. implement controller
3. How are we going to track the demon? Hmmmm
4. ^ as no requirement for real time as we can pause /resume now, we can yolo or we can just do full image idk. 




Done: 

1. CheatEngine communication w/ python / lua 
2. CV processing for stamina / health

---

## Setup Guide

### 1. Cheat Engine Integration
Cheat Engine is required to **pause/resume the game** and teleport for resets during learning.

**Steps:**
1. Open Cheat Engine and attach it to **Dark Souls Remastered**.
2. Press `Ctrl + Alt + L`.
3. Copy and paste the contents of `CEHook.lua`.

**Notes:**
- `CEHook.lua` / `CE.py` writes to a temporary file in `C:/temp` as a workaround for Lua pipe issues that I had with CE 7.6


For sending commands we just write to the file as below: 




```
    def _send_command(self, cmd: str, wait_for_response=True, timeout=2):
        with open(self.command_file, 'w') as f:
            f.write(cmd)
        
        if not wait_for_response:
            time.sleep(0.05)
            return None
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            if os.path.exists(self.status_file):
                try:
                    with open(self.status_file, 'r') as f:
                        status = f.read().strip()
                    os.remove(self.status_file)
                    return status
                except:
                    pass
            time.sleep(0.01)
        
        return None

```

**Starting positions:** Provided in `Positions.json`, use the x,y,z and method in the cehook.



---

### 2. CV.py
- Captures the Dark Souls Remastered game window.
- Preprocesses the image and crops out the **stamina**, **health**, and **boss health bars** for analysis.

---

### 3. Running the Program
You have two options:

1. **Debug Mode**: Run `./DEBUGWINDOW.py`  
   - Launches a Tkinter window for debugging image capture and bar extraction.

2. **Main Loop**: Run `./main.py`  
   - Starts the main loop for capturing game frames and processing player/boss state. Ubcomment the imshow method to see images if you want

---

## Notes
- No `requirements.txt` is provided. Install dependencies manually (OpenCV, mss, pygetwindow, etc.), ill get to this 
- This is a **work in progress** — current code is primarily boilerplate and support libraries.

---

**Disclaimer:**  
This project is a big WIP.

TODO is all over the place 