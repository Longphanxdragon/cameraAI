# === IMPORTS ===
import os

# --- Tự động chuyển về thư mục gốc chart2code/ ---
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT_DIR)

import torch
from datasets import load_dataset, Dataset
from PIL import Image
import glob
from transformers import (
    VisionEncoderDecoderModel,
    ViTImageProcessor,
    AutoTokenizer,
    Seq2SeqTrainingArguments,
    Seq2SeqTrainer,
    default_data_collator
)

# === CÀI ĐẶT ===
MODEL_NAME = "nlpconnect/vit-gpt2-image-captioning"
DATA_DIR   = "data/codes"
OUTPUT_DIR = "models"

print("Chuẩn bị model...")

# === TẢI MODEL & TOOLS ===
image_processor = ViTImageProcessor.from_pretrained(MODEL_NAME)
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
tokenizer.pad_token = tokenizer.eos_token
model = VisionEncoderDecoderModel.from_pretrained(MODEL_NAME)

print("Tải xong model. Chuẩn bị tải Dataset...")

# === TẢI DATASET ===
all_code_files = glob.glob(f'{DATA_DIR}/*.txt')
dataset = Dataset.from_dict({'file_path': all_code_files})
dataset = dataset.train_test_split(test_size=0.1)
train_dataset = dataset['train']
eval_dataset = dataset['test']

print(f"Tải xong {len(train_dataset)} train, {len(eval_dataset)} eval.")

# === HÀM PREPROCESS ===

# ----- SỬA LỖI Ở ĐÂY -----
def preprocess_function(examples): 
# --------------------------
    code_paths = examples['file_path']

    codes = [open(path, 'r', encoding='utf-8').read() for path in code_paths]
    image_paths = [path.replace('data/codes', 'data/images').replace('.txt', '.png') for path in code_paths]
    images = [Image.open(path).convert("RGB") for path in image_paths]

    pixel_values = image_processor(images=images, return_tensors="pt").pixel_values

    labels = tokenizer(
        codes,
        padding="max_length",
        truncation=True,
        max_length=512
    ).input_ids

    batch = {
        'pixel_values': pixel_values,
        'labels': labels
    }
    return batch

print("Đang xử lý dataset...")

train_dataset = train_dataset.map(preprocess_function, batched=True, remove_columns=['file_path'])
eval_dataset = eval_dataset.map(preprocess_function, batched=True, remove_columns=['file_path'])

print("Xử lý xong!")

# === CÀI ĐẶT HUẤN LUYỆN ===
training_args = Seq2SeqTrainingArguments(
    output_dir=OUTPUT_DIR,
    per_device_train_batch_size=8,
    per_device_eval_batch_size=8,
    predict_with_generate=True,
    eval_steps=20,
    save_steps=20,
    logging_steps=10,
    num_train_epochs=1,
    remove_unused_columns=False,
    label_names=["labels"]
)

# === TẠO TRAINER ===
trainer = Seq2SeqTrainer(
    model=model,
    tokenizer=image_processor,
    args=training_args,
    train_dataset=train_dataset,
    eval_dataset=eval_dataset,
    data_collator=default_data_collator
)

print("=== BẮT ĐẦU HUẤN LUYỆN ===")

# --- Bắt đầu train ---
trainer.train()

print("=== HUẤN LUYỆN HOÀN TẤT! ===")

# --- Lưu model ---
final_model_path = f"{OUTPUT_DIR}/final_model"
trainer.save_model(final_model_path)
image_processor.save_pretrained(final_model_path)
tokenizer.save_pretrained(final_model_path)

print(f"Đã lưu model vào: {final_model_path}")