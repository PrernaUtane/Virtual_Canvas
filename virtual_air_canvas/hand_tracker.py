import cv2
import mediapipe as mp

class HandTracker:
    def __init__(self, mode=False, max_hands=1, detection_con=0.7, track_con=0.7):
        self.mode = mode
        self.max_hands = max_hands
        self.detection_con = detection_con
        self.track_con = track_con

        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            static_image_mode=self.mode,
            max_num_hands=self.max_hands,
            min_detection_confidence=self.detection_con,
            min_tracking_confidence=self.track_con
        )
        self.mp_draw = mp.solutions.drawing_utils

    def find_hands(self, frame, draw=True):
        """
        Processes the frame and detects hands.
        Returns the original frame (optionally drawn on) and the results.
        """
        # Convert to RGB as MediaPipe requires it
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        self.results = self.hands.process(frame_rgb)

        if self.results.multi_hand_landmarks and draw:
            for hand_landmarks in self.results.multi_hand_landmarks:
                self.mp_draw.draw_landmarks(frame, hand_landmarks, self.mp_hands.HAND_CONNECTIONS)
                
        return frame, self.results

    def get_landmarks(self, frame, results, hand_no=0):
        """
        Extracts landmark positions for a specific hand.
        Returns a list of [id, cx, cy] coordinates.
        """
        lm_list = []
        if results.multi_hand_landmarks:
            # We only track max_num_hands=1 so hand_no=0 is safe
            hand_landmarks = results.multi_hand_landmarks[hand_no]
            h, w, c = frame.shape
            for id, lm in enumerate(hand_landmarks.landmark):
                cx, cy = int(lm.x * w), int(lm.y * h)
                lm_list.append([id, cx, cy])
        return lm_list
