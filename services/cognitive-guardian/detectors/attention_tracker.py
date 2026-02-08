"""
Attention Tracker – uses webcam feed (MediaPipe Face Mesh)
to estimate gaze direction and head pose.

NOTE: Heavy ML imports are deferred to avoid startup cost when
running in stub / unit-test mode.
"""

from typing import Dict, Any, Optional
import time


class AttentionTracker:
    """Lightweight attention tracker wrapping MediaPipe."""

    def __init__(self):
        self._mp_face_mesh = None  # lazy loaded

    def _ensure_model(self):
        if self._mp_face_mesh is None:
            try:
                import mediapipe as mp
                self._mp_face_mesh = mp.solutions.face_mesh.FaceMesh(
                    max_num_faces=1,
                    refine_landmarks=True,
                    min_detection_confidence=0.5,
                    min_tracking_confidence=0.5,
                )
            except ImportError:
                pass

    def process_frame(self, frame_rgb) -> Dict[str, Any]:
        """Process a single RGB frame and return attention metrics."""
        self._ensure_model()
        if self._mp_face_mesh is None:
            return {"face_detected": False, "reason": "mediapipe_unavailable"}

        results = self._mp_face_mesh.process(frame_rgb)
        if not results.multi_face_landmarks:
            return {"face_detected": False, "timestamp": time.time()}

        landmarks = results.multi_face_landmarks[0]
        # Simplified gaze estimation using iris landmarks (468-477)
        nose_tip = landmarks.landmark[1]
        return {
            "face_detected": True,
            "eye_gaze_x": round(nose_tip.x - 0.5, 3),
            "eye_gaze_y": round(nose_tip.y - 0.5, 3),
            "head_pitch": 0.0,  # TODO – compute from pose landmarks
            "head_yaw": 0.0,
            "blink_detected": False,
            "timestamp": time.time(),
        }
