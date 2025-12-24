import os
import time
from pathlib import Path
from typing import Tuple, Optional, List

class DarkSoulsCheatWrapper:
    def __init__(self, command_file=r"C:\temp\ce_commands.txt", 
                 status_file=r"C:\temp\ce_status.txt"):
        self.command_file = command_file
        self.status_file = status_file
        
        os.makedirs(os.path.dirname(command_file), exist_ok=True)
        self._cleanup()
        
        if not self._wait_for_ready(timeout=5):
            print("Warning: Could not verify CE is ready")
    
    def _cleanup(self):
        for f in [self.command_file, self.status_file]:
            if os.path.exists(f):
                try:
                    os.remove(f)
                except:
                    pass
    
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
    
    def _wait_for_ready(self, timeout=5):
        start_time = time.time()
        while time.time() - start_time < timeout:
            if os.path.exists(self.status_file):
                try:
                    with open(self.status_file, 'r') as f:
                        status = f.read().strip()
                    if status == "ready":
                        return True
                except:
                    pass
            time.sleep(0.1)
        return False
    
    # Speed control
    def pause(self):
        """Pause the game (speed = 0)"""
        print("Pausing game...")
        status = self._send_command("pause")
        if status == "paused":
            print("✓ Game paused")
        return status
    
    def resume(self):
        """Resume the game (speed = 1)"""
        print("Resuming game...")

        self.set_speed(1)
        return; 
        status = self._send_command("resume")
        if status == "resumed":
            print("✓ Game resumed")
        return status
    
    def set_speed(self, speed: float):
        """Set game speed multiplier (e.g., 0.5 = half speed, 2.0 = double speed)"""
        print(f"Setting speed to {speed}x...")
        status = self._send_command(f"speed:{speed}")
        if status and status.startswith("speed:"):
            print(f"✓ Speed set to {speed}x")
        return status
    
    # Position control
    def save_position(self, name: str):
        """Save current player position with a name"""
        print(f"Saving position: {name}")
        status = self._send_command(f"save_pos:{name}")
        if status == f"position_saved:{name}":
            print(f"✓ Position '{name}' saved")
            return True
        print(f"✗ Failed to save position")
        return False
    
    def load_position(self, name: str):
        """Load a saved or predefined position by name"""
        print(f"Loading position: {name}")
        status = self._send_command(f"load_pos:{name}")
        if status == f"position_loaded:{name}":
            print(f"✓ Teleported to '{name}'")
            return True
        print(f"✗ Position '{name}' not found")
        return False
    
    def teleport2(self, target, y: Optional[float] = None, z: Optional[float] = None):
        """
        Teleport to a position. Can be called in two ways:
        1. teleport("position_name") - teleport to named position
        2. teleport(x, y, z) - teleport to coordinates
        """
        if y is None and z is None:
            # Assume target is a position name
            return self.load_position(target)
        else:
            # Assume target is x coordinate
            x = target
            print(f"Teleporting to ({x}, {y}, {z})")
            status = self._send_command(f"teleport:{x},{y},{z}")
            if status == "teleported":
                print(f"✓ Teleported")
                return True
            print(f"✗ Teleport failed")
            return False
    
    def get_position(self) -> Optional[Tuple[float, float, float]]:
        """Get current player position coordinates"""
        status = self._send_command("get_position")
        if status and status.startswith("position:"):
            coords = status.split(":", 1)[1]
            try:
                x, y, z = map(float, coords.split(","))
                return (x, y, z)
            except:
                pass
        return None
    
    def list_positions(self) -> List[str]:
        """List all available positions (both predefined and saved)"""
        status = self._send_command("list_positions")
        if status and status.startswith("positions:"):
            positions_str = status.split(":", 1)[1]
            if positions_str:
                return positions_str.split(",")
        return []
    
    # Health/Stats control
    def reset_health(self):
        """Reset health to maximum"""
        print("Resetting health...")
        status = self._send_command("reset_health")
        if status == "health_reset":
            print("✓ Health reset")
            return True
        print("✗ Failed to reset health")
        return False
    
    def reset_stamina(self):
        """Reset stamina to maximum"""
        print("Resetting stamina...")
        status = self._send_command("reset_stamina")
        if status == "stamina_reset":
            print("✓ Stamina reset")
            return True
        print("✗ Failed to reset stamina")
        return False
    
    def reset_all(self):
        """Reset health, stamina, and other stats"""
        print("Resetting all stats...")
        status = self._send_command("reset_all")
        if status == "all_reset":
            print("✓ All stats reset")
            return True
        print("✗ Failed to reset all stats")
        return False
    
    def get_position(self) -> Optional[dict]:
        """Get current player position as both floats and bytes"""
        status = self._send_command("get_position")
        if status and status.startswith("position:"):
            data = status.split(":", 1)[1]
            if "|" in data:
                floats_str, bytes_str = data.split("|")
                x, y, z = map(float, floats_str.split(","))
                xb, yb, zb = bytes_str.split(",")
                return {
                    "floats": (x, y, z),
                    "bytes": (xb, yb, zb)
                }
        return None

    def teleport(self, target, y: Optional[float] = None, z: Optional[float] = None):
        """
        Teleport to a position. Can be called in two ways:
        1. teleport(x, y, z) - teleport to float coordinates
        2. teleport((x_bytes, y_bytes, z_bytes)) - teleport using byte arrays (most precise)
        """
        if isinstance(target, tuple) and len(target) == 3 and isinstance(target[0], str):
            # Byte array format
            xb, yb, zb = target
            status = self._send_command(f"teleport_bytes:{xb},{yb},{zb}")
            if status == "teleported":
                return True
            return False
        else:
            # Float format
            x = target
            status = self._send_command(f"teleport:{x},{y},{z}")
            if status == "teleported":
                return True
            return False
    
    
    def set_health(self, value: int):
        """Set health to specific value"""
        print(f"Setting health to {value}")
        status = self._send_command(f"set_health:{value}")
        if status == f"health_set:{value}":
            print(f"✓ Health set to {value}")
            return True
        print("✗ Failed to set health")
        return False
    
    # Convenience methods
    def reset_for_boss_fight(self, position_name: str = "boss_start", pause_first: bool = True):
        """Reset everything and teleport to boss fight start"""
        print(f"\n=== Resetting for boss fight ===")
        success = True
        
        # Pause game first (optional but recommended)
        if pause_first:
            self.pause()
            time.sleep(0.1)
        
        # Reset stats
        if not self.reset_all():
            success = False
        
        # Teleport to position
        if not self.load_position(position_name):
            success = False
        
        # Resume game
        if pause_first:
            self.resume()
        
        if success:
            print("✓ Ready for boss fight!\n")
        else:
            print("✗ Some operations failed\n")
        
        return success
    
    def save_current_position(self, name: str):
        """Save current position and print coordinates"""
        pos = self.get_position()
        if pos:
            print(f"Current position: {pos}")
        
        return self.save_position(name)
    
    def show_available_positions(self):
        """Print all available positions"""
        positions = self.list_positions()
        if positions:
            print("\n=== Available Positions ===")
            for pos in positions:
                if pos.startswith("preset:"):
                    print(f"  📍 {pos[7:]} (predefined)")
                elif pos.startswith("saved:"):
                    print(f"  💾 {pos[6:]} (saved)")
                else:
                    print(f"  • {pos}")
            print()
        else:
            print("No positions available")

