from transformers import VisionEncoderDecoderModel, ViTImageProcessor, AutoTokenizer
from PIL import Image
import torch
import os

# --- Tự động tìm thư mục gốc của project (chart2code/) ---
# Dù chạy script từ đâu cũng không bị lỗi đường dẫn
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT_DIR)

# --- CẤU HÌNH ---
MODEL_PATH      = "models/final_model"
TEST_IMAGE_PATH = "data/images/bar_chart_1.png"  # Đổi thành ảnh bạn muốn test
MAX_CODE_LENGTH = 512
# ---------------

print(f"Đang tải model từ: {MODEL_PATH}...")
try:
    model = VisionEncoderDecoderModel.from_pretrained(MODEL_PATH)
    image_processor = ViTImageProcessor.from_pretrained(MODEL_PATH)
    tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH)
except Exception as e:
    print(f"Lỗi: Không thể tải model từ '{MODEL_PATH}'. {e}")
    exit()

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model.to(device)
print(f"Model đã được tải và chạy trên: {device}")

def predict_code(image_path):
    try:
        img = Image.open(image_path).convert("RGB")

        pixel_values = image_processor(images=img, return_tensors="pt").pixel_values
        pixel_values = pixel_values.to(device) 

        # Thêm torch.no_grad() để tối ưu khi dự đoán (không cần tính gradient)
        with torch.no_grad():
            output_ids = model.generate(
                pixel_values,
                max_length=MAX_CODE_LENGTH, 
                num_beams=4,    
                early_stopping=True 
            )

        pred_code = tokenizer.decode(output_ids[0], skip_special_tokens=True)
        return pred_code.strip() 

    except FileNotFoundError:
        return f"Lỗi: Không tìm thấy file ảnh tại '{image_path}'"
    except Exception as e:
        return f"Lỗi không xác định khi dự đoán: {e}"

# --- CHẠY DỰ ĐOÁN ---
if __name__ == "__main__":
    generated_code = predict_code(TEST_IMAGE_PATH)
    
    print("\n" + "="*50)
    print(f"ẢNH ĐẦU VÀO: {TEST_IMAGE_PATH}")
    print("="*50)
    print(f"CODE DỰ ĐOÁN ĐƯỢC:\n")
    print(generated_code)
    print("="*50)
    
    # --- (Tùy chọn) So sánh với code gốc ---
    try:
        original_code_path = TEST_IMAGE_PATH.replace('images', 'codes').replace('.png', '.txt')
        with open(original_code_path, 'r', encoding='utf-8') as f:
            original_code = f.read()
        print("\nCODE GỐC (Để so sánh):\n")
        print(original_code.strip())
        print("="*50)
    except FileNotFoundError:
        print(f"(Không tìm thấy code gốc tại: {original_code_path})")
    except Exception as e:
        print(f"Lỗi khi đọc code gốc: {e}")