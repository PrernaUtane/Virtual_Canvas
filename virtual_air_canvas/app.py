import cv2
import numpy as np
import streamlit as st
import time

from hand_tracker import HandTracker
from gesture_detector import GestureDetector
from drawing_utils import DrawingUtils
from ui_controls import UIControls

def main():
    UIControls.setup_page()
    bgr_color = UIControls.render_sidebar()
    cam_ph, canvas_ph = UIControls.render_layout()
    
    # Initialize Core Components
    tracker = HandTracker(detection_con=0.8, track_con=0.8)
    detector = GestureDetector()
    
    # Session State Variables
    if 'prev_pt' not in st.session_state:
        st.session_state['prev_pt'] = None
    if 'mode' not in st.session_state:
        st.session_state['mode'] = "NONE"

    # If camera is stopped, just render the canvas (if it exists)
    if not st.session_state.get('run_camera', False):
        cam_ph.info("📷 Webcam is sleeping. Start it from the sidebar!")
        if 'canvas' in st.session_state:
            # Display current canvas
            canvas_rgb = cv2.cvtColor(st.session_state['canvas'], cv2.COLOR_BGR2RGB)
            canvas_ph.image(canvas_rgb, use_column_width="always")
        return

    # Initialize Webcam
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
    
    if not cap.isOpened():
        st.error("Error: Could not access the webcam.")
        return

    # Main Processing Loop
    while st.session_state['run_camera']:
        ret, frame = cap.read()
        if not ret:
            st.error("Error: Failed to capture frame.")
            break
            
        # Flip frame horizontally for selfie-view
        frame = cv2.flip(frame, 1)
        h, w, c = frame.shape
        
        # Initialize Canvas based on camera dimensions
        DrawingUtils.initialize_canvas(w, h)
        
        # 1. Find Hands & Landmarks
        frame, results = tracker.find_hands(frame, draw=True)
        lmList = tracker.get_landmarks(frame, results)
        
        # 2. Gesture Detection & Logic
        mode_text = "NONE"
        mode_color = (255, 255, 255)
        
        if len(lmList) > 0:
            fingers = detector.fingers_up(lmList)
            action = detector.determine_mode(fingers)
            
            x1, y1 = lmList[8][1], lmList[8][2]   # Index
            x2, y2 = lmList[12][1], lmList[12][2] # Middle
            
            # --- ACTION LOGIC --- #
            
            if action == "CLEAR":
                mode_text = "🧹 CLEAR PAGE"
                mode_color = (0, 0, 255)
                DrawingUtils.clear_canvas()
                st.session_state['prev_pt'] = None
                
            elif action == "PINCH":
                p1_idx, p2_idx = 4, 8 # Thumb, Index
                distance, (cx, cy) = detector.get_distance(p1_idx, p2_idx, lmList)
                
                # Dynamic mapping for brush size [30 -> 250px mapped to 2->80 thickness]
                b_size = int(np.interp(distance, [30, 250], [2, 80]))
                st.session_state['brush_size'] = b_size
                
                mode_text = f"🤏 THICKNESS: {b_size}"
                mode_color = (255, 100, 100)
                
                # Feedback visual
                cv2.circle(frame, (cx, cy), b_size, bgr_color, cv2.FILLED)
                st.session_state['prev_pt'] = None
                
            elif action == "SELECTION":
                mode_text = "✌️ SELECTION / HOVER"
                mode_color = (200, 200, 0)
                
                # Visual cursor bounding box
                cv2.rectangle(frame, (x1, y1 - 30), (x2, y2 + 30), (200, 200, 0), 2)
                st.session_state['prev_pt'] = None
                
            elif action == "DRAWING":
                mode_text = "✍️ DRAWING"
                mode_color = bgr_color
                
                # Visual cursor target
                cv2.circle(frame, (x1, y1), 15, bgr_color, cv2.FILLED)
                
                current_pt = (x1, y1)
                
                if st.session_state['prev_pt'] is None:
                    st.session_state['prev_pt'] = current_pt
                    
                # Smoothing
                smooth_pt = DrawingUtils.get_smoothed_point(current_pt, st.session_state['prev_pt'], smoothing_factor=0.6)
                
                DrawingUtils.draw_on_canvas(
                    st.session_state['prev_pt'], 
                    smooth_pt, 
                    bgr_color, 
                    st.session_state['brush_size']
                )
                
                # Update previous point
                st.session_state['prev_pt'] = smooth_pt
            
            else:
                st.session_state['prev_pt'] = None

            # Add Mode Overlay UI on the frame
            cv2.putText(frame, mode_text, (50, 100), cv2.FONT_HERSHEY_SIMPLEX, 1.5, mode_color, 3)

        # 3. Canvas Merging and UI Update
        merged = DrawingUtils.merge_canvas_with_frame(frame)
        
        # Convert to RGB for Streamlit rendering
        final_cam = cv2.cvtColor(merged, cv2.COLOR_BGR2RGB)
        final_canvas = cv2.cvtColor(st.session_state['canvas'], cv2.COLOR_BGR2RGB)
        
        cam_ph.image(final_cam, use_column_width="always")
        canvas_ph.image(final_canvas, use_column_width="always")
        
        # Tiny sleep to stabilize frame rate and prevent overwhelming Streamlit
        time.sleep(0.01)
        
    cap.release()

if __name__ == "__main__":
    main()
