# veo3_sam.py

import multiprocessing
import vlc
import time
import os
from sam import run_sam # sam.py의 run_sam 함수를 직접 임포트


# veo3 인트로 영상 재생 함수
def play_veo3_intro():

    video_path = r"C:\Artech5\Image_Box\veo3\eco_smart.mp4"
    if not os.path.exists(video_path):
        print(f"[VLC Player Error] 인트로 영상을 찾을 수 없습니다: {video_path}")
        return

    instance = vlc.Instance("--no-xlib")
    player = instance.media_player_new()
    media = instance.media_new(video_path)
    player.set_media(media)
    player.set_fullscreen(True)
    
    print(f"[VLC Player] 인트로 영상 재생 시작: {video_path}")
    while True:
        player.play()
        time.sleep(1.5)
        # 영상 재생이 끝날 때까지 기다렸다가 다시 재생
        while player.is_playing():
            time.sleep(0.5)
        player.stop()


# sam 실행 함수
def run_sam_in_process(target_age, face_path, result_queue):

    print(f"[SAM] SAM 프로세스 시작. (나이: {target_age}, 이미지: {face_path})")
    # sam.py의 run_sam 함수를 호출
    result_image_path = run_sam(target_age, face_path)
    # 결과를 Queue에 넣어 메인 프로세스에 전달
    result_queue.put(result_image_path)
    print(f"[SAM] SAM 프로세스 완료. 결과: {result_image_path}")


# 외부 호출용 메인 함수
def run_veo3_with_sam(target_age, face_path):

    # 프로세스 간 결과 공유를 위한 Queue 생성
    result_queue = multiprocessing.Queue()

    # 1. veo3 영상 재생 프로세스 생성 및 시작
    video_process = multiprocessing.Process(target=play_veo3_intro)
    video_process.start()

    # 2. SAM 실행 프로세스 생성 및 시작
    sam_process = multiprocessing.Process(
        target=run_sam_in_process,
        args=(target_age, face_path, result_queue)
    )
    sam_process.start()

    # SAM 프로세스가 끝날 때까지 기다림
    sam_process.join()

    # SAM 작업이 끝났으므로 영상 재생 프로세스 종료
    if video_process.is_alive():
        video_process.terminate()
        video_process.join()
        print("[VLC Player] SAM 작업이 완료되어 인트로 영상 재생을 종료합니다.")

    # Queue에서 SAM 실행 결과 가져오기
    face2_path = result_queue.get()
    
    return face2_path




if __name__ == '__main__':
    # Windows, macOS 등에서 spawn 방식을 사용하는 것이 안전합니다.
    multiprocessing.set_start_method('spawn', force=True)

    # --- 테스트용 파라미터 ---
    # 실제로는 이 함수를 호출하기 전에 capture()를 통해 face1_path를 얻어야 합니다.
    face1_path = r"C:\ARTECH5\Image_Box\image1\face_1.jpg" 
    target_age_input = 65
    
    # SAM API 서버가 켜져 있는지 확인하세요.
    print("--- VEO3 인트로 + SAM 동시 실행 테스트 ---")
    
    if not os.path.exists(face1_path):
        print(f"테스트를 위한 원본 이미지 파일이 없습니다: {face1_path}")
    else:
        # 메인 함수 실행
        result_face2_path = run_veo3_with_sam(target_age_input, face1_path)

        if result_face2_path:
            print(f"\n✅ 최종 생성된 이미지 경로: {result_face2_path}")
        else:
            print("\n❌ 이미지 생성에 실패했습니다.")