# ĐỒ ÁN: CHART2CODE (Phần 1)

## Mục tiêu

Huấn luyện mô hình AI (Chart2Code) để chuyển ảnh biểu đồ thành code Python (`matplotlib`). Model này là cơ sở cho các phần sau.

---

## Các File Gửi Kèm

* **`generate_dataset.py`**: Tạo dataset ảnh (`.png`) + code (`.txt`) cho 4 loại biểu đồ: cột, đường, tròn, scatter.
* **`train.py`**: Huấn luyện model. Dùng model nền `nlpconnect/vit-gpt2-image-captioning`.
* **`predict.py`**: Chạy thử model với 1 ảnh đầu vào.
* **`evaluate.py`**: Chấm điểm model (tính % độ chính xác).
* **`chart2code-model/final_model/`**: Thư mục chứa model đã huấn luyện.
* **`requirements.txt`**: (Nên tạo) Liệt kê thư viện cần cài.
* **`README.md`**: (File này) Hướng dẫn.

---

## Cài Đặt

1.  **Cài Python:** Cần **Python 3.11.9**. Chọn **"Add Python to PATH"** khi cài.
2.  **Tạo Môi trường ảo (Khuyến nghị):**
    ```bash
    # Trong thư mục đồ án
    python -m venv .venv 
    .\.venv\Scripts\activate 
    ```
    *(Mở Terminal sau này, chạy `.\.venv\Scripts\activate` trước).*
3.  **Cài Thư Viện:** Tạo file `requirements.txt` (nội dung như cũ), rồi chạy:
    ```bash
    python -m pip install -r requirements.txt 
    ```
    *(Cần cài `torch`, `transformers`, `datasets`, `accelerate`...).*

---

## Cách Chạy

1.  **Tạo Dataset (Nếu chưa có):**
    * Chạy `generate_dataset.py`. Sửa `TOTAL_SAMPLES` trong file nếu muốn tạo nhiều hơn (vd: 2500).
    ```bash
    python generate_dataset.py
    ```

2.  **Huấn Luyện Model:**
    * Chạy `train.py`. Bước này tốn thời gian và tạo thư mục `chart2code-model/final_model`.
    ```bash
    python train.py 
    ```
    *(Nhấn `Ctrl + C` để dừng giữa chừng).*

3.  **Chạy Thử 1 Ảnh:**
    * Mở `predict.py`, sửa `TEST_IMAGE_PATH` thành ảnh muốn thử.
    * Chạy:
    ```bash
    python predict.py
    ```

4.  **Chấm Điểm:**
    * Chạy `evaluate.py`. Sẽ báo % chính xác.
    ```bash
    python evaluate.py
    ```

---

## Thông Tin Thêm

* **Model:** `nlpconnect/vit-gpt2-image-captioning`.
* **Kỹ thuật:** Supervised Fine-Tuning.
* **Dataset:** Tự tạo bằng `generate_dataset.py`.

---

## Kết Quả

*Model train trên [Số lượng] ảnh. Mất khoảng [Thời gian] trên [CPU/GPU]. Độ chính xác (Exact Match): [Kết quả]%.*

*(Điền số liệu thực tế sau khi chạy).*

---

