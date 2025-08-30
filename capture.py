import cv2
import mediapipe as mp
import time
import os
import numpy as np
from PIL import ImageFont, Image, ImageDraw

def capture(save_dir=r"C:\ARTECH5\Image_Box\image1", filename="face_1.jpg"):
    """
    웹캠을 사용하여 사용자의 얼굴을 촬영하고 지정된 경로에 저장합니다.
    try...finally 구문을 사용하여 어떤 상황에서도 카메라 자원이 확실하게 해제되도록 보장합니다.
    """
    os.makedirs(save_dir, exist_ok=True)
    
    cap = cv2.VideoCapture(0)
    face_mesh = mp.solutions.face_mesh.FaceMesh(static_image_mode=False, max_num_faces=1)
    
    # --- [수정] 자원 해제를 보장하기 위해 try...finally 구문 사용 ---
    try:
        if not cap.isOpened():
            print("[ERROR] 카메라를 열 수 없습니다.")
            return None

        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)

        window_name = "Camera"
        cv2.namedWindow(window_name, cv2.WND_PROP_FULLSCREEN)
        cv2.setWindowProperty(window_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
        cv2.waitKey(1)

        font_path = "C:/Windows/Fonts/malgun.ttf"
        try:
            font = ImageFont.truetype(font_path, 40)
        except IOError:
            print(f"[WARNING] 폰트 파일을 찾을 수 없습니다: {font_path}. 기본 폰트를 사용합니다.")
            font = ImageFont.load_default()

        facing_start_time = None
        save_path = os.path.join(save_dir, filename)
        
        while True:
            ret, frame = cap.read()
            if not ret:
                print("[ERROR] 카메라에서 프레임을 읽을 수 없습니다.")
                break

            # 화면에 표시될 최종 이미지 생성 (정사각형으로 크롭 및 검은 배경에 배치)
            h, w, _ = frame.shape
            crop_size = min(h, w)
            start_x = (w - crop_size) // 2
            start_y = (h - crop_size) // 2
            square_frame = frame[start_y:start_y + crop_size, start_x:start_x + crop_size]
            
            display_size = 1080 # 1920x1080 화면에 맞춤
            resized_frame = cv2.resize(square_frame, (display_size, display_size))
            
            black_bg = np.zeros((1080, 1920, 3), dtype=np.uint8)
            x_offset = (1920 - display_size) // 2
            y_offset = (1080 - display_size) // 2
            black_bg[y_offset:y_offset + display_size, x_offset:x_offset + display_size] = resized_frame

            # 얼굴 정면 인식 로직
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            result = face_mesh.process(rgb_frame)
            current_time = time.time()
            is_facing = False

            if result.multi_face_landmarks:
                for face_landmarks in result.multi_face_landmarks:
                    # is_facing_forward 함수 로직을 직접 구현
                    landmarks = face_landmarks.landmark
                    if len(landmarks) >= 468:
                        nose_tip = landmarks[1]
                        left_eye = landmarks[33]
                        right_eye = landmarks[263]
                        
                        eye_center_x = (left_eye.x + right_eye.x) / 2
                        yaw_diff = abs(nose_tip.x - eye_center_x)
                        
                        if yaw_diff < 0.03: # 정면을 보고 있다고 판단하는 임계값
                            is_facing = True
                            break
            
            if is_facing:
                if facing_start_time is None:
                    facing_start_time = current_time
                elif current_time - facing_start_time >= 2.0:
                    print("[INFO] 정면 응시 2초 감지. 사진 저장 시도.")
                    cv2.imwrite(save_path, frame)
                    print(f"[INFO] 사진 저장 완료: {save_path}")
                    return save_path # 성공 시 경로 반환
            else:
                facing_start_time = None

            # 화면에 안내 문구 표시
            pil_img = Image.fromarray(cv2.cvtColor(black_bg, cv2.COLOR_BGR2RGB))
            draw = ImageDraw.Draw(pil_img)
            text = "카메라 정면을 2초간 응시해주세요"
            text_bbox = draw.textbbox((0, 0), text, font=font)
            text_width = text_bbox[2] - text_bbox[0]
            draw.text(((1920 - text_width) // 2, 50), text, font=font, fill=(255, 255, 255))
            final_display = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)

            cv2.imshow(window_name, final_display)

            if cv2.waitKey(1) & 0xFF == 27: # ESC 키를 누르면 종료
                print("[INFO] 사용자에 의해 촬영이 취소되었습니다.")
                break
        
        # 루프가 정상적으로 끝나거나 break로 종료된 경우 (저장 실패)
        return None

    finally:
        # --- [핵심] 어떤 경우에도 이 코드는 반드시 실행됨 ---
        print("[INFO] 카메라 자원을 정리하고 창을 닫습니다.")
        if cap.isOpened():
            cap.release() # 카메라 장치 해제
        cv2.destroyAllWindows() # 모든 OpenCV 창 닫기

if __name__ == "__main__":
    # 테스트를 위한 코드
    saved_path = capture()
    if saved_path:
        print(f"테스트 성공: 파일이 {saved_path}에 저장되었습니다.")
    else:
        print("테스트 실패 또는 취소됨.")

