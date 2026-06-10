import cv2
from face_recognizer import FaceRecognizer

def main():
    print("==================================================")
    print("📹 CamVision AI - Chế độ Nhận Diện Khuôn Mặt")
    print("==================================================")
    
    # Khởi tạo recognizer và trỏ thư mục chứa ảnh khuôn mặt
    recognizer = FaceRecognizer(known_faces_dir="data/known_faces")
    
    print("\nĐang mở webcam (Hoặc đổi số 0 thành đường dẫn RTSP)...")
    video_capture = cv2.VideoCapture(0)
    
    if not video_capture.isOpened():
        print("❌ Lỗi: Không thể mở camera!")
        return

    print("✅ Đã kết nối camera. Nhấn 'q' trên bàn phím để thoát.")
    
    while True:
        # Đọc 1 khung hình từ camera
        ret, frame = video_capture.read()
        if not ret:
            print("Không thể đọc khung hình từ camera.")
            break
            
        # Tìm và nhận diện khuôn mặt
        face_locations, face_names = recognizer.recognize_faces(frame)
        
        # Vẽ khung và ghi tên lên từng khuôn mặt tìm được
        for (top, right, bottom, left), name in zip(face_locations, face_names):
            # Nếu nhận ra (khác Unknown) thì khung màu xanh lá, ngược lại khung màu đỏ
            color = (0, 255, 0) if name != "Unknown" else (0, 0, 255)
            
            # Vẽ viền vuông
            cv2.rectangle(frame, (left, top), (right, bottom), color, 2)

            # Vẽ ô nền cho tên
            cv2.rectangle(frame, (left, bottom - 30), (right, bottom), color, cv2.FILLED)
            font = cv2.FONT_HERSHEY_DUPLEX
            # In tên người
            cv2.putText(frame, name, (left + 6, bottom - 6), font, 0.6, (255, 255, 255), 1)

        # Hiển thị cửa sổ video trực tiếp lên màn hình
        cv2.imshow('CamVision AI - Test Nhan Dien', frame)

        # Nhấn phím 'q' để tắt
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # Dọn dẹp sau khi tắt
    video_capture.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
