"""
Tuần 1 — Test kết nối RTSP với IP Camera
=========================================
Chạy: python test_rtsp.py

Nếu không có camera thật, dùng video file để giả lập.
"""

import cv2
import sys

# ─────────────────────────────────────────────────────────────
# ĐỔI THÔNG TIN CAMERA CỦA BẠN Ở ĐÂY
# ─────────────────────────────────────────────────────────────

# Ví dụ các URL theo từng hãng:
RTSP_TEMPLATES = {
    "hikvision": "rtsp://{user}:{password}@{ip}:554/Streaming/Channels/101",
    "ezviz":     "rtsp://{user}:{password}@{ip}:554/h264/ch1/main/av_stream",
    "imou":      "rtsp://{user}:{password}@{ip}:554/cam/realmonitor?channel=1&subtype=0",
    "tenda":     "rtsp://{user}:{password}@{ip}:554/stream1",
    "generic":   "rtsp://{user}:{password}@{ip}:554/stream",
}

# ── Điền thông tin camera của bạn ──
CAMERA_BRAND    = "hikvision"   # đổi thành: ezviz / imou / tenda / generic
CAMERA_IP       = "192.168.1.64"
CAMERA_USER     = "admin"
CAMERA_PASSWORD = "admin123"

# ── Hoặc dùng video file để test khi chưa có camera ──
# SOURCE = "test_video.mp4"      # bỏ comment dòng này nếu dùng video
SOURCE = 0                     # bỏ comment dòng này nếu dùng webcam USB

# ─────────────────────────────────────────────────────────────

def build_rtsp_url(brand, ip, user, password):
    template = RTSP_TEMPLATES.get(brand, RTSP_TEMPLATES["generic"])
    return template.format(ip=ip, user=user, password=password)

def test_camera(source):
    print(f"\n{'='*50}")
    print(f"🔌 Đang kết nối tới: {source}")
    print(f"{'='*50}\n")

    cap = cv2.VideoCapture(source)

    if not cap.isOpened():
        print("❌ Không thể kết nối! Kiểm tra lại:")
        print("   - IP camera có đúng không?")
        print("   - Username/password có đúng không?")
        print("   - Camera và máy tính có cùng mạng LAN không?")
        return False

    print("✅ Kết nối thành công!\n")

    # Thông tin stream
    width  = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps    = cap.get(cv2.CAP_PROP_FPS)
    print(f"📐 Độ phân giải: {width} x {height}")
    print(f"🎞️  FPS: {fps:.1f}")

    # Đọc thử 5 frame
    print(f"\n📸 Đọc thử 5 frames...")
    for i in range(5):
        ret, frame = cap.read()
        if not ret:
            print(f"   Frame {i+1}: ❌ Đọc thất bại")
        else:
            print(f"   Frame {i+1}: ✅ shape={frame.shape}, dtype={frame.dtype}")

    # Lưu ảnh mẫu
    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
    ret, frame = cap.read()
    if ret:
        output_path = "sample_frame.jpg"
        cv2.imwrite(output_path, frame)
        print(f"\n💾 Đã lưu ảnh mẫu tại: {output_path}")
        print("   Mở file đó để kiểm tra hình ảnh từ camera\n")

    cap.release()
    print("✅ Test hoàn thành! Camera hoạt động tốt.")
    return True


if __name__ == "__main__":
    # Kiểm tra xem có dùng video file không
    try:
        source = SOURCE  # type: ignore
        print("📁 Dùng video file/webcam làm nguồn test")
    except NameError:
        # Dùng RTSP camera thật
        source = build_rtsp_url(CAMERA_BRAND, CAMERA_IP, CAMERA_USER, CAMERA_PASSWORD)
        print(f"🏷️  Hãng camera: {CAMERA_BRAND.upper()}")

    test_camera(source)
