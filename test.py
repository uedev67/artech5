from gpt_stt import gpt_listen
from remove_audio import play_and_remove_audio_concurrently 
import time


# 최초 ai 인간 영상 재생과 사용자 마이크 듣는 함수 테스트
# ai 인간 영사 재생과 마이크 녹음 영상 재생 사이에 로딩 영상이 출력이 안 됌 . 원인 찾아야 함.

if __name__ == "__main__":

    talking_video = r"C:\Artech5\Image_Box\Image3\2025_08_06_17.06.05.mp4"


    # talking_video 재생 및 오디오 제거, whisper 모델 로드 (동시)
    talking_no_voice, whisper = play_and_remove_audio_concurrently(talking_video)

    # talking_video 재생이 끝난 후 로딩 중 영상 전체화면 재생
    import subprocess
    loading_video = r"C:\Artech5\Image_Box\loadinig.mp4"
    ffplay_bin = "ffplay"
    cmd = [ffplay_bin, "-autoexit", "-fs", "-loglevel", "error", loading_video]
    loading_proc = subprocess.Popen(cmd)

    # whisper 모델이 None일 경우 대기, 로드되면 로딩 영상 종료
    while whisper is None:
        time.sleep(0.1)
    loading_proc.terminate()  # whisper 모델 준비되면 영상 종료

    # whisper 모델이 준비된 후 gpt_listen 실행
    user_input = gpt_listen(duration=7, whisper_model=whisper)