import numpy as np
import streamlit as st
import mediapipe as mp
import math
from PIL import Image, ImageDraw, ImageFont
import io
import av
from streamlit_webrtc import webrtc_streamer, VideoProcessorBase, WebRtcMode, RTCConfiguration

# Initialize MediaPipe Hands
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(min_detection_confidence=0.7, min_tracking_confidence=0.7, max_num_hands=1)

RTC_CONFIGURATION = RTCConfiguration(
    {"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]}
)

def set_page_config():
    st.set_page_config(page_title="Virtual Air Canvas", page_icon="🖌️", layout="wide")

class CanvasProcessor(VideoProcessorBase):
    def __init__(self):
        self.canvas = None # Will be a NumPy array
        self.prev_x = 0
        self.prev_y = 0
        self.drawing = False
        self.brush_size = 5
        self.brush_color = (255, 0, 0, 255) # RGBA
        self.clear_canvas = False

    def detect_fingers(self, lmList):
        fingers = []
        tipIds = [4, 8, 12, 16, 20]
        if not lmList:
            return [False]*5
            
        # Thumb: tip vs mcp
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

    def recv(self, frame: av.VideoFrame) -> av.VideoFrame:
        # Get frame as ndarray (RGB)
        img = frame.to_ndarray(format="rgb24")
        
        # Flip horizontally for selfie-view
        img = np.fliplr(img).copy()
        h, w, c = img.shape
        
        # User explicitly requested a NumPy array as the canvas.
        if self.canvas is None:
            self.canvas = np.zeros((h, w, 4), dtype=np.uint8)
        elif getattr(self.canvas, 'shape', (0,0))[:2] != (h, w):
            self.canvas = np.zeros((h, w, 4), dtype=np.uint8)
            
        if self.clear_canvas:
            self.canvas = np.zeros((h, w, 4), dtype=np.uint8)
            self.clear_canvas = False

        # Apply MediaPipe processing
        results = hands.process(img)
        lmList = []
        
        # Convert annotated frame to PIL image for drawing UI elements
        pil_img = Image.fromarray(img).convert("RGBA")
        draw = ImageDraw.Draw(pil_img)
        
        # Use PIL Image temporally to draw into the NumPy canvas
        canvas_img = Image.fromarray(self.canvas)
        canvas_draw = ImageDraw.Draw(canvas_img)
        
        if results.multi_hand_landmarks:
            for handLms in results.multi_hand_landmarks:
                landmarks = []
                for id, lm in enumerate(handLms.landmark):
                    cx, cy = int(lm.x * w), int(lm.y * h)
                    landmarks.append((cx, cy))
                    lmList.append([id, cx, cy])
                    
                # Draw connections manually without using mediapipe drawing utilities
                for connection in mp_hands.HAND_CONNECTIONS:
                    start_idx = connection[0]
                    end_idx = connection[1]
                    if start_idx < len(landmarks) and end_idx < len(landmarks):
                        draw.line([landmarks[start_idx], landmarks[end_idx]], fill=(0, 255, 0, 255), width=2)
                        
                # Draw landmarks manually
                for cx, cy in landmarks:
                    draw.ellipse([cx - 4, cy - 4, cx + 4, cy + 4], fill=(255, 0, 0, 255))
        
        if len(lmList) != 0:
            x1, y1 = lmList[8][1:]   # Index finger tip
            x2, y2 = lmList[12][1:]  # Middle finger tip
            tx, ty = lmList[4][1:]   # Thumb tip
            
            fingers = self.detect_fingers(lmList)
            
            # Open Palm: Clear Canvas
            if sum(fingers) == 5:
                # Direct reset of the numpy array
                self.canvas = np.zeros((h, w, 4), dtype=np.uint8)
                canvas_img = Image.fromarray(self.canvas) # Update reference
                canvas_draw = ImageDraw.Draw(canvas_img)
                draw.text((50, 50), "CLEAR CANVAS", fill=(255, 0, 0, 255))
                
            # Pinch Control (Thickness)
            elif fingers[0] and fingers[1] and not fingers[2] and not fingers[3] and not fingers[4]:
                distance = math.hypot(x1 - tx, y1 - ty)
                b_size = int(np.interp(distance, [20, 200], [1, 50]))
                self.brush_size = b_size
                
                cx, cy = (x1 + tx) // 2, (y1 + ty) // 2
                draw.ellipse([cx - b_size, cy - b_size, cx + b_size, cy + b_size], fill=self.brush_color)
                draw.text((50, 50), f"THICKNESS: {b_size}", fill=(255, 0, 0, 255))
                self.drawing = False
                
            # Selection Mode (Index + Middle Up)
            elif fingers[1] and fingers[2]:
                self.drawing = False
                draw.rectangle([x1, y1 - 25, x2, y2 + 25], fill=(255, 0, 255, 255))
                draw.text((50, 50), "SELECTION MODE", fill=(255, 0, 255, 255))
                self.prev_x, self.prev_y = x1, y1
                
            # Drawing Mode (Only Index Up)
            elif fingers[1] and not fingers[2] and sum(fingers[2:]) == 0:
                draw.ellipse([x1 - 15, y1 - 15, x1 + 15, y1 + 15], fill=self.brush_color)
                draw.text((50, 50), "DRAWING MODE", fill=self.brush_color)
                
                if not self.drawing:
                    self.drawing = True
                    self.prev_x, self.prev_y = x1, y1
                
                if self.prev_x != 0 and self.prev_y != 0:
                    # Draw continuous line onto the temporary PIL canvas
                    canvas_draw.line([(self.prev_x, self.prev_y), (x1, y1)], fill=self.brush_color, width=self.brush_size, joint="curve")
                    # Draw circles at endpoints for smooth edges
                    canvas_draw.ellipse([self.prev_x - self.brush_size//2, self.prev_y - self.brush_size//2, self.prev_x + self.brush_size//2, self.prev_y + self.brush_size//2], fill=self.brush_color)
                    canvas_draw.ellipse([x1 - self.brush_size//2, y1 - self.brush_size//2, x1 + self.brush_size//2, y1 + self.brush_size//2], fill=self.brush_color)
                    
                self.prev_x, self.prev_y = x1, y1
            else:
                self.drawing = False
                
        # Write back to permanent NumPy canvas state
        self.canvas = np.array(canvas_img)
        
        # Composite the canvas on top of the webcam frame
        out_img = Image.alpha_composite(pil_img, canvas_img)
        out_arr = np.array(out_img.convert("RGB"))
        return av.VideoFrame.from_ndarray(out_arr, format="rgb24")


def initialize_state():
    if 'brush_size' not in st.session_state:
        st.session_state['brush_size'] = 5
    if 'clear_triggered' not in st.session_state:
        st.session_state['clear_triggered'] = False

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
        
    st.sidebar.subheader("Drawing Tools")
    color = st.sidebar.color_picker("Pick a Brush Color", "#FF0000")
    # Convert hex to RGBA
    h = color.lstrip('#')
    rgb = tuple(int(h[i:i+2], 16) for i in (0, 2, 4))
    rgba_color = (rgb[0], rgb[1], rgb[2], 255)
    
    brush_size = st.sidebar.slider("Brush Thickness", 1, 50, st.session_state['brush_size'], key='thickness_slider')
    st.session_state['brush_size'] = brush_size
    
    eraser = st.sidebar.checkbox("Eraser Mode (Draw invisible/clear)")
    if eraser:
        # Erasing by drawing transparent pixels (alpha=0) uses Pillow composite trick. 
        # For simplicity, we can draw a black mask. 
        rgba_color = (0, 0, 0, 255)
        
    if st.sidebar.button("Clear Canvas", key="clear_btn"):
        st.session_state['clear_triggered'] = True
        
    st.sidebar.subheader("Export")
    return rgba_color

def main():
    set_page_config()
    st.title("🖌️ AI Virtual Air Canvas (WebRTC)")
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
    rgba_color = sidebar_ui()
    
    webrtc_ctx = webrtc_streamer(
        key="canvas",
        mode=WebRtcMode.SENDRECV,
        rtc_configuration=RTC_CONFIGURATION,
        video_processor_factory=CanvasProcessor,
        media_stream_constraints={"video": True, "audio": False},
        async_processing=True,
    )
    
    if webrtc_ctx.video_processor:
        webrtc_ctx.video_processor.brush_color = rgba_color
        webrtc_ctx.video_processor.brush_size = st.session_state['brush_size']
            
        if st.session_state['clear_triggered']:
            webrtc_ctx.video_processor.clear_canvas = True
            st.session_state['clear_triggered'] = False
            
        # Download Canvas
        st.sidebar.markdown("---")
        try:
            canvas_np = webrtc_ctx.video_processor.canvas
            if canvas_np is not None:
                # Need to convert NumPy array to PIL image for downloading
                canvas_img = Image.fromarray(canvas_np)
                img_byte_arr = io.BytesIO()
                canvas_img.save(img_byte_arr, format='PNG')
                st.sidebar.download_button(
                    label="Download Drawing as PNG",
                    data=img_byte_arr.getvalue(),
                    file_name="virtual_canvas.png",
                    mime="image/png",
                )
        except Exception:
            st.sidebar.info("Start video to draw and download!")

if __name__ == "__main__":
    main()
