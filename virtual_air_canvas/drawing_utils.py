import cv2
import numpy as np
import streamlit as st

class DrawingUtils:
    @staticmethod
    def initialize_canvas(width, height):
        if 'canvas' not in st.session_state or st.session_state['canvas'].shape[:2] != (height, width):
            st.session_state['canvas'] = np.zeros((height, width, 3), dtype=np.uint8)

    @staticmethod
    def clear_canvas():
        if 'canvas' in st.session_state:
            st.session_state['canvas'] = np.zeros_like(st.session_state['canvas'])
            
    @staticmethod
    def draw_on_canvas(p1, p2, color, thickness):
        """
        Draw a smooth line from p1 to p2 on the global canvas state.
        """
        if p1 is not None and p2 is not None:
             cv2.line(st.session_state['canvas'], p1, p2, color, thickness)

    @staticmethod
    def merge_canvas_with_frame(frame):
        """
        Merges the current Streamlit session canvas with the OpenCV frame.
        """
        if 'canvas' not in st.session_state:
            return frame
            
        canvas = st.session_state['canvas']
        gray_canvas = cv2.cvtColor(canvas, cv2.COLOR_BGR2GRAY)
        
        # Create a mask of the drawing (where canvas is NOT black)
        _, mask = cv2.threshold(gray_canvas, 10, 255, cv2.THRESH_BINARY)
        mask_inv = cv2.bitwise_not(mask)
        
        # Black out the drawing region in the original frame
        frame_bg = cv2.bitwise_and(frame, frame, mask=mask_inv)
        
        # Take the colored region from the drawing canvas
        canvas_fg = cv2.bitwise_and(canvas, canvas, mask=mask)
        
        # Combine the backgrounds
        merged = cv2.add(frame_bg, canvas_fg)
        return merged
        
    @staticmethod
    def get_smoothed_point(current_pt, prev_pt, smoothing_factor=0.5):
        """
        Applies simple exponential smoothing to reduce jitter.
        Lower factor = smoother but more lag. Higher factor = more responsive but jittery.
        """
        if prev_pt is None or current_pt is None:
            return current_pt
            
        smoothed_x = int(prev_pt[0] * (1 - smoothing_factor) + current_pt[0] * smoothing_factor)
        smoothed_y = int(prev_pt[1] * (1 - smoothing_factor) + current_pt[1] * smoothing_factor)
        
        return (smoothed_x, smoothed_y)
