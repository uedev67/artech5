# remove_audio.py (수정된 버전)

import os
import subprocess
import time
import multiprocessing
from typing import Optional, Tuple, Any

# 서드파티 라이브러리는 함수 내부에서 import 합니다.
# import vlc  <- 이 줄을 주석 처리하거나 삭제
# import whisper <- 이 줄을 주석 처리하거나 삭제






# whisper 모델을 로드하는 함수
def whisper_loader_process(queue, model_name):
    """자식 프로세스에서 Whisper 모델을 로드하고 결과를 큐에 넣는 함수"""
    import stt_listen
    model = stt_listen.load_model(model_name)
    print(f"[WHISPER] 모델 로드 완료: {model_name}")
    queue.put(model)


# sadtalker 영상 재생 함수
def play_video_vlc(video_path: str, fullscreen: bool = True): # 반환 타입에서 vlc.MediaPlayer 제거
    """VLC를 사용하여 비디오를 재생합니다."""
    import vlc  # 함수 내부에서 import
    if not os.path.isfile(video_path):
        raise FileNotFoundError(f"입력 파일을 찾을 수 없습니다: {video_path}")

    instance = vlc.Instance("--no-xlib --quiet")
    player = instance.media_player_new()
    media = instance.media_new(video_path)
    player.set_media(media)

    if fullscreen:
        player.set_fullscreen(True)

    print(f"[VLC Player] 영상 재생 시작: {video_path}")
    player.play()
    time.sleep(1)
    return player




# sadtalker 영상에서 소리만 제거하는 함수
def remove_audio_ffmpeg(video_path: str, output_path: Optional[str] = None, ffmpeg_bin: str = "ffmpeg") -> subprocess.Popen:
    """ffmpeg를 사용하여 비디오에서 오디오를 제거하는 서브프로세스를 시작합니다."""
    if not os.path.isfile(video_path):
        raise FileNotFoundError(f"입력 파일을 찾을 수 없습니다: {video_path}")

    base, ext = os.path.splitext(video_path)
    if not output_path:
        output_path = f"{base}_no_audio{ext if ext else '.mp4'}"

    cmd = [
        ffmpeg_bin, "-hide_banner", "-y",
        "-i", video_path,
        "-map", "0", "-map", "-0:a",
        "-c", "copy",
        output_path
    ]
    print(f"[FFmpeg] 오디오 제거 완료 : {output_path}")
    return subprocess.Popen(cmd)



# 메인 호출 함수
def play_and_process_concurrently(talking_video: str,
                                  ffmpeg_bin: str = "ffmpeg",
                                  fullscreen: bool = True) -> Tuple[str, any]: # whisper.Whisper 타입을 any로 변경
    """멀티프로세싱으로 영상 재생(VLC), 오디오 제거, Whisper 모델 로드를 동시에 수행합니다."""
    base, ext = os.path.splitext(talking_video)
    output_path = f"{base}_no_audio{ext if ext else '.mp4'}"

    model_queue = multiprocessing.Queue()

    # 'load_whisper_model_process' 함수 대신 lambda를 사용하여 직접 처리
    p_whisper = multiprocessing.Process(
        target=whisper_loader_process,
        args=(model_queue, "medium"),
        daemon=True
    )
    p_whisper.start()

    vlc_player = play_video_vlc(talking_video, fullscreen=fullscreen)
    p_strip = remove_audio_ffmpeg(talking_video, output_path=output_path, ffmpeg_bin=ffmpeg_bin)

    while vlc_player.is_playing():
        time.sleep(0.5)
    print("[VLC Player] 영상 재생 완료.")
    
    vlc_player.stop()  # 플레이어 정지
    vlc_player.release() # 플레이어 리소스 해제 (창이 닫힘)

    # 1. 큐에서 데이터를 먼저 꺼내서 Whisper 프로세스의 대기를 풀어줍니다.
    whisper_model = model_queue.get()

    # 2. 이제 나머지 프로세스들이 끝날 때까지 안전하게 기다립니다.
    strip_rc = p_strip.wait()
    p_whisper.join()

    if strip_rc != 0:
        raise RuntimeError(f"무음 변환 실패 (ffmpeg 종료 코드 {strip_rc})")

    return output_path, whisper_model


# 테스트 
if __name__ == "__main__":
    multiprocessing.freeze_support()

    talking_video = "sample_4sec_with_audio.mp4"

    if not os.path.exists(talking_video):
        print(f"오류: '{talking_video}' 파일을 찾을 수 없습니다. 경로를 확인해주세요.")
    else:
        output_path, model = play_and_process_concurrently(
            talking_video,
            ffmpeg_bin="ffmpeg",
            fullscreen=True
        )
        print(f"\n무음 동영상 저장 경로: {output_path}")
        print(f"로드된 Whisper 모델: {model}")