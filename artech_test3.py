import multiprocessing
from multi3 import play_and_strip_audio
from stt_listen import mic_listen



if __name__ == "__main__":
    multiprocessing.freeze_support()
    multiprocessing.set_start_method('spawn', force=True)

    print("최소 기능 테스트 시작...")
    # 실제 존재하는 비디오 파일 경로를 넣어야 합니다.
    talking_video = r"C:\Artech5\Image_Box\Image3\2025_08_19_16.13.14.mp4"

    talking_no_voice = play_and_strip_audio(talking_video)
    
    user_input = mic_listen(
        loading_video=r"C:\Artech5\Image_Box\loading.mp4",
        ready_video=r"C:\Artech5\Image_Box\mic_listening.mp4",
        duration=7
    )

    print(f"user_input:", user_input)