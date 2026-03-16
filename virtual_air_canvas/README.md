# AI Virtual Air Canvas (Modular Edition)

An AI-powered web application that allows users to draw on a virtual canvas using hand gestures detected through a webcam. Features a modular, clean architecture and a modern dark UI!

## Tech Stack
- **Python**: Core language
- **OpenCV**: Webcam capture and drawing operations
- **MediaPipe Hands**: Lightning-fast 21-point hand tracking
- **Streamlit**: Elegant web interface
- **NumPy**: Matrix operations for canvas masks

## Architecture
The application is refactored for production readiness:
- `app.py`: Entry point and main orchestration loop
- `hand_tracker.py`: Wrapper for MediaPipe configuration
- `gesture_detector.py`: Pure logic for interpreting landmarks into gestures
- `drawing_utils.py`: Canvas state manipulation and OpenCV drawing masks
- `ui_controls.py`: Streamlit responsive web components

## Actions & Gestures
1. **DRAWING**: Hold only your index finger up.
2. **SELECTION/HOVER**: Hold index and middle fingers up to move without drawing.
3. **PINCH**: Bring your thumb and index finger close together. Distance controls the thickness of the brush.
4. **CLEAR**: Open palm (all 5 fingers up).

## Installation

```bash
git clone <your_repo_url>
cd virtual_air_canvas
pip install -r requirements.txt
```

## Running the app
```bash
streamlit run app.py
```
*Note: Due to a Streamlit deprecation warning, we have refactored images to use `use_container_width=True` instead of `use_container_width=False` / `column_width`*.

## Deployment on Streamlit Cloud
1. Push this folder to GitHub.
2. Go to [share.streamlit.io](https://share.streamlit.io) and deploy `app.py`.
