# 파일명: ending_with_button.py (단순 영상 재생기로 수정됨)

import subprocess
import sys
import os

if __name__ == "__main__":
    """
    이 워커 스크립트는 이제 정해진 비상상황 비디오를
    전체 화면으로 재생하고 종료하는 역할만 담당합니다.
    모든 아두이노 통신 로직은 제거되었습니다.
    """
    video_path = r"C:\Artech5\Image_Box\Emergency.mp4"

    if not os.path.exists(video_path):
        print(f"Error: Video file not found at '{video_path}'", file=sys.stderr)
        sys.exit(1)

    try:
        # VLC 미디어 플레이어 실행 명령어
        vlc_command = [
            "C:\\Program Files\\VideoLAN\\VLC\\vlc.exe",
            '--fullscreen',
            '--quiet',
            '--no-video-title-show',
            video_path,
            'vlc://quit'  # 영상 재생이 끝나면 VLC가 자동으로 종료되도록 함
        ]
        
        print(f"[Worker] Playing emergency video: {video_path}")
        # subprocess.run은 해당 프로세스가 끝날 때까지 기다립니다.
        subprocess.run(vlc_command, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print("[Worker] Emergency video playback finished.")
        sys.exit(0) # 정상 종료 코드
        
    except FileNotFoundError:
        print("Error: VLC executable not found. Please check the path.", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"An unexpected error occurred in ending worker: {e}", file=sys.stderr)
        sys.exit(1)