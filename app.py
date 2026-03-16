import cv2
import numpy as np
import streamlit as st
import mediapipe as mp
import math
from PIL import Image
import io

# Initialize MediaPipe Hands
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(min_detection_confidence=0.7, min_tracking_confidence=0.7, max_num_hands=1)
mp_draw = mp.solutions.drawing_utils

def set_page_config():
    st.set_page_config(page_title="Virtual Air Canvas", page_icon="🖌️", layout="wide")

def initialize_state():
    # Application state setup
    if 'canvas' not in st.session_state:
        st.session_state['canvas'] = np.zeros((480, 640, 3), dtype=np.uint8)
    if 'prev_x' not in st.session_state:
        st.session_state['prev_x'] = 0
    if 'prev_y' not in st.session_state:
        st.session_state['prev_y'] = 0
    if 'drawing' not in st.session_state:
        st.session_state['drawing'] = False
    if 'run_camera' not in st.session_state:
        st.session_state['run_camera'] = False
    if 'brush_size' not in st.session_state:
        st.session_state['brush_size'] = 5

def sidebar_ui():
    st.sidebar.title("🧰 Tools & Settings")
    
    st.sidebar.subheader("📖 Gesture Guide")
    st.sidebar.markdown("""
    * **☝️ Index Finger** → Draw
    * **✌️ Index + Middle** → Selection Mode
    * **🤏 Thumb + Index** → Brush Size Control
    * **🖐 Open Palm** → Clear Canvas
    """)
    st.sidebar.divider()
    
    # Camera Controls
    st.sidebar.subheader("Camera Control")
    if st.sidebar.button("Start / Stop Webcam", key="cam_btn"):
        st.session_state['run_camera'] = not st.session_state['run_camera']
        
    st.sidebar.markdown(f"**Webcam is:** {'🟢 Running' if st.session_state['run_camera'] else '🔴 Stopped'}")
        
    # Drawing Tools
    st.sidebar.subheader("Drawing Tools")
    color = st.sidebar.color_picker("Pick a Brush Color", "#FF0000")
    # Convert hex to BGR format for OpenCV
    h = color.lstrip('#')
    rgb = tuple(int(h[i:i+2], 16) for i in (0, 2, 4))
    bgr_color = (rgb[2], rgb[1], rgb[0])
    
    # Dynamic brush thickness slider
    brush_size = st.sidebar.slider("Brush Thickness", 1, 50, st.session_state['brush_size'], key='thickness_slider')
    st.session_state['brush_size'] = brush_size
    
    eraser = st.sidebar.checkbox("Eraser Mode (Draw black)")
    if eraser:
        bgr_color = (0, 0, 0)
        
    if st.sidebar.button("Clear Canvas", key="clear_btn"):
        st.session_state['canvas'] = np.zeros(st.session_state['canvas'].shape, dtype=np.uint8)
        
    st.sidebar.subheader("Export")
    
    # Convert canvas array to PNG for download
    canvas_rgb = cv2.cvtColor(st.session_state['canvas'], cv2.COLOR_BGR2RGB)
    canvas_image = Image.fromarray(canvas_rgb)
    img_byte_arr = io.BytesIO()
    canvas_image.save(img_byte_arr, format='PNG')
    img_byte_arr = img_byte_arr.getvalue()
    
    st.sidebar.download_button(
        label="Download Drawing as PNG",
        data=img_byte_arr,
        file_name="virtual_canvas.png",
        mime="image/png",
    )
    
    return bgr_color

def detect_fingers(lmList):
    """
    Returns a list of 5 booleans indicating whether each finger is UP.
    Fingers: [Thumb, Index, Middle, Ring, Pinky]
    """
    fingers = []
    tipIds = [4, 8, 12, 16, 20]
    
    if not lmList:
        return [False]*5
        
    # Thumb: tip vs mcp check
    if lmList[tipIds[0]][1] > lmList[tipIds[0] - 1][1]:
        fingers.append(True)
    else:
        fingers.append(False)
        
    # 4 Fingers: tip y-coord vs PIP y-coord
    for id in range(1, 5):
        if lmList[tipIds[id]][2] < lmList[tipIds[id] - 2][2]:
            fingers.append(True)
        else:
            fingers.append(False)
            
    return fingers


