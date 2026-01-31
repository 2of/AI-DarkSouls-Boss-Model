import random
import numpy as np


class MLWrapper():
    """
    Wrapper for ML model inference.
    
    okay so here's a vector im not sure  vector (15 dimensions total):
    - [0] hp: Player HP (0-1)
    - [1] stamina: Player stamina (0-1)
    - [2] boss_hp: Boss HP (0-1)


    For optical flow stuff we have this: 
    Now, issue is this is MUDDY AS FUCK 


    - [3-14] optical_flow_features: 12 features from OpticalFlowTracker.get_ml_features()
        - [3] motion_x: Horizontal motion direction
        - [4] motion_y: Vertical motion direction
        - [5] motion_mag: Overall motion magnitude
        - [6] motion_dir: Motion direction (0-1, circular)
        - [7] motion_area: Percentage of frame with motion
        - [8] top_motion: Motion in top half
        - [9] bottom_motion: Motion in bottom half
        - [10] left_motion: Motion in left half
        - [11] right_motion: Motion in right half
        - [12] center_motion: Motion in center region
        - [13] acceleration: Change in motion speed
        - [14] motion_variance: Spread of motion values
    """
    
    STATE_DIM = 15
    
    def __init__(self, controller):
        self.controller = controller

    def encode_state(self, hp, stamina, boss_hp, motion_dir=0, motion_mag=0, motion_vec=(0, 0)):
        """
        
        """
        return np.array([
            hp / 100.0,
            stamina / 100.0,
            boss_hp / 100.0,
            motion_dir / 360.0,
            min(motion_mag / 50.0, 1.0),
            (motion_vec[0] + 50) / 100.0,
            (motion_vec[1] + 50) / 100.0,
        ], dtype=np.float32)

    def encode_full_state(self, hp, stamina, boss_hp, flow_features):
        """
        Encode the complete game state into a normalized feature vector.
        
        Args:
            hp: Player HP percentage (0-100)
            stamina: Player stamina percentage (0-100)
            boss_hp: Boss HP percentage (0-100)
            flow_features: 12-element array from OpticalFlowTracker.get_ml_features()
            
        Returns:
            numpy array of shape (15,) with all normalized features
        """
        # Normalize bar values
        bar_features = np.array([
            hp / 100.0,
            stamina / 100.0,
            boss_hp / 100.0,
        ], dtype=np.float32)
        
        # Ensure flow_features is the right shape
        if flow_features is None:
            flow_features = np.zeros(12, dtype=np.float32)
        else:
            flow_features = np.asarray(flow_features, dtype=np.float32)
            if len(flow_features) != 12:
                flow_features = np.zeros(12, dtype=np.float32)
        
        # Concatenate into full state vector
        state = np.concatenate([bar_features, flow_features])
        
        return state
    
    def get_state_feature_names(self):
        """Get names of all state features for debugging."""
        return [
            'hp', 'stamina', 'boss_hp',
            'motion_x', 'motion_y', 'motion_mag', 'motion_dir',
            'motion_area', 'top_motion', 'bottom_motion',
            'left_motion', 'right_motion', 'center_motion',
            'acceleration', 'motion_variance'
        ]

    def getmove(self, v=None, state_vector=None):
        """
        Get the next move. Currently returns a random move.
        
        Args:
            v: Legacy format [stamina, hp, boss_hp]
            state_vector: New format - full encoded state vector (15,)
        """
        # TODO: Replace with actual model inference
        # When you have a trained model:
        # if state_vector is not None:
        #     action_probs = self.model.predict(state_vector)
        #     return self.controller.get_all_actions()[np.argmax(action_probs)]
        
        return random.choice(self.controller.get_all_actions())
    
    def state_to_string(self, state_vector):
        """Format state vector as readable string for debugging."""
        names = self.get_state_feature_names()
        parts = [f"{name}={val:.2f}" for name, val in zip(names, state_vector)]
        return " | ".join(parts)
