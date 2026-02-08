"""
Voice Emotion Detector – placeholder for Wav2Vec2-based
speech emotion recognition.
"""

from typing import Optional


class VoiceEmotionDetector:
    """
    Detects emotion from voice using a fine-tuned Wav2Vec2 model.
    Currently returns heuristic results; the real model will be
    loaded from ml/training/cognitive_load_lstm/ once trained.
    """

    LABELS = ["neutral", "happy", "sad", "angry", "fearful", "surprised"]

    def __init__(self):
        self._model = None
        self._processor = None

    def _load_model(self):
        """Lazy-load the transformer model."""
        try:
            from transformers import Wav2Vec2ForSequenceClassification, Wav2Vec2Processor

            model_name = "ehcalabres/wav2vec2-lg-xlsr-en-speech-emotion-recognition"
            self._processor = Wav2Vec2Processor.from_pretrained(model_name)
            self._model = Wav2Vec2ForSequenceClassification.from_pretrained(model_name)
        except Exception:
            pass

    def detect(self, audio_array, sample_rate: int = 16000) -> Optional[str]:
        """Return the dominant emotion label from an audio segment."""
        if self._model is None:
            self._load_model()
        if self._model is None:
            return "neutral"  # fallback

        import torch

        inputs = self._processor(
            audio_array, sampling_rate=sample_rate, return_tensors="pt", padding=True
        )
        with torch.no_grad():
            logits = self._model(**inputs).logits
        predicted_id = torch.argmax(logits, dim=-1).item()
        return self.LABELS[predicted_id] if predicted_id < len(self.LABELS) else "neutral"