def process_frame(frame, bgr_color, placeholder_cam, placeholder_canvas):
    # Flip horizontally for selfie-view
    frame = cv2.flip(frame, 1)
    h, w, c = frame.shape
    
    # Resize canvas if needed based on frame dimensions
    if st.session_state['canvas'].shape[:2] != (h, w):
        st.session_state['canvas'] = np.zeros((h, w, 3), dtype=np.uint8)
        
    canvas = st.session_state['canvas']
    
    # MediaPipe operates on RGB images
    frameRGB = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = hands.process(frameRGB)
    
    lmList = []
    
    if results.multi_hand_landmarks:
        for handLms in results.multi_hand_landmarks:
            mp_draw.draw_landmarks(frame, handLms, mp_hands.HAND_CONNECTIONS)
            for id, lm in enumerate(handLms.landmark):
                cx, cy = int(lm.x * w), int(lm.y * h)
                lmList.append([id, cx, cy])
                
    if len(lmList) != 0:
        x1, y1 = lmList[8][1:]   # Index finger tip
        x2, y2 = lmList[12][1:]  # Middle finger tip
        tx, ty = lmList[4][1:]   # Thumb tip
        
        fingers = detect_fingers(lmList)
        
        # Open Palm: Clear Canvas (all 5 fingers up)
        if sum(fingers) == 5:
            canvas = np.zeros((h, w, 3), dtype=np.uint8)
            st.session_state['canvas'] = canvas
            cv2.putText(frame, "CLEAR CANVAS", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 3)
            
        # Pinch Control (Thumb + Index close together) Thickness Control
        elif fingers[0] and fingers[1] and not fingers[2] and not fingers[3] and not fingers[4]:
            distance = math.hypot(x1 - tx, y1 - ty)
            # Map distance linearly from [20-200] range to brush size [1-50]
            b_size = int(np.interp(distance, [20, 200], [1, 50]))
            st.session_state['brush_size'] = b_size
            
            # Draw thickness feedback circle between thumb and index
            cx, cy = (x1 + tx) // 2, (y1 + ty) // 2
            cv2.circle(frame, (cx, cy), b_size, bgr_color, cv2.FILLED)
            cv2.putText(frame, f"THICKNESS: {b_size}", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 3)
            st.session_state['drawing'] = False
            
        # Selection Mode (Index + Middle Up)
        elif fingers[1] and fingers[2]:
            st.session_state['drawing'] = False
            # Draw selection cursor
            cv2.rectangle(frame, (x1, y1 - 25), (x2, y2 + 25), (255, 0, 255), cv2.FILLED)
            cv2.putText(frame, "SELECTION MODE", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 255), 3)
            # Make sure we don't draw a line when returning to draw mode
            st.session_state['prev_x'], st.session_state['prev_y'] = x1, y1
            
        # Drawing Mode (Only Index Up)
        elif fingers[1] and not fingers[2] and sum(fingers[2:]) == 0:
            cv2.circle(frame, (x1, y1), 15, bgr_color, cv2.FILLED)
            cv2.putText(frame, "DRAWING MODE", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, bgr_color, 3)
            
            if not st.session_state['drawing']:
                st.session_state['drawing'] = True
                st.session_state['prev_x'], st.session_state['prev_y'] = x1, y1
            
            # Smoothly connect line from previous point to current point
            if st.session_state['prev_x'] != 0 and st.session_state['prev_y'] != 0:
                cv2.line(canvas, (st.session_state['prev_x'], st.session_state['prev_y']), 
                         (x1, y1), bgr_color, st.session_state['brush_size'])
                
            st.session_state['prev_x'], st.session_state['prev_y'] = x1, y1
            
        else:
            st.session_state['drawing'] = False
            
    # Combine real frame with drawing canvas
    gray = cv2.cvtColor(canvas, cv2.COLOR_BGR2GRAY)
    _, inv_mask = cv2.threshold(gray, 20, 255, cv2.THRESH_BINARY_INV)
    inv_mask = cv2.cvtColor(inv_mask, cv2.COLOR_GRAY2BGR)
    
    # Ensure drawing blends without blowing out natural camera colors
    bg = cv2.bitwise_and(frame, inv_mask)
    merged_frame = cv2.bitwise_or(bg, canvas)
    
    # Streamlit refresh (Convert to RGB for accurate UI rendering)
    placeholder_cam.image(cv2.cvtColor(merged_frame, cv2.COLOR_BGR2RGB), channels="RGB")
    placeholder_canvas.image(cv2.cvtColor(canvas, cv2.COLOR_BGR2RGB), channels="RGB")


def main():
    set_page_config()
    st.title("🖌️ AI Virtual Air Canvas")
    st.markdown("Use hand gestures detected by your webcam to draw in the air! **Open the sidebar** for tools.")
    
    st.markdown("""
        <style>
        .gesture-card {
            background-color: #1E2127;
            padding: 15px;
            border-radius: 10px;
            border: 1px solid #333;
            height: 100%;
            color: #FFF;
        }
        </style>
    """, unsafe_allow_html=True)
    
    st.markdown("### Gesture Controls Guide")
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown('<div class="gesture-card"><h4>☝️ Drawing Mode</h4><p><b>Index finger up</b></p><p>Move your index finger to draw on the canvas.</p></div>', unsafe_allow_html=True)
    with c2:
        st.markdown('<div class="gesture-card"><h4>✌️ Selection Mode</h4><p><b>Index + Middle up</b></p><p>Used for selecting tools or pausing drawing.</p></div>', unsafe_allow_html=True)
    with c3:
        st.markdown('<div class="gesture-card"><h4>🤏 Brush Size</h4><p><b>Thumb + Index pinch</b></p><p>Distance between the fingers controls brush thickness.</p></div>', unsafe_allow_html=True)
    with c4:
        st.markdown('<div class="gesture-card"><h4>🖐 Clear Canvas</h4><p><b>Open palm</b></p><p>Clears the entire canvas.</p></div>', unsafe_allow_html=True)
    st.write("")
    st.divider()
    
    initialize_state()
    bgr_color = sidebar_ui()
    
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Webcam View")
        placeholder_cam = st.empty()
    with col2:
        st.subheader("Digital Canvas")
        placeholder_canvas = st.empty()
        
    if not st.session_state['run_camera']:
        placeholder_cam.info("Webcam is stopped. Click 'Start / Stop Webcam' in the sidebar.")
        placeholder_canvas.image(cv2.cvtColor(st.session_state['canvas'], cv2.COLOR_BGR2RGB), channels="RGB")
        return
        
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    
    while st.session_state['run_camera'] and cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            st.error("Cannot read from webcam.")
            break
            
        process_frame(frame, bgr_color, placeholder_cam, placeholder_canvas)
        
    cap.release()

if __name__ == "__main__":
    main()
