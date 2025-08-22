# video_processor.py

import os
import subprocess
import time
from typing import Optional
import platform

# Windows 환경에서 창을 제어하기 위해 추가
# pywin32 라이브러리가 필요합니다. (pip install pywin32)
if platform.system() == "Windows":
    try:
        import win32gui
        import win32con
        PYWIN32_AVAILABLE = True
    except ImportError:
        PYWIN32_AVAILABLE = False
        print("경고: pywin32 라이브러리가 설치되지 않았습니다. 창이 맨 앞으로 오지 않을 수 있습니다.")
else:
    PYWIN32_AVAILABLE = False

def play_video_vlc(video_path: str, fullscreen: bool = True):
    """VLC를 사용하여 비디오를 재생하고 플레이어 객체를 반환합니다."""
    import vlc
    if not os.path.isfile(video_path):
        raise FileNotFoundError(f"입력 파일을 찾을 수 없습니다: {video_path}")

    # --- ▼▼▼ 핵심 수정 부분 (v3) ▼▼▼ ---
    # VLC 인스턴스 생성 시 옵션을 조정하여 창 핸들 반환을 더 안정적으로 만듭니다.
    instance = vlc.Instance("--quiet")
    # --- ▲▲▲ 핵심 수정 부분 (v3) ▲▲▲ ---
    
    player = instance.media_player_new()
    media = instance.media_new(video_path)
    player.set_media(media)
    if fullscreen:
        player.set_fullscreen(True)
    
    print(f"[VLC] 영상 재생 시작: {video_path}")
    player.play()
    

    if platform.system() == "Windows" and PYWIN32_AVAILABLE:
        hwnd = None
        # 창 핸들을 얻을 때까지 최대 5초간 0.1초 간격으로 반복 시도합니다.
        for _ in range(50):
            hwnd = player.get_hwnd()
            if hwnd:  # hwnd가 None이나 0이 아니면 유효한 것으로 간주
                break
            time.sleep(0.1)

        # 핸들을 성공적으로 찾았을 경우에만 창 제어 코드를 실행합니다. (오류 방지)
        if hwnd:
            print(f"VLC 창 핸들(HWND)을 찾았습니다: {hwnd}")
            try:
                win32gui.SetForegroundWindow(hwnd)
                win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
            except Exception as e:
                print(f"pywin32로 창을 제어하는 중 오류 발생: {e}")
        else:
            print("경고: VLC 창 핸들을 시간 내에 가져오지 못했습니다. (타임아웃)")

    return player

def remove_audio_ffmpeg(video_path: str, output_path: Optional[str] = None) -> subprocess.Popen:
    """ffmpeg를 사용하여 비디오에서 오디오를 제거하는 서브프로세스를 시작합니다."""
    if not output_path:
        base, ext = os.path.splitext(video_path)
        output_path = f"{base}_no_audio{ext or '.mp4'}"

    cmd = [
        "ffmpeg", "-hide_banner", "-y",
        "-i", video_path,
        "-c:v", "copy", "-an",
        output_path
    ]
    print(f"[FFmpeg] 오디오 제거 시작: {output_path}")
    return subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def play_and_strip_audio(video_path: str) -> str:
    """
    영상 재생과 오디오 제거를 동시에 수행합니다.
    완료되면 오디오가 제거된 파일의 경로를 반환합니다.
    """
    print("--- 1단계: 영상 재생 및 오디오 제거 시작 ---")
    output_path = f"{os.path.splitext(video_path)[0]}_no_audio.mp4"

    p_strip = remove_audio_ffmpeg(video_path, output_path)
    vlc_player = play_video_vlc(video_path)

    while vlc_player.is_playing():
        time.sleep(0.5)
    print("[VLC] 영상 재생 완료.")
    
    vlc_player.stop()
    vlc_player.release()

    # FFmpeg 프로세스가 끝나기를 대기하고, 출력을 가져옵니다.
    stdout, stderr = p_strip.communicate()
    if p_strip.returncode != 0:
        print("--- FFmpeg 오류 출력 ---")
        print(stderr.decode('utf-8', errors='ignore'))
        print("-----------------------")
        raise RuntimeError(f"FFmpeg 오디오 제거 실패 (종료 코드 {p_strip.returncode})")
    
    print(f"[FFmpeg] 오디오 제거 완료: {output_path}")
    print("--- 1단계 완료 ---\n")
    return output_path