import streamlit as st
import cv2
from PIL import Image
import io
import numpy as np

class UIControls:
    @staticmethod
    def setup_page():
        st.set_page_config(
            page_title="AI Virtual Air Canvas", 
            page_icon="🖌️", 
            layout="wide",
            initial_sidebar_state="expanded"
        )
        # Custom CSS for modern dark UI vibes
        st.markdown("""
            <style>
            .stApp {
                background-color: #0E1117;
                color: #FFFFFF;
            }
            .stSidebar {
                background-color: #1E2127;
            }
            div[data-testid="stImage"] {
                border-radius: 10px;
                overflow: hidden;
                box-shadow: 0 4px 6px rgba(0,0,0,0.3);
            }
            h1 {
                color: #00F0FF;
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            }
            .gesture-card {
                background-color: #1E2127;
                padding: 15px;
                border-radius: 10px;
                border: 1px solid #333;
                height: 100%;
            }
            </style>
        """, unsafe_allow_html=True)
        st.title("🖌️ AI Virtual Air Canvas")
        
        # Feature: Gesture Controls Guide added to the top
        st.markdown("### Gesture Controls Guide")
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.markdown('<div class="gesture-card"><h4>☝️ Drawing Mode</h4><p><b>Index finger up</b></p><p>Draw lines on the canvas following finger movement.</p></div>', unsafe_allow_html=True)
        with c2:
            st.markdown('<div class="gesture-card"><h4>✌️ Selection Mode</h4><p><b>Index + Middle up</b></p><p>Used for selecting tools or stopping drawing.</p></div>', unsafe_allow_html=True)
        with c3:
            st.markdown('<div class="gesture-card"><h4>🤏 Brush Size</h4><p><b>Thumb + Index pinch</b></p><p>Distance between fingers controls brush thickness.</p></div>', unsafe_allow_html=True)
        with c4:
            st.markdown('<div class="gesture-card"><h4>🖐 Clear Canvas</h4><p><b>Open palm</b></p><p>Clears the entire drawing canvas.</p></div>', unsafe_allow_html=True)
        st.write("")
        st.divider()

    @staticmethod
    def render_sidebar():
        st.sidebar.header("🧰 Tools & Settings")
        
        # Tool: Sidebar Quick Reference Guide
        st.sidebar.subheader("📖 Gesture Guide")
        st.sidebar.markdown("""
        * **☝️ Index Finger** → Draw
        * **✌️ Index + Middle** → Selection Mode
        * **🤏 Thumb + Index** → Brush Size
        * **🖐 Open Palm** → Clear Canvas
        """)
        st.sidebar.divider()
        
        # Camera Control
        st.sidebar.subheader("Camera Control")
        if 'run_camera' not in st.session_state:
            st.session_state['run_camera'] = False
            
        if st.sidebar.button("▶️ Start / ⏸️ Stop Webcam"):
            st.session_state['run_camera'] = not st.session_state['run_camera']
            
        status = "🟢 Running" if st.session_state['run_camera'] else "🔴 Stopped"
        st.sidebar.markdown(f"**Status:** {status}")
            
        st.sidebar.divider()
        
        # Drawing Tools
        st.sidebar.subheader("Drawing Tools")
        color_hex = st.sidebar.color_picker("Pick Brush Color", "#00F0FF")
        
        # Convert hex to BGR
        h = color_hex.lstrip('#')
        rgb = tuple(int(h[i:i+2], 16) for i in (0, 2, 4))
        bgr_color = (rgb[2], rgb[1], rgb[0])
        
        # Thickness
        if 'brush_size' not in st.session_state:
            st.session_state['brush_size'] = 10
        thickness = st.sidebar.slider("Brush Thickness", 2, 80, st.session_state['brush_size'])
        st.session_state['brush_size'] = thickness    
        
        # Eraser Mode
        eraser = st.sidebar.toggle("Eraser Mode", help="Draw in black to erase")
        if eraser:
            bgr_color = (0, 0, 0)
            
        st.sidebar.divider()
        
        # Actions
        st.sidebar.subheader("Actions")
        if st.sidebar.button("🗑️ Clear Canvas"):
            if 'canvas' in st.session_state:
                st.session_state['canvas'] = np.zeros_like(st.session_state['canvas'])
                
        # Download
        if 'canvas' in st.session_state:
            canvas_rgb = cv2.cvtColor(st.session_state['canvas'], cv2.COLOR_BGR2RGB)
            img = Image.fromarray(canvas_rgb)
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            byte_im = buf.getvalue()
            
            st.sidebar.download_button(
                label="💾 Download Drawing",
                data=byte_im,
                file_name="air_canvas_masterpiece.png",
                mime="image/png"
            )
            
        return bgr_color

    @staticmethod
    def render_layout():
        col1, col2 = st.columns([1, 1], gap="medium")
        with col1:
            st.markdown("### 📷 Live Camera Feed")
            cam_ph = st.empty()
        with col2:
            st.markdown("### 🎨 Digital Canvas")
            canvas_ph = st.empty()
            
        return cam_ph, canvas_ph
