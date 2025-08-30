import multiprocessing
import vlc
import time
import os
import sys
import subprocess
from pydub import AudioSegment

# --- Task 1: Veo3 영상 재생 (수정됨) ---
def play_veo3(theme):
    """
    veo3 테마 영상을 한 번만 재생하고 종료되도록 수정합니다.
    """
    theme_video_map = {
        "지하벙커 생존자 커뮤니티": r"C:\Artech5\Image_Box\veo3\지하 세계_1080_60.mp4"  ,
        "사이버펑크": r"C:\Artech5\Image_Box\veo3\사이버펑크 최종_1080.mp4",
        "에코 스마트시티": r"C:\Artech5\Image_Box\veo3\에코스마트시티 1080.mp4",
        "화성 이주": r"C:\Artech5\Image_Box\veo3\화성 이주 최종_1080.mp4",
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
    
    # 영상을 한 번 재생합니다.
    player.play()
    
    # 재생이 시작될 때까지 잠시 대기
    time.sleep(1.5) 
    
    # 영상이 끝날 때까지 대기합니다.
    while player.is_playing():
        time.sleep(0.5)
        
    # 재생 완료 후 플레이어 정리
    player.stop()
    print(f"[VLC Player] '{theme}' 영상 재생이 완료되었습니다.")


def _add_leading_silence(audio_path, duration_ms=1000):
    """
    주어진 오디오 파일 앞에 지정된 시간(ms)만큼의 무음을 추가하고
    임시 파일 경로를 반환합니다.
    """
    try:
        # 오디오 파일 로드
        sound = AudioSegment.from_file(audio_path)
        # 1초(1000ms)짜리 무음 생성
        silence = AudioSegment.silent(duration=duration_ms)
        # 무음 + 원본 오디오
        padded_sound = silence + sound
        
        # 원본 파일명에 '_padded'를 붙여 임시 파일 경로 생성
        file_name, file_extension = os.path.splitext(audio_path)
        temp_padded_path = f"{file_name}_padded{file_extension}"
        
        # 새 파일로 저장
        padded_sound.export(temp_padded_path, format=file_extension.lstrip('.'))
        print(f"[AUDIO_FIX] 원본 오디오에 1초 무음 추가 완료: {temp_padded_path}")
        
        return temp_padded_path
    except Exception as e:
        print(f"❌ [AUDIO_FIX_ERROR] 오디오 파일 처리 중 오류 발생: {e}", file=sys.stderr)
        # 실패 시 원본 경로 그대로 반환
        return audio_path



# --- 메인 함수: 외부 호출용 (수정됨) ---
def veo3_with_sadtalker(theme, first_voice, face2):
    base_path = "C:\\Artech5"
    main_path = os.path.join(base_path, "0.Main")
    sadtalker_result_dir = os.path.join(base_path, "Image_Box", "Image3")
    os.makedirs(sadtalker_result_dir, exist_ok=True)

    # 영상 재생 프로세스 시작
    video_process = multiprocessing.Process(target=play_veo3, args=(theme,))
    print("메인 프로그램: 동영상 재생 프로세스를 시작합니다.")
    video_process.start()

    # [수정] SadTalker에 전달하기 전, 음성 파일에 무음을 추가합니다.
    padded_audio_path = _add_leading_silence(first_voice)

    # SadTalker Worker 스크립트 실행
    worker_script_path = os.path.join(main_path, 'sadtalker_worker.py')
    command = [
        sys.executable,
        worker_script_path,
        '--audio', padded_audio_path,  # 수정된 음성 파일 경로 사용
        '--result_dir', sadtalker_result_dir,
        '--face_path', face2
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
    
    stdout, stderr = sadtalker_proc.communicate()

    # [선택 사항] 작업이 끝난 후 생성된 임시 오디오 파일을 삭제합니다.
    if padded_audio_path != first_voice and os.path.exists(padded_audio_path):
        try:
            os.remove(padded_audio_path)
            print(f"[CLEANUP] 임시 오디오 파일 삭제 완료: {padded_audio_path}")
        except Exception as e:
            print(f"❌ [CLEANUP_ERROR] 임시 오디오 파일 삭제 실패: {e}", file=sys.stderr)

    if stderr:
        print(f"[WORKER_ERROR]\n{stderr.strip()}")

    talking_video = stdout.strip().splitlines()[-1] if stdout.strip() else None

    if talking_video and os.path.exists(talking_video):
        print(f"메인 프로그램: Worker로부터 결과물 경로 수신 성공: {talking_video}")
    else:
        print("메인 프로그램: Worker로부터 유효한 결과물을 받지 못했습니다.")
        talking_video = None

    if video_process.is_alive():
        print("메인 프로그램: SadTalker 작업 완료. veo3 영상이 끝날 때까지 대기합니다.")
        video_process.join()
        print("메인 프로그램: veo3 영상 재생이 정상적으로 종료되었습니다.")

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
    face2_path = r"C:\Artech5\Image_Box\Image2\image_age_60.jpg"

    generated_video_path = veo3_with_sadtalker(video_theme, voice_path, face2_path)

    if generated_video_path:
        print(f"\n✅ 최종 생성된 영상 경로: {generated_video_path}")
    else:
        print("\n❌ 영상 생성에 실패했습니다.")