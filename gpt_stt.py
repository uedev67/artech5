
import time
import numpy as np
import stt_listen
import pyaudio
import wave
import tempfile
import cv2
import threading
from PIL import ImageFont, ImageDraw, Image
import torch


CHUNK = 2048               # 버퍼 크기 2048보다 작으면 끊김 발생
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000               # Whisper 권장 샘플레이트
DURATION = 7               # 기본 녹음 시간(초)

# Whisper 모델 미리 로드 : 녹음과 모델 로드가 동시에 일어나면 모델 로딩(gpu자원 독점) 때문에 녹음 끊김이 발생함 + 미리 로드하면 녹음 후 모델 연산 속도가 빨라짐 
# device = "cuda" if torch.cuda.is_available() else "cpu"
# print("사용 중인 디바이스:", device)
# model = whisper.load_model("medium")  # 4080에서는 medium 모델 권장인데, large-v3가 더 성능이 좋음
# print("✅ Whisper 모델 로드 완료")


def record_audio(duration=DURATION, sample_rate=RATE):

    # 녹음 중 영상 전체화면 재생 (ffplay)
    import subprocess
    video_path = r"C:\Artech5\Image_Box\mic_listening.mp4"
    ffplay_bin = "ffplay"
    cmd = [ffplay_bin, "-autoexit", "-fs", "-loglevel", "error", video_path]
    video_proc = subprocess.Popen(cmd)
    # # 카메라 먼저 켜기
    # stop_event = threading.Event()
    # cam_thread = threading.Thread(target=camera_thread_func, args=(stop_event,), daemon=True)
    # cam_thread.start()
    # time.sleep(0.5)  # 카메라 안정화


    p = pyaudio.PyAudio()
    stream = p.open(format=FORMAT, channels=CHANNELS, rate=sample_rate,
                    input=True, frames_per_buffer=CHUNK)

    print("🎙️ 녹음 시작...")
    frames = []

    for _ in range(0, int(sample_rate / CHUNK * duration)):
        data = stream.read(CHUNK, exception_on_overflow=False)  # 끊김 완화
        frames.append(data)

    print("✅ 녹음 완료.")

    stream.stop_stream()
    stream.close()
    p.terminate()

    # 녹음 끝나고 영상 프로세스 종료 대기
    video_proc.wait()

    # 임시 wav 저장
    temp_wav = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
    with wave.open(temp_wav.name, 'wb') as wf:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(p.get_sample_size(FORMAT))
        wf.setframerate(sample_rate)
        wf.writeframes(b''.join(frames))

    return temp_wav.name



def STT_whisper(audio_path, whisper_model):
    print("📝 Whisper STT 실행 중...")
    result = whisper_model.transcribe(audio_path, language="ko")
    return result["text"]


# 외부에서 사용할 gpt_listen 함수 : 앞서 로드된 whisper 모델을 사용
def gpt_listen(duration: int, whisper_model) -> str:

    audio_file_path = record_audio(duration=duration)
    print(f"📂 녹음 파일 경로: {audio_file_path}")
    transcribed_text = STT_whisper(audio_file_path, whisper_model)
    print(f"💬 변환된 텍스트: {transcribed_text}")
    return transcribed_text


# 실행부
if __name__ == "__main__":
    audio_file_path = record_audio(duration=7)  # 녹음 실행
    print(f"📂 녹음 파일 경로: {audio_file_path}")

    transcribed_text = STT_whisper(audio_file_path)
    print(f"💬 변환된 텍스트: {transcribed_text}")
