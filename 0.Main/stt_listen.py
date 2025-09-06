import multiprocessing
import time
import os
import pyaudio
import wave
import tempfile
import vlc

# PyAudio 녹음 설정 (변경 없음)
CHUNK = 2048
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000

# --- 헬퍼 함수: 영상 재생 (변경 없음) ---
def play_fullscreen_video(video_path, subtitle_text=None):
    if not os.path.isfile(video_path):
        print(f"[오류] 영상 파일을 찾을 수 없습니다: {video_path}")
        return

    vlc_options = [
        "--no-xlib", "--quiet", "--input-repeat=-1", "--sub-source=marq"
    ]
    instance = vlc.Instance(" ".join(vlc_options))
    player = instance.media_player_new()
    media = instance.media_new(video_path)
    player.set_media(media)

    if subtitle_text:
        player.video_set_marquee_int(vlc.VideoMarqueeOption.Enable, 1)
        player.video_set_marquee_string(vlc.VideoMarqueeOption.Text, subtitle_text.encode('utf-8'))
        player.video_set_marquee_int(vlc.VideoMarqueeOption.Position, 8)
        player.video_set_marquee_int(vlc.VideoMarqueeOption.Size, 60)
        player.video_set_marquee_int(vlc.VideoMarqueeOption.Color, 0xFFFFFF)
        player.video_set_marquee_int(vlc.VideoMarqueeOption.Timeout, 0)

    player.set_fullscreen(True)
    player.play()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        player.stop()

# --- 헬퍼 함수: 오디오 녹음 (변경 없음) ---
def record_audio_pyaudio(duration, sample_rate):
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

# --- 메인 실행 함수 (수정됨) ---
def mic_listen(loading_video: str, ready_video: str, duration: int = 5, subtitle_text: str = None) -> str:
    print("--- 음성 인식 시퀀스 시작 ---")
    
    # 1. '로딩 중' 영상 재생 (자막 표시 O)
    loading_process = multiprocessing.Process(target=play_fullscreen_video, args=(loading_video, subtitle_text), daemon=True)
    loading_process.start()
    print(f"[시스템] 로딩 영상 재생 시작: {loading_video}")

    import whisper
    # 2. Whisper 모델 로드
    print("[Whisper] 모델을 로드하는 중입니다...")
    model = whisper.load_model("large-v3")
    print("[Whisper] 모델 로드 완료.")

    # 3. '로딩 중' 영상 종료
    loading_process.terminate()
    loading_process.join()
    print("[시스템] 로딩 영상 종료.")

    # 4. '녹음 준비 완료' 영상 재생 (자막 표시 X)
    # [수정] 자막을 표시하지 않도록 subtitle_text 인자 제거
    ready_process = multiprocessing.Process(target=play_fullscreen_video, args=(ready_video,), daemon=True)
    ready_process.start()
    print(f"[시스템] 녹음 준비 완료 영상 재생 시작: {ready_video}")

    # 5. 오디오 녹음 실행
    audio_path = record_audio_pyaudio(duration=duration, sample_rate=RATE)

    # 6. '녹음 준비 완료' 영상 종료
    ready_process.terminate()
    ready_process.join()
    print("[시스템] 녹음 준비 완료 영상 종료.")

    # [삭제] 음성 변환 중 영상을 재생하던 7, 8, 9번 과정 제거
    
    # 7. 녹음된 음성을 텍스트로 변환
    print("[Whisper] 음성 인식을 시작합니다...")
    result = model.transcribe(audio_path, language="ko")
    transcribed_text = result["text"]
    print(f"[Whisper] 변환 결과: {transcribed_text}")
    
    # 8. 임시 녹음 파일 삭제
    os.remove(audio_path)

    print("--- 음성 인식 시퀀스 완료 ---\n")
    return transcribed_text