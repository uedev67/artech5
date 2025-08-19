import multiprocessing
import vlc
import time
import os
import sys
import subprocess # subprocess 모듈 추가

# --- Task 1: Veo3 영상 재생 (변경 없음) ---
def play_veo3(theme):
    theme_video_map = {
        "지하벙커 생존자 커뮤니티": r"C:\Artech5\Image_Box\veo3\eco_smart.mp4",
        "사이버펑크": r"C:\Artech5\Image_Box\veo3\eco_smart.mp4",
        "에코 스마트시티": r"C:\Artech5\Image_Box\veo3\eco_smart.mp4",
        "화성 이주": r"C:\Artech5\Image_Box\veo3\eco_smart.mp4",
    }
    video_path = theme_video_map.get(theme)
    if not video_path or not os.path.exists(video_path):
        print(f"[VLC Player Error] '{theme}'에 해당하는 영상을 찾을 수 없거나 파일이 없습니다.")
        return

    instance = vlc.Instance("--no-xlib")
    player = instance.media_player_new()
    media = instance.media_new(video_path)
    player.set_media(media)
    player.set_fullscreen(True)
    
    print(f"[VLC Player] '{theme}' 테마 영상 재생 시작: {video_path}")
    while True:
        player.play()
        time.sleep(1.5)
        while player.is_playing():
            time.sleep(0.5)
        player.stop()


# --- 메인 함수: 외부 호출용 (수정됨) ---
def veo3_with_sadtalker(theme, first_voice, face2):
    base_path = "C:\\Artech5"
    main_path = os.path.join(base_path, "0.Main")
    sadtalker_result_dir = os.path.join(base_path, "Image_Box", "Image3")
    os.makedirs(sadtalker_result_dir, exist_ok=True)

    video_process = multiprocessing.Process(target=play_veo3, args=(theme,))
    print("메인 프로그램: 동영상 재생 프로세스를 시작합니다.")
    video_process.start()

    worker_script_path = os.path.join(main_path, 'sadtalker_worker.py')
    # [수정] Worker에게 face2 경로를 전달하기 위해 --face_path 인자 추가
    command = [
        sys.executable,
        worker_script_path,
        '--audio', first_voice,
        '--result_dir', sadtalker_result_dir,
        '--face_path', face2  # <-- 이 인자 추가
    ]

    print("메인 프로그램: SadTalker Worker 프로세스를 시작합니다.")
    sadtalker_proc = subprocess.Popen(
        command,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        cwd=main_path,
        creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
    )
    
    # ... (이하 communicate() 부터 return 까지의 코드는 변경 없습니다) ...
    stdout, stderr = sadtalker_proc.communicate()

    if stderr:
        print(f"[WORKER_ERROR]\n{stderr.strip()}")

    talking_video = stdout.strip().splitlines()[-1] if stdout.strip() else None

    if talking_video and os.path.exists(talking_video):
        print(f"메인 프로그램: Worker로부터 결과물 경로 수신 성공: {talking_video}")
    else:
        print("메인 프로그램: Worker로부터 유효한 결과물을 받지 못했습니다.")
        talking_video = None

    if video_process.is_alive():
        print("메인 프로그램: SadTalker 작업이 완료되어 동영상 재생을 종료합니다.")
        video_process.terminate()
        video_process.join()

    print("메인 프로그램: 모든 작업이 완료되었습니다.")
    return talking_video




# 테스트 
if __name__ == "__main__":
    try:
        multiprocessing.set_start_method('spawn')
    except RuntimeError:
        pass

    video_theme = "지하벙커 생존자 커뮤니티"
    voice_path = r"C:\Artech5\Image_Box\eco_50_60.wav"
    # [수정] 테스트를 위한 face2 이미지 경로 예시
    face2_path = r"C:\Artech5\Image_Box\Image2\image_age_60.jpg"

    # [수정] 변경된 함수에 맞게 테스트 호출
    generated_video_path = veo3_with_sadtalker(video_theme, voice_path, face2_path)

    if generated_video_path:
        print(f"\n✅ 최종 생성된 영상 경로: {generated_video_path}")
    else:
        print("\n❌ 영상 생성에 실패했습니다.")