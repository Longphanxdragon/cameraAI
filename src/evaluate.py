# === EVALUATE.PY ===
# Đo độ chính xác của model trên toàn bộ eval dataset
# Metric 1: Exact Match   - code sinh ra có giống y chang code gốc không?
# Metric 2: BLEU Score    - code sinh ra giống một phần bao nhiêu %?

import os
import glob
import torch
from PIL import Image
from transformers import VisionEncoderDecoderModel, ViTImageProcessor, AutoTokenizer
from nltk.translate.bleu_score import sentence_bleu, SmoothingFunction

# --- Tự động chuyển về thư mục gốc chart2code/ ---
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT_DIR)

# === CẤU HÌNH ===
MODEL_PATH      = "models/final_model"
DATA_IMAGE_DIR  = "data/images"
DATA_CODE_DIR   = "data/codes"
MAX_CODE_LENGTH = 512
# Chỉ evaluate trên 100 ảnh đầu tiên (để chạy nhanh, tăng lên nếu muốn chính xác hơn)
MAX_SAMPLES     = 100

# === TẢI MODEL ===
print(f"Đang tải model từ: {MODEL_PATH}...")
model           = VisionEncoderDecoderModel.from_pretrained(MODEL_PATH)
image_processor = ViTImageProcessor.from_pretrained(MODEL_PATH)
tokenizer       = AutoTokenizer.from_pretrained(MODEL_PATH)
device          = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model.to(device)
print(f"Model chạy trên: {device}")

# === HÀM DỰ ĐOÁN ===
def predict(image_path):
    img          = Image.open(image_path).convert("RGB")
    pixel_values = image_processor(images=img, return_tensors="pt").pixel_values.to(device)
    with torch.no_grad():
        output_ids = model.generate(
            pixel_values,
            max_length=MAX_CODE_LENGTH,
            num_beams=4,
            early_stopping=True
        )
    return tokenizer.decode(output_ids[0], skip_special_tokens=True).strip()

# === ĐÁNH GIÁ ===
image_files    = sorted(glob.glob(f"{DATA_IMAGE_DIR}/*.png"))[:MAX_SAMPLES]
exact_match    = 0
total_bleu     = 0.0
smoother       = SmoothingFunction().method1

print(f"\nĐang đánh giá {len(image_files)} ảnh...\n")

for i, image_path in enumerate(image_files):
    # Tìm code gốc tương ứng
    filename       = os.path.basename(image_path).replace(".png", ".txt")
    code_path      = os.path.join(DATA_CODE_DIR, filename)

    if not os.path.exists(code_path):
        continue

    with open(code_path, "r", encoding="utf-8") as f:
        reference_code = f.read().strip()

    predicted_code = predict(image_path)

    # Exact Match
    if predicted_code == reference_code:
        exact_match += 1

    # BLEU Score (so sánh theo từng token)
    ref_tokens  = reference_code.split()
    pred_tokens = predicted_code.split()
    bleu        = sentence_bleu([ref_tokens], pred_tokens, smoothing_function=smoother)
    total_bleu += bleu

    if (i + 1) % 10 == 0:
        print(f"  [{i+1}/{len(image_files)}] BLEU trung bình tạm: {total_bleu/(i+1):.4f}")

# === KẾT QUẢ ===
n = len(image_files)
print("\n" + "="*50)
print(f"KẾT QUẢ ĐÁNH GIÁ ({n} mẫu)")
print("="*50)
print(f"  Exact Match : {exact_match}/{n} = {exact_match/n*100:.1f}%")
print(f"  BLEU Score  : {total_bleu/n:.4f}  ({total_bleu/n*100:.1f}%)")
print("="*50)
