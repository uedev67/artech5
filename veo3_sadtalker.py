import multiprocessing
import os
import cv2




# --- 작업 1: 별도의 프로세스에서 실행될 동영상 재생 함수 ---
def play_video_func(video_path):

    while True: # 비디오를 무한 반복 재생하기 위한 루프
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            print(f"[Video Player] 에러: 비디오 파일을 열 수 없습니다: {video_path}")
            return

        print(f"[Video Player] 영상 재생 시작: {video_path}")
        
        window_name = 'Playing Video'
        cv2.namedWindow(window_name, cv2.WINDOW_FULLSCREEN)
        cv2.setWindowProperty(window_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

        while cap.isOpened():
            ret, frame = cap.read()
            if ret:
                cv2.imshow(window_name, frame)
                if cv2.waitKey(25) & 0xFF == ord('q'):
                    cap.release()
                    cv2.destroyAllWindows()
                    print("[Video Player] 사용자가 재생을 중단했습니다.")
                    return # 'q'를 누르면 함수 전체 종료
            else:
                break # 비디오의 끝에 도달하면 루프 탈출
        
        cap.release() # 다음 반복을 위해 자원 해제
        print("[Video Player] 영상 한 번 재생 완료. 다시 시작합니다.")
    cv2.destroyAllWindows()


# --- 작업 2: 별도의 프로세스에서 실행될 SadTalker 실행 함수 ---
def run_sadtalker_func(source_image, driven_audio, result_dir):
    from sadtalker import run_sadtalker
    print("[SadTalker] 비디오 생성을 시작합니다.")
    result_path = run_sadtalker(
        face_path=source_image,
        audio_path=driven_audio,
        result_dir=result_dir,
        size=256,
        preprocess="crop",
        verbose=True
    )
    if result_path:
        print(f"[SadTalker] 비디오 생성 완료: {result_path}")
    else:
        print("[SadTalker] 비디오 생성 실패.")


if __name__ == "__main__":
    # 중요: Windows 및 CUDA 환경에서 멀티프로세싱 시 'spawn' 방식을 사용하는 것이 안전합니다.
    multiprocessing.set_start_method('spawn')

    video_to_play_path = r"C:\ARTECH_3\년대_지하_벙커_생존자_취침.mp4"  

    sadtalker_source_image = r"C:\ARTECH_3\Image_Box\image2\image_age_65.jpg"
    sadtalker_driven_audio = r"C:\ARTECH_3\clova_voice\5060 남자\voice_nraewon.wav"
    sadtalker_result_dir = r"C:\ARTECH_3\Image_Box\result.mp4"

    video_process = multiprocessing.Process(target=play_video_func, args=(video_to_play_path,))
    sadtalker_process = multiprocessing.Process(target=run_sadtalker_func, args=(sadtalker_source_image, sadtalker_driven_audio, sadtalker_result_dir))

    print("메인 프로그램: 동영상 재생 및 SadTalker 프로세스를 시작합니다.")
    video_process.start()
    sadtalker_process.start()


    # 각 프로세스가 끝날 때까지 메인 스크립트가 기다리도록 합니다.
    sadtalker_process.join() # SadTalker 작업이 끝날 때까지 기다림
    
    # SadTalker 작업이 끝나면 영상 재생 프로세스를 강제 종료
    if video_process.is_alive():
        print("메인 프로그램: SadTalker 작업이 완료되어 동영상 재생을 종료합니다.")
        video_process.terminate() # or .kill()
        video_process.join()

    print("메인 프로그램: 모든 작업이 완료되었습니다.")