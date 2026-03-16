import math
import numpy as np

class GestureDetector:
    def __init__(self):
        self.tip_ids = [4, 8, 12, 16, 20] # Thumb, Index, Middle, Ring, Pinky tip IDs

    def fingers_up(self, lm_list):
        """
        Determines which fingers are pointing up.
        Returns a list of 5 booleans [Thumb, Index, Middle, Ring, Pinky].
        """
        fingers = []
        if len(lm_list) == 0:
             return [False] * 5

        # 1. Thumb
        # Thumb operates on purely X axis primarily or depends on handedness. 
        # A simple check: tip is higher (lower Y value) than IP point if hand is upright
        # Or checking relative to MCP.
        if lm_list[self.tip_ids[0]][1] > lm_list[self.tip_ids[0] - 1][1]:
            fingers.append(True)
        else:
            fingers.append(False)

        # 2-5. Other 4 Fingers
        # Compare tip Y coordinate with PIP Y coordinate
        for id in range(1, 5):
            if lm_list[self.tip_ids[id]][2] < lm_list[self.tip_ids[id] - 2][2]:
                fingers.append(True)
            else:
                fingers.append(False)
                
        return fingers

    def get_distance(self, p1_idx, p2_idx, lm_list):
        """
        Calculates distance between two landmarks.
        Returns the distance, and the (x, y) coordinates of the midpoint.
        """
        if len(lm_list) < max(p1_idx, p2_idx):
            return 0, (0, 0)
            
        x1, y1 = lm_list[p1_idx][1], lm_list[p1_idx][2]
        x2, y2 = lm_list[p2_idx][1], lm_list[p2_idx][2]
        cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
        
        distance = math.hypot(x2 - x1, y2 - y1)
        return distance, (cx, cy)

    def determine_mode(self, fingers):
        """
        Decodes fingers configuration into a specific gesture/mode.
        Modes: 'CLEAR', 'DRAWING', 'SELECTION', 'PINCH', 'NONE'
        """
        # Open Palm: clear canvas
        if sum(fingers) == 5:
            return "CLEAR"
            
        # Pinch (Thumb + Index): control thickness. 
        # Approximation: if thumb and index are both up/near, and others are down.
        if fingers[0] and fingers[1] and sum(fingers[2:]) == 0:
            return "PINCH"
            
        # Selection Mode: Index and Middle are Up
        if fingers[1] and fingers[2] and sum(fingers[3:]) == 0:
            return "SELECTION"
            
        # Drawing Mode: Only Index is Up
        if fingers[1] and sum(fingers[2:]) == 0:
            return "DRAWING"
            
        return "NONE"
