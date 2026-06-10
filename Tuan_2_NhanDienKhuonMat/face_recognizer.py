import face_recognition
import cv2
import os
import numpy as np

class FaceRecognizer:
    def __init__(self, known_faces_dir="data/known_faces"):
        self.known_faces_dir = known_faces_dir
        self.known_face_encodings = []
        self.known_face_names = []
        self.load_known_faces()

    def load_known_faces(self):
        print(f"Đang tải dữ liệu khuôn mặt từ: {self.known_faces_dir}...")
        if not os.path.exists(self.known_faces_dir):
            print(f"Cảnh báo: Thư mục {self.known_faces_dir} không tồn tại.")
            return

        for filename in os.listdir(self.known_faces_dir):
            if filename.endswith((".jpg", ".jpeg", ".png")):
                filepath = os.path.join(self.known_faces_dir, filename)
                # Lấy tên file làm tên người (Ví dụ: Long.jpg -> Tên: Long)
                name = os.path.splitext(filename)[0]
                
                # Load ảnh và trích xuất đặc điểm khuôn mặt
                image = face_recognition.load_image_file(filepath)
                encodings = face_recognition.face_encodings(image)
                
                if encodings:
                    self.known_face_encodings.append(encodings[0])
                    self.known_face_names.append(name)
                    print(f"  + Đã học khuôn mặt của: {name}")
                else:
                    print(f"  - Cảnh báo: Không tìm thấy khuôn mặt rõ ràng trong file {filename}")
                    
        print(f"-> Hoàn tất. Đã học tổng cộng {len(self.known_face_names)} khuôn mặt.")

    def recognize_faces(self, frame):
        # Thu nhỏ khung hình xuống 1/4 để xử lý nhanh hơn (tăng FPS)
        small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
        
        # Chuyển đổi màu từ BGR (OpenCV) sang RGB (face_recognition)
        rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)
        
        # Tìm tọa độ các khuôn mặt và trích xuất đặc điểm
        face_locations = face_recognition.face_locations(rgb_small_frame)
        face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)
        
        face_names = []
        for face_encoding in face_encodings:
            name = "Unknown"

            if self.known_face_encodings:
                # Tính toán khoảng cách (độ sai lệch) giữa khuôn mặt trên camera và các khuôn mặt đã học
                face_distances = face_recognition.face_distance(self.known_face_encodings, face_encoding)
                best_match_index = np.argmin(face_distances)
                
                # Nếu độ sai lệch nhỏ hơn ngưỡng (mặc định của thư viện là 0.6) thì coi như khớp
                if face_distances[best_match_index] < 0.6:
                    name = self.known_face_names[best_match_index]

            face_names.append(name)
            
        # Nhân tọa độ lên 4 lần (vì lúc nãy đã thu nhỏ 1/4)
        scaled_face_locations = []
        for top, right, bottom, left in face_locations:
            top *= 4
            right *= 4
            bottom *= 4
            left *= 4
            scaled_face_locations.append((top, right, bottom, left))
            
        return scaled_face_locations, face_names
