import threading
from threading import Event
import time
import wave
import contextlib

import cv2
import simpleaudio as sa


def get_wav_duration_sec(wav_path: str) -> float:
    """WAV 파일 길이(초)를 반환 (외부 의존성 없이 wave 모듈 사용)"""
    with contextlib.closing(wave.open(wav_path, 'rb')) as wf:
        frames = wf.getnframes()
        rate = wf.getframerate()
        return frames / float(rate)


def play_audio_wav(wav_path: str, start_event: Event):
    """오디오 스레드: start_event 신호와 동시에 WAV 재생"""
    wave_obj = sa.WaveObject.from_wave_file(wav_path)
    start_event.wait()                     # 동시에 시작하기 위한 동기화 지점
    play_obj = wave_obj.play()
    play_obj.wait_done()                   # 오디오가 끝날 때까지 블록


def play_video_for_duration(video_path: str, duration_sec: float, start_event: Event, window_name="Video"):
    """비디오 스레드: start_event 이후 duration_sec 동안만 재생하고 종료"""
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"[ERROR] 비디오를 열 수 없습니다: {video_path}")
        return

    # FPS가 0으로 나올 때를 대비한 안전값
    fps = cap.get(cv2.CAP_PROP_FPS)
    fps = fps if fps and fps > 1e-2 else 30.0
    frame_interval = 1.0 / fps

    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)  # 창 크기 조절 가능
    cv2.resizeWindow(window_name, 960, 540)          # 보기 좋게 기본 크기 조정 (선택)

    start_event.wait()                # 오디오와 동시 시작
    t0 = time.perf_counter()          # 정확한 경과 시간 측정용
    next_frame_time = t0

    while True:
        # 종료 조건 1: 재생 시간 초과
        if time.perf_counter() - t0 >= duration_sec:
            break

        # 프레임 읽기
        ret, frame = cap.read()
        if not ret:                   # 영상이 더 짧다면 조기 종료
            break

        # 화면 표시
        cv2.imshow(window_name, frame)

        # 키 처리 (ESC로 강제 종료 가능)
        if cv2.waitKey(1) & 0xFF == 27:
            break

        # FPS에 맞춰 슬립 (가벼운 프레임 타이밍 보정)
        next_frame_time += frame_interval
        sleep_for = next_frame_time - time.perf_counter()
        if sleep_for > 0:
            time.sleep(sleep_for)

    cap.release()
    cv2.destroyWindow(window_name)



def AI_reply(video_path: str, wav_path: str) -> bool:
    """
    오디오(wav_path) 길이에 맞춰 비디오(video_path)를 동기 재생.
    사용 예: ai_reply_video = AI_reply(talking_no_voice, voice)
    성공 시 True, 실패 시 False 반환
    """
    try:
        duration = get_wav_duration_sec(wav_path)
        print(f"[INFO] 오디오 길이: {duration:.3f}초 (비디오는 이 시간까지만 재생)")

        start_event = Event()
        th_audio = threading.Thread(target=play_audio_wav, args=(wav_path, start_event), daemon=True)
        th_video = threading.Thread(target=play_video_for_duration, args=(video_path, duration, start_event), daemon=True)

        th_audio.start()
        th_video.start()

        # 두 스레드가 모두 준비되었다고 판단되면 거의 동시에 시작 신호를 보냄
        start_event.set()

        # 완료 대기
        th_audio.join()
        th_video.join()
        print("[INFO] 동시 재생 완료")
        return True
    except Exception as e:
        print(f"[ERROR] AI_reply 실행 실패: {e}")
        return False


# 테스트 실행부
if __name__ == "__main__":
    # 테스트용 경로 설정
    video_path = "path/to/your/video.mp4"
    wav_path = "path/to/your/audio.wav"

    # AI_reply 실행
    success = AI_reply(video_path, wav_path)
    if success:
        print("[TEST] AI_reply 정상 실행")
    else:
        print("[TEST] AI_reply 실행 중 오류 발생")