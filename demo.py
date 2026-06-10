# === DEMO.PY ===
# Giao diện web demo cho chart2code
# Chạy: python demo.py  →  mở trình duyệt tại http://localhost:7860

import os
import torch
import gradio as gr
from PIL import Image
from transformers import VisionEncoderDecoderModel, ViTImageProcessor, AutoTokenizer

# --- Tự động chuyển về thư mục gốc chart2code/ ---
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(ROOT_DIR)

# === CẤU HÌNH ===
MODEL_PATH      = "models/final_model"
MAX_CODE_LENGTH = 512

# === TẢI MODEL (1 lần duy nhất lúc khởi động) ===
print("Đang tải model...")
model           = VisionEncoderDecoderModel.from_pretrained(MODEL_PATH)
image_processor = ViTImageProcessor.from_pretrained(MODEL_PATH)
tokenizer       = AutoTokenizer.from_pretrained(MODEL_PATH)
device          = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model.to(device)
model.eval()
print(f"Model sẵn sàng trên: {device}")

# === HÀM XỬ LÝ ===
def generate_code(image):
    """Nhận ảnh từ Gradio → trả về code matplotlib"""
    if image is None:
        return "Vui lòng upload ảnh biểu đồ!"

    img          = image.convert("RGB")
    pixel_values = image_processor(images=img, return_tensors="pt").pixel_values.to(device)

    with torch.no_grad():
        output_ids = model.generate(
            pixel_values,
            max_length=MAX_CODE_LENGTH,
            num_beams=4,
            early_stopping=True
        )

    code = tokenizer.decode(output_ids[0], skip_special_tokens=True).strip()
    return code

# === GIAO DIỆN GRADIO ===
demo = gr.Interface(
    fn=generate_code,
    inputs=gr.Image(type="pil", label="📊 Upload ảnh biểu đồ"),
    outputs=gr.Code(language="python", label="💻 Code matplotlib sinh ra"),
    title="🤖 Chart2Code",
    description=(
        "**Upload ảnh biểu đồ** (bar, line, pie, scatter) → "
        "Model sẽ sinh ra **code Python matplotlib** tương ứng.\n\n"
        "Model: ViT-GPT2 fine-tuned trên 2500 biểu đồ tự tạo."
    ),
    examples=[],          # Thêm path ảnh mẫu ở đây nếu có
    theme=gr.themes.Soft(),
    allow_flagging="never"
)

if __name__ == "__main__":
    demo.launch(share=False)  # share=True để tạo link public
