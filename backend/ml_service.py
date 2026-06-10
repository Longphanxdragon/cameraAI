"""
ML Service — wraps ViT-GPT2 model for chart-to-code generation.
Uses lazy loading so the model loads only on first API call.
"""
import io
import os
import torch
from PIL import Image
from transformers import VisionEncoderDecoderModel, ViTImageProcessor, AutoTokenizer

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_PATH = os.path.join(ROOT_DIR, "models", "final_model")


class MLService:
    def __init__(self):
        self.model = None
        self.processor = None
        self.tokenizer = None
        self.device = None
        self._loaded = False

    def load(self):
        if self._loaded:
            return
        print(f"[ML] Loading model from: {MODEL_PATH}")
        self.model = VisionEncoderDecoderModel.from_pretrained(MODEL_PATH)
        self.processor = ViTImageProcessor.from_pretrained(MODEL_PATH)
        self.tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH)
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model.to(self.device)
        self.model.eval()
        self._loaded = True
        print(f"[ML] Model ready on {self.device}")

    def generate_code(self, image_bytes: bytes) -> str:
        self.load()
        img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        pixel_values = self.processor(
            images=img, return_tensors="pt"
        ).pixel_values.to(self.device)

        with torch.no_grad():
            output_ids = self.model.generate(
                pixel_values,
                max_length=512,
                num_beams=4,
                early_stopping=True,
            )
        return self.tokenizer.decode(output_ids[0], skip_special_tokens=True).strip()


# Singleton instance
ml_service = MLService()
