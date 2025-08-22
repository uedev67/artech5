# 파일명: interactive_player_worker.py

import threading
import subprocess
import argparse
import sys
import os
from button_test import button 

vlc_proc = None

def button_listener(age):
    global vlc_proc
    try:
        result = button(age)
        if vlc_proc and vlc_proc.poll() is None:
            vlc_proc.terminate()
        print(result)
    except Exception as e:
        print(f"Button listener error: {e}", file=sys.stderr)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Play video with VLC and wait for button input.")
    parser.add_argument("--path", type=str, required=True)
    parser.add_argument("--age", type=int, required=True)
    args = parser.parse_args()

    if not os.path.exists(args.path):
        print(f"Video file not found: {args.path}", file=sys.stderr)
        sys.exit(1)

    listener = threading.Thread(target=button_listener, args=(args.age,), daemon=True)
    listener.start()

    try:
        vlc_command = [
            "C:\\Program Files\\VideoLAN\\VLC\\vlc.exe",
            '--fullscreen', '--quiet', '--no-video-title-show',args.path, 'vlc://quit'
        ]
        vlc_proc = subprocess.Popen(vlc_command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        vlc_proc.wait()
    except Exception as e:
        print(f"VLC playback error: {e}", file=sys.stderr)
        sys.exit(1)