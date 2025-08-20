import multiprocessing
from multiprocessing import Event
import time
import wave
import contextlib
import tkinter as tk # 화면 해상도를 얻기 위해 import

import cv2
import simpleaudio as sa
import numpy as np # 검은 배경(캔버스)을 만들기 위해 import


def get_wav_duration_sec(wav_path: str) -> float:
    """WAV 파일 길이(초)를 반환 (외부 의존성 없이 wave 모듈 사용)"""
    with contextlib.closing(wave.open(wav_path, 'rb')) as wf:
        frames = wf.getnframes()
        rate = wf.getframerate()
        return frames / float(rate)



def play_audio_wav(wav_path: str, start_event: Event):
    """오디오 프로세스: start_event 신호와 동시에 WAV 재생"""
    wave_obj = sa.WaveObject.from_wave_file(wav_path)
    start_event.wait()
    play_obj = wave_obj.play()
    play_obj.wait_done()



def play_video_for_duration(video_path: str, duration_sec: float, start_event: Event, window_name="Video"):
    """비디오 프로세스: 1:1 비율을 유지하며 전체 화면으로 영상을 반복 재생"""
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"[ERROR] 비디오를 열 수 없습니다: {video_path}")
        return

    # 1. 화면 해상도 가져오기
    root = tk.Tk()
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    root.destroy()

    # 2. 영상 원본 크기 및 비율에 맞는 새 크기 계산
    video_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    video_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    # 화면 높이에 맞춰 영상 크기 조절 (1:1 영상이므로 높이기준)
    new_h = screen_height
    new_w = new_h # 1:1 비율

    # 만약 계산된 너비가 화면 너비보다 크면, 너비에 맞춰 재조정
    if new_w > screen_width:
        new_w = screen_width
        new_h = new_w # 1:1 비율

    # 3. 영상을 중앙에 배치하기 위한 좌표 계산
    x_offset = (screen_width - new_w) // 2
    y_offset = (screen_height - new_h) // 2
    
    # 4. 검은색 배경(캔버스) 생성
    canvas = np.zeros((screen_height, screen_width, 3), dtype="uint8")

    fps = cap.get(cv2.CAP_PROP_FPS)
    fps = fps if fps > 1e-2 else 30.0
    frame_interval = 1.0 / fps

    # 전체 화면 설정
    cv2.namedWindow(window_name, cv2.WND_PROP_FULLSCREEN)
    cv2.setWindowProperty(window_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

    start_event.wait()
    t0 = time.perf_counter()
    next_frame_time = t0

    while True:
        if time.perf_counter() - t0 >= duration_sec:
            break

        ret, frame = cap.read()
        if not ret:
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            continue
        
        # 5. 프레임 크기를 조절하고 검은 캔버스 중앙에 삽입
        resized_frame = cv2.resize(frame, (new_w, new_h))
        # 매번 새로 검은 캔버스를 만들어 붙여넣거나, 기존 캔버스의 해당 영역만 업데이트
        canvas[y_offset:y_offset + new_h, x_offset:x_offset + new_w] = resized_frame

        # 최종 결과물(캔버스)을 화면에 표시
        cv2.imshow(window_name, canvas)

        if cv2.waitKey(1) & 0xFF == 27:
            break

        next_frame_time += frame_interval
        sleep_for = next_frame_time - time.perf_counter()
        if sleep_for > 0:
            time.sleep(sleep_for)

    cap.release()
    cv2.destroyWindow(window_name)



def AI_reply(video_path: str, wav_path: str) -> bool:
    # 이 부분은 변경 사항 없습니다.
    try:
        duration = get_wav_duration_sec(wav_path)
        print(f"[INFO] 오디오 길이: {duration:.3f}초 (비디오는 이 시간 동안 반복 재생)")

        start_event = Event()
        
        p_audio = multiprocessing.Process(target=play_audio_wav, args=(wav_path, start_event), daemon=True)
        p_video = multiprocessing.Process(target=play_video_for_duration, args=(video_path, duration + 0.5, start_event), daemon=True) # 오디오보다 영상이 0.5초 늦게 마무리

        p_audio.start()
        p_video.start()

        start_event.set()

        p_audio.join()
        p_video.join()
        print("[INFO] 동시 재생 완료")
        return True
    except Exception as e:
        print(f"[ERROR] AI_reply 실행 실패: {e}")
        return False



# 테스트 실행부
if __name__ == "__main__":
    # 테스트용 경로 설정
    video_path = "path/to/your/1_1_video.mp4" # 1:1 비율의 영상 경로
    wav_path = "path/to/your/audio.wav"

    success = AI_reply(video_path, wav_path)
    if success:
        print("[TEST] AI_reply 정상 실행")
    else:
        print("[TEST] AI_reply 실행 중 오류 발생")