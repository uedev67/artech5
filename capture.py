import cv2
import mediapipe as mp
import time
import os


# 얼굴 캡처 함수: 얼굴 촬영 후 저장 경로 반환
def capture(save_dir=r"C:\ARTECH5\Image_Box\image1", filename="face_1.jpg"):
    os.makedirs(save_dir, exist_ok=True)

    mp_face_mesh = mp.solutions.face_mesh
    face_mesh = mp_face_mesh.FaceMesh(static_image_mode=False, max_num_faces=1)

    def is_facing_forward(landmarks):
        if len(landmarks) < 468:
            return False
        left_eye = landmarks[33]
        right_eye = landmarks[263]
        nose_tip = landmarks[1]
        chin = landmarks[152]
        forehead = landmarks[10]
        eye_center_x = (left_eye.x + right_eye.x) / 2
        nose_eye_diff_x = abs(nose_tip.x - eye_center_x)
        eye_diff_y = abs(left_eye.y - right_eye.y)
        vertical_center_y = (chin.y + forehead.y) / 2
        nose_pitch_diff_y = abs(nose_tip.y - vertical_center_y)
        return (nose_eye_diff_x < 0.03) and (eye_diff_y < 0.02) and (nose_pitch_diff_y < 0.04)

    def save_face_image(image, save_path):
        cv2.imwrite(save_path, image)
        print(f"[INFO] 최종 얼굴 저장 완료: {save_path}")

    def verify_and_save(temp_image, face_mesh, save_path):
        temp_rgb = cv2.cvtColor(temp_image, cv2.COLOR_BGR2RGB)
        result = face_mesh.process(temp_rgb)
        if result.multi_face_landmarks:
            for landmarks in result.multi_face_landmarks:
                if is_facing_forward(landmarks.landmark):
                    save_face_image(temp_image, save_path)
                    return True
        return False

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("[ERROR] 카메라 열기 실패")
        return None

    facing_start_time = None
    save_path = os.path.join(save_dir, filename)

    while True:
        ret, frame = cap.read()
        if not ret:
            break
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        result = face_mesh.process(rgb)
        current_time = time.time()
        if result.multi_face_landmarks:
            for landmarks in result.multi_face_landmarks:
                if len(landmarks.landmark) < 468:
                    continue
                if is_facing_forward(landmarks.landmark):
                    if facing_start_time is None:
                        facing_start_time = current_time
                    elif current_time - facing_start_time >= 3.0:
                        print("[INFO] 정면 응시 3초 이상 감지됨. 사진 촬영 시도 중...")
                        while True:
                            ret2, retry_frame = cap.read()
                            if not ret2:
                                continue
                            temp_image = retry_frame.copy()
                            if verify_and_save(temp_image, face_mesh, save_path):
                                print("[INFO] 성공적으로 저장 후 종료.")
                                cap.release()
                                cv2.destroyAllWindows()
                                return save_path
                            else:
                                print("[INFO] 2차 정면 판별 실패. 다시 시도 중...")
                            time.sleep(0.5)
                else:
                    facing_start_time = None
        cv2.imshow("Camera", frame)
        if cv2.waitKey(1) & 0xFF == 27:
            break
    cap.release()
    cv2.destroyAllWindows()
    return None
