# Virtual Air Canvas Web App

An AI-powered web application that allows users to draw on a virtual canvas using hand gestures detected through a webcam. Built with Python, Streamlit, OpenCV, and MediaPipe.

## Features
- **Drawing Mode**: Point your index finger UP to draw on the canvas.
- **Selection Mode**: Raise both index and middle fingers to move the cursor without drawing.
- **Brush Thickness Control**: Pinch (bring thumb and index fingers close) to adjust the brush size dynamically based on distance.
- **Clear Canvas**: Open your palm (all fingers up) to clear the entire canvas.
- **Customization**: Select colors and clear canvas from the sidebar. Download the final canvas as a PNG.

## Installation

1. Make sure you have Python installed.
2. Install the required dependencies using pip:
   ```bash
   pip install -r requirements.txt
   ```

## How to Run Locally

Run the Streamlit application:
```bash
streamlit run app.py
```
This will open the application in your default web browser. Allow camera access when prompted. 
To start drawing, use the sidebar to start/stop the webcam.

## How to Deploy on Streamlit Cloud

1. Create a GitHub repository and push your `app.py`, `requirements.txt`, and this `README.md` to it.
2. Go to [Streamlit Community Cloud](https://streamlit.io/cloud) and sign in with your GitHub account.
3. Click "New app".
4. Select your repository, branch, and `app.py` as the main file path.
5. Click "Deploy app".

> **Note on Deployment Camera Access**: When deployed to Streamlit Cloud, the server runs remotely, so standard OpenCV `cv2.VideoCapture(0)` will attempt to access the camera of the server, not the user's local laptop camera. The current app implementation uses OpenCV which works perfectly for local deployments. For Streamlit Cloud camera access from a remote client, a component like `streamlit-webrtc` is typically recommended.
