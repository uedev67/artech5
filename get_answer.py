import multiprocessing
import cv2
import tkinter as tk
import numpy as np
import os

# gpt.py와 clova.py의 함수를 가져옵니다.
from gpt import ask_gpt
from clova import clova

def play_loading_video(stop_event: multiprocessing.Event, video_path: str):
    """
    영상이 종료될 때까지 전체 화면으로 반복 재생하는 프로세스입니다.
    stop_event가 설정되면 재생을 중단하고 창을 닫습니다.
    (ai_reply.py의 영상 재생 코드를 재사용 및 수정)
    """
    if not os.path.exists(video_path):
        print(f"[오류] 비디오 파일을 찾을 수 없습니다: {video_path}")
        return

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"[오류] 비디오를 열 수 없습니다: {video_path}")
        return

    # 화면 해상도를 가져와 전체 화면 설정
    root = tk.Tk()
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    root.destroy()

    # 영상을 화면 중앙에 맞추기 위한 좌표 계산
    video_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    video_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    scale = min(screen_width / video_width, screen_height / video_height)
    new_w, new_h = int(video_width * scale), int(video_height * scale)
    x_offset = (screen_width - new_w) // 2
    y_offset = (screen_height - new_h) // 2
    
    canvas = np.zeros((screen_height, screen_width, 3), dtype="uint8")
    window_name = "Loading"
    
    cv2.namedWindow(window_name, cv2.WND_PROP_FULLSCREEN)
    cv2.setWindowProperty(window_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

    while not stop_event.is_set():
        ret, frame = cap.read()
        if not ret:
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0) # 영상이 끝나면 처음으로 되감기
            continue

        # 리사이즈된 프레임을 검은 캔버스 중앙에 배치
        resized_frame = cv2.resize(frame, (new_w, new_h))
        canvas.fill(0) 
        canvas[y_offset:y_offset + new_h, x_offset:x_offset + new_w] = resized_frame
        
        cv2.imshow(window_name, canvas)

        # 25ms 딜레이 (약 40fps), ESC 누르면 강제 종료
        if cv2.waitKey(25) & 0xFF == 27:
            break
    
    cap.release()
    cv2.destroyAllWindows()

def run_ai_tasks(queue: multiprocessing.Queue, user_input, theme, target_age, speaker,name):

    try:
        print("[AI 작업] GPT에 답변을 요청합니다...")
        answer = ask_gpt(user_input, theme,name)
        print(f"[AI 작업] GPT 답변: {answer}")
        
        print("[AI 작업] Clova 음성 합성을 요청합니다...")
        voice_path = clova(target_age, answer, speaker=speaker)
        print(f"[AI 작업] Clova 음성 합성 완료: {voice_path}")
        
        queue.put(voice_path) # 성공 시, 결과값을 큐에 저장
    except Exception as e:
        print(f"[AI 작업 오류] AI 작업 중 오류 발생: {e}")
        queue.put(None) # 실패 시, None을 큐에 저장

def get_answer(user_input: str, theme: str, target_age : int, gender: str, speaker: str, name: str) -> str:

    loading_video_path = r"C:\Artech5\Image_Box\GPT_Loading.mp4"
    
    stop_event = multiprocessing.Event()
    result_queue = multiprocessing.Queue()
    
    # 1. 영상 재생 프로세스 생성
    video_process = multiprocessing.Process(
        target=play_loading_video, 
        args=(stop_event, loading_video_path)
    )
    
    # 2. AI 작업(GPT, Clova) 프로세스 생성
    ai_process = multiprocessing.Process(
        target=run_ai_tasks, 
        args=(result_queue, user_input, theme, target_age, speaker,name)
    )
    
    # 두 프로세스 동시 시작
    video_process.start()
    ai_process.start()
    
    # AI 작업이 끝날 때까지 대기
    ai_process.join()
    
    # AI 작업이 끝나면 영상 재생 프로세스에 중단 신호 전송
    stop_event.set()
    
    # 영상 프로세스가 완전히 종료될 때까지 잠시 대기
    video_process.join()
    
    # AI 작업 결과를 큐에서 가져와 반환
    result_voice_path = result_queue.get()
    
    return result_voice_path

# =================== 이 파일을 직접 실행할 경우, 아래 테스트 코드가 동작합니다 ===================
if __name__ == "__main__":
    # artech_test2.py와 동일하게 멀티프로세싱 초기화
    multiprocessing.freeze_support()
    multiprocessing.set_start_method('spawn', force=True)
    
    print("get_answer 함수 테스트를 시작합니다. (약 6~7초 소요)")
    print("로딩 영상이 전체 화면으로 재생됩니다.")
    
    # 테스트용 가상 입력값
    test_user_input = "너는 누구야?"
    test_theme = "사이버펑크"
    test_target_age = 50
    test_gender = "남자"
    
    # 함수 실행
    final_voice_path = get_answer(
        user_input=test_user_input,
        theme=test_theme,
        target_age=test_target_age,
        gender=test_gender
    )
    
    if final_voice_path:
        print(f"\n[최종 결과] 음성 파일 생성 성공!")
        print(f"-> 파일 경로: {final_voice_path}")
    else:
        print("\n[최종 결과] 음성 파일 생성에 실패했습니다.")