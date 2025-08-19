import multiprocessing
from remove_audio import play_and_process_concurrently


if __name__ == "__main__":
    multiprocessing.freeze_support()
    multiprocessing.set_start_method('spawn', force=True)

    print("최소 기능 테스트 시작...")
    # 실제 존재하는 비디오 파일 경로를 넣어야 합니다.
    video_file = r"C:\Artech5\Image_Box\Image3\2025_08_19_16.13.14.mp4"

    output, model = play_and_process_concurrently(video_file)

    print(f"테스트 성공! 결과: {output}, {model}")