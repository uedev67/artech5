

import threading
import argparse
import sys
import time
import serial
import subprocess
import os

# 동영상 재생 함수 (이전과 동일)
def play_video(video_path):
    vlc_executable = "C:\\Program Files\\VideoLAN\\VLC\\vlc.exe"
    if not os.path.exists(video_path):
        print(f"Video file not found: {video_path}", file=sys.stderr)
        return None
    
    vlc_command = [
        vlc_executable, '--fullscreen', '--quiet', '--no-video-title-show',
        video_path, 'vlc://quit'
    ]
    try:
        proc = subprocess.Popen(vlc_command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return proc
    except FileNotFoundError:
        print(f"VLC executable not found at: {vlc_executable}", file=sys.stderr)
        return None
    except Exception as e:
        print(f"VLC playback error: {e}", file=sys.stderr)
        return None

def arduino_communication_thread(port, video_start_signal, vlc_process_holder):
    """
    아두이노 통신을 전담하는 스레드 함수.
    1. '30'을 보낸다.
    2. 메인 스레드에 동영상 재생 신호를 보낸다.
    3. '40'을 기다리고, 받으면 동영상을 종료한다.
    """
    ser = None
    try:
        # 1. 아두이노 연결 및 '30' 전송
        ser = serial.Serial(port, 9600, timeout=2)
        time.sleep(2)  # 연결 안정화 대기
        ser.write(b"30\n")
        print("Arduino Listener: Sent '30' to Arduino.")

        # 2. 메인 스레드에 동영상 재생 신호 보내기
        video_start_signal.set()
        print("Arduino Listener: Sent signal to start video.")

        # 3. '40' 수신 대기
        print("Arduino Listener: Now waiting for '40' from Arduino...")
        if ser.in_waiting > 0:
            response = ser.readline().decode('utf-8').strip()
            print(f"Arduino Listener: Received '{response}'.")
            
            # '40'을 받으면 동영상 종료
            if response == "40":
                vlc_proc = vlc_process_holder[0]
                if vlc_proc and vlc_proc.poll() is None:
                    print("Arduino Listener: Handshake successful. Terminating video.")
                    vlc_proc.terminate()
                    
    except serial.SerialException as e:
        print(f"Listener Error: Port {port}에 연결할 수 없습니다. {e}", file=sys.stderr)
        # 통신 자체에 실패하면 동영상 재생 신호를 보내지 않음
        if not video_start_signal.is_set():
             video_start_signal.set() # 메인 스레드가 무한정 기다리지 않도록 신호 전송
    except Exception as e:
        print(f"Listener Error: {e}", file=sys.stderr)
    finally:
        if ser and ser.is_open:
            ser.close()
            print("Arduino Listener: Serial connection closed.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Send data to Arduino, then play a video while waiting for response.")
    parser.add_argument("--port", type=str, required=True, help="Arduino serial port (e.g., COM3)")
    args = parser.parse_args()

    video_start_signal = threading.Event() # 스레드 간 신호를 위한 Event 객체
    vlc_process_holder = [None]  # 스레드 간에 VLC 프로세스 객체를 공유하기 위한 리스트

    # 아두이노 통신 스레드 생성 및 시작
    comm_thread = threading.Thread(
        target=arduino_communication_thread, 
        args=(args.port, video_start_signal, vlc_process_holder), 
        daemon=True
    )
    comm_thread.start()

    # 아두이노 스레드로부터 동영상 재생 신호가 올 때까지 대기
    print("Main Thread: Waiting for signal from Arduino thread to start video...")
    video_start_signal.wait() # 신호가 올 때까지 여기서 멈춤

    # 신호를 받으면 동영상 재생 시작
    print("Main Thread: Signal received. Starting video playback...")
    video_file_path = "C:\\Artech5\\Image_Box\\Emergency.mp4"
    vlc_proc = play_video(video_file_path)
    
    # 리스트에 프로세스 객체를 저장하여 다른 스레드가 접근할 수 있도록 함
    if vlc_proc:
        vlc_process_holder[0] = vlc_proc

        # 통신 스레드가 끝나거나, 타임아웃(25초)이 될 때까지 대기
        comm_thread.join(timeout=25)

        if comm_thread.is_alive():
            print("Main Thread: Communication timed out after 25 seconds.", file=sys.stderr)
            if vlc_proc.poll() is None:
                vlc_proc.terminate()
        else:
            print("Main Thread: Communication thread finished.")
            if vlc_proc.poll() is None:
                vlc_proc.wait() # 통신이 먼저 끝나면, 비디오가 끝날 때까지 대기
    else:
        print("Main Thread: Exiting because video playback failed to start.", file=sys.stderr)
