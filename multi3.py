# video_processor.py

import os
import subprocess
import time
import multiprocessing
from typing import Optional

def play_video_vlc(video_path: str, fullscreen: bool = True):
    """VLC를 사용하여 비디오를 재생하고 플레이어 객체를 반환합니다."""
    import vlc
    if not os.path.isfile(video_path):
        raise FileNotFoundError(f"입력 파일을 찾을 수 없습니다: {video_path}")

    instance = vlc.Instance("--no-xlib --quiet")
    player = instance.media_player_new()
    media = instance.media_new(video_path)
    player.set_media(media)
    if fullscreen:
        player.set_fullscreen(True)
    
    print(f"[VLC] 영상 재생 시작: {video_path}")
    player.play()
    time.sleep(1) # 재생 시작을 위한 짧은 대기
    return player

def remove_audio_ffmpeg(video_path: str, output_path: Optional[str] = None) -> subprocess.Popen:
    """ffmpeg를 사용하여 비디오에서 오디오를 제거하는 서브프로세스를 시작합니다."""
    if not output_path:
        base, ext = os.path.splitext(video_path)
        output_path = f"{base}_no_audio{ext or '.mp4'}"

    cmd = [
        "ffmpeg", "-hide_banner", "-y",
        "-i", video_path,
        "-c:v", "copy", "-an", # -an 플래그가 오디오 없음을 의미
        output_path
    ]
    print(f"[FFmpeg] 오디오 제거 시작: {output_path}")
    return subprocess.Popen(cmd)

def play_and_strip_audio(video_path: str) -> str:
    """
    영상 재생과 오디오 제거를 동시에 수행합니다.
    완료되면 오디오가 제거된 파일의 경로를 반환합니다.
    """
    print("--- 1단계: 영상 재생 및 오디오 제거 시작 ---")
    output_path = f"{os.path.splitext(video_path)[0]}_no_audio.mp4"

    # 1. FFmpeg 오디오 제거 프로세스 시작
    p_strip = remove_audio_ffmpeg(video_path, output_path)
    
    # 2. VLC 영상 재생 시작
    vlc_player = play_video_vlc(video_path)

    # 3. 영상 재생이 끝날 때까지 대기
    while vlc_player.is_playing():
        time.sleep(0.5)
    print("[VLC] 영상 재생 완료.")
    
    # 4. 플레이어 리소스 정리
    vlc_player.stop()
    vlc_player.release()

    # 5. FFmpeg 프로세스가 끝나기를 대기
    strip_rc = p_strip.wait()
    if strip_rc != 0:
        raise RuntimeError(f"FFmpeg 오디오 제거 실패 (종료 코드 {strip_rc})")
    
    print(f"[FFmpeg] 오디오 제거 완료: {output_path}")
    print("--- 1단계 완료 ---\n")
    return output_path