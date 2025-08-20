# audio_recorder_v2.py

import multiprocessing
import time
import os
import whisper
import pyaudio
import wave
import tempfile

# PyAudio 녹음 설정
CHUNK = 2048
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000  # Whisper 권장 샘플레이트


# --- 헬퍼 함수: 영상 재생 ---
def play_fullscreen_video(video_path):
    """
    별도의 프로세스에서 지정된 영상을 전체화면으로 무한 반복 재생합니다.
    """
    import vlc
    if not os.path.isfile(video_path):
        print(f"[오류] 영상 파일을 찾을 수 없습니다: {video_path}")
        return

    # --input-repeat=-1 옵션으로 무한 반복 설정
    instance = vlc.Instance("--no-xlib --quiet --input-repeat=-1")
    player = instance.media_player_new()
    media = instance.media_new(video_path)
    player.set_media(media)
    player.set_fullscreen(True)
    player.play()
    
    # 프로세스가 종료 신호를 받을 때까지 대기
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        player.stop()



# --- 헬퍼 함수: 오디오 녹음 (gpt_stt.py 로직 통합) ---
def record_audio_pyaudio(duration, sample_rate):
    """
    PyAudio를 사용하여 마이크에서 오디오를 녹음하고 임시 파일 경로를 반환합니다.
    """
    p = pyaudio.PyAudio()
    stream = p.open(format=FORMAT, channels=CHANNELS, rate=sample_rate,
                    input=True, frames_per_buffer=CHUNK)

    print(f"\n[마이크] 지금부터 {duration}초 동안 녹음을 시작합니다. 말씀해주세요...")
    frames = []
    for _ in range(0, int(sample_rate / CHUNK * duration)):
        data = stream.read(CHUNK, exception_on_overflow=False)
        frames.append(data)
    print("[마이크] 녹음 완료.")

    stream.stop_stream()
    stream.close()
    p.terminate()

    temp_wav = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
    with wave.open(temp_wav.name, 'wb') as wf:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(p.get_sample_size(FORMAT))
        wf.setframerate(sample_rate)
        wf.writeframes(b''.join(frames))
    
    return temp_wav.name



# --- 메인 실행 함수 ---
def stt_with_visual_cues(loading_video: str, ready_video: str, duration: int = 5) -> str:
    """
    모델 로딩과 녹음 대기 상태를 별도의 영상으로 표시하며 음성 인식을 수행합니다.
    """
    print("--- 음성 인식 시퀀스 시작 ---")
    
    # 1. '로딩 중' 영상 재생 프로세스 시작
    loading_process = multiprocessing.Process(target=play_fullscreen_video, args=(loading_video,), daemon=True)
    loading_process.start()
    print(f"[시스템] 로딩 영상 재생 시작: {loading_video}")

    # 2. Whisper 모델 로드 (시간이 가장 오래 걸리는 작업)
    print("[Whisper] 'medium' 모델을 로드하는 중입니다...")
    model = whisper.load_model("medium")
    print("[Whisper] 모델 로드 완료.")

    # 3. '로딩 중' 영상 종료
    loading_process.terminate()
    loading_process.join()
    print("[시스템] 로딩 영상 종료.")

    # 4. '녹음 준비 완료' 영상 재생 프로세스 시작
    ready_process = multiprocessing.Process(target=play_fullscreen_video, args=(ready_video,), daemon=True)
    ready_process.start()
    print(f"[시스템] 녹음 준비 완료 영상 재생 시작: {ready_video}")

    # 5. 오디오 녹음 실행
    audio_path = record_audio_pyaudio(duration=duration, sample_rate=RATE)

    # 6. '녹음 준비 완료' 영상 종료
    ready_process.terminate()
    ready_process.join()
    print("[시스템] 녹음 준비 완료 영상 종료.")

    # 7. 녹음된 음성을 텍스트로 변환
    print("[Whisper] 음성 인식을 시작합니다...")
    result = model.transcribe(audio_path, language="ko")
    transcribed_text = result["text"]
    
    # 8. 임시 녹음 파일 삭제
    os.remove(audio_path)
    
    print("--- 음성 인식 시퀀스 완료 ---\n")
    return transcribed_text