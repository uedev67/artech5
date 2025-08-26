# artech_test2.py (수정된 버전)

import multiprocessing
import subprocess
import sys
import os
import time
import serial
import threading # threading 모듈 추가
from multiprocessing import Process, Queue

# --- 필요한 모듈 Import ---
from survey_client import run_survey_server
from capture import capture
from veo3_sam import run_veo3_with_sam
from veo3_sadtalker import veo3_with_sadtalker
from get_first_voice import get_first_voice
from get_subtitle import get_subtitle
from stt_listen import mic_listen
from get_answer import get_answer
from ai_reply import AI_reply
# 수정된 button_test 모듈을 import 합니다.
from button_test import button


def opening_with_button(survey_age, ser, video_path=r"C:\Artech5\Image_Box\loading.mp4"):
    """
    영상 재생과 버튼 입력을 이 함수 내에서 직접 처리하며,
    열려있는 'ser' 객체를 인자로 받습니다.
    """
    print("[SERVER] 오프닝 시퀀스를 시작합니다. (내장 워커 실행)")

    vlc_proc = None
    result_container = [survey_age]

    def button_listener():
        nonlocal vlc_proc
        try:
            target_age = button(survey_age, ser=ser)
            result_container[0] = target_age
            if vlc_proc and vlc_proc.poll() is None:
                vlc_proc.terminate()
        except Exception as e:
            print(f"Button listener error: {e}", file=sys.stderr)

    listener = threading.Thread(target=button_listener, daemon=True)
    listener.start()

    try:
        vlc_command = [
            "C:\\Program Files\\VideoLAN\\VLC\\vlc.exe",
            '--fullscreen', '--quiet', '--no-video-title-show', video_path, 'vlc://quit'
        ]
        vlc_proc = subprocess.Popen(vlc_command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        vlc_proc.wait()
    except FileNotFoundError:
        print(f"VLC를 찾을 수 없습니다. 경로를 확인하세요: C:\\Program Files\\VideoLAN\\VLC\\vlc.exe", file=sys.stderr)
    except Exception as e:
        print(f"VLC playback error: {e}", file=sys.stderr)

    final_target_age = result_container[0]
    if final_target_age != survey_age:
        print(f"[SERVER] 버튼 입력을 통해 새로운 나이대를 받았습니다: {final_target_age}")
    else:
        print(f"[SERVER] 버튼 입력 없이 영상이 종료되었습니다.")

    return final_target_age


def video_playback_worker(video_path, result_queue):
    from multi3 import play_and_strip_audio
    try:
        output_path = play_and_strip_audio(video_path)
        result_queue.put(output_path)
    except Exception as e:
        result_queue.put(e)


def ending_with_button(ser, video_path=r"C:\Artech5\Image_Box\Emergency.mp4"):
    """
    [수정] 엔딩 영상을 재생하면서 동시에 아두이노의 종료 신호를 기다립니다.
    """
    print("[SERVER] 엔딩 시퀀스를 시작합니다.")
    vlc_proc = None
    is_end_signal_received = False

    def end_listener():
        nonlocal vlc_proc, is_end_signal_received
        try:
            print("[SERVER] 아두이노로 엔딩 시작 신호(30) 전송")
            ser.write(b'30\n')

            timeout_seconds = 30
            deadline = time.time() + timeout_seconds
            
            print(f"[SERVER] 아두이노 종료 신호(100) 대기 중... (최대 {timeout_seconds}초)")
            while time.time() < deadline:
                if ser.in_waiting > 0:
                    line = ser.readline().decode('utf-8').strip()
                    if line == "100":
                        print("[SERVER] 아두이노로부터 종료 신호(100) 수신 완료.")
                        is_end_signal_received = True
                        if vlc_proc and vlc_proc.poll() is None:
                            vlc_proc.terminate()
                        break
            
            if not is_end_signal_received:
                print("❌ [SERVER] 아두이노 종료 신호(100) 대기 시간 초과.")

        except Exception as e:
            print(f"❌ [SERVER] 엔딩 리스너 중 에러 발생: {e}", file=sys.stderr)

    listener = threading.Thread(target=end_listener, daemon=True)
    listener.start()

    try:
        vlc_command = [
            "C:\\Program Files\\VideoLAN\\VLC\\vlc.exe",
            '--fullscreen', '--quiet', '--no-video-title-show', video_path, 'vlc://quit'
        ]
        vlc_proc = subprocess.Popen(vlc_command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        vlc_proc.wait()
    except FileNotFoundError:
        print(f"VLC를 찾을 수 없습니다. 경로를 확인하세요: C:\\Program Files\\VideoLAN\\VLC\\vlc.exe", file=sys.stderr)
    except Exception as e:
        print(f"VLC playback error: {e}", file=sys.stderr)
    
    listener.join(timeout=1.0)

    # [수정] 신호 수신 여부와 관계없이, 시퀀스가 끝났음을 알리기 위해 항상 True를 반환합니다.
    print("[SERVER] 엔딩 시퀀스 완료.")
    return True

def run_sequence_1():
    """
    시퀀스 1: 설문, 아두이노 초기화, 버튼 입력을 처리합니다.
    이 함수 내에서 시리얼 포트를 열고 닫습니다.
    """
    ser = None
    port = 'COM3'
    baudrate = 9600
    try:
        ser = serial.Serial(port, baudrate, timeout=10)
        time.sleep(2)
        print(f"[ARDUINO] 시퀀스 1: 시리얼 포트 {port}를 열었습니다.")

        survey_result = run_survey_server()   
        print(f"[SERVER] 설문 결과: {survey_result}")
        
        survey_age = survey_result.get("age")
        if isinstance(survey_age, str) and survey_age.endswith("대"):
            try:
                survey_age = int(int(survey_age.replace("대", "")) / 10)
            except Exception:
                survey_age = 2
        
        print("[SERVER] 아두이노로 시작 신호(1000) 전송")
        ser.write(b'1000\n')

        print("[SERVER] 아두이노 준비 완료 신호('start') 대기 중...")
        is_arduino_ready = False
        while True:
            line = ser.readline().decode('utf-8').strip()
            if line == "start":
                print("[SERVER] 'start' 신호 수신 완료.")
                is_arduino_ready = True
                break
            elif not line:
                print("❌ [ARDUINO] 'start' 신호 대기 시간 초과.")
                break
        
        if not is_arduino_ready:
            return None

        print("버튼을 눌러주세요")
        target_age = opening_with_button(survey_age, ser) 
        target_age = target_age * 10 
        print(f"[SERVER] 버튼으로 받은 target_age: {target_age}")

        return {
            "target_age": target_age,
            "gender": survey_result.get("gender"),
            "theme": survey_result.get("theme")
        }
    except serial.SerialException as e:
        print(f"❌ [ARDUINO] 에러: 포트 {port}를 열 수 없습니다. {e}")
        return None
    finally:
        if ser and ser.is_open:
            ser.close()
            print("[ARDUINO] 시퀀스 1: 시리얼 포트를 닫았습니다.")


def run_artech5():
    multiprocessing.freeze_support()
    multiprocessing.set_start_method('spawn', force=True)
    
    sequence_1_result = run_sequence_1()
    if not sequence_1_result:
        print("❌ [SERVER] 시퀀스 1 실행에 실패하여 전체 프로그램을 종료합니다.")
        return

    face1 = capture()
    if not face1:
        print("❌ [SERVER] 얼굴 캡처에 실패하여 시퀀스를 중단합니다.")
        return

    ser = None
    port = 'COM3'
    baudrate = 9600
    try:
        ser = serial.Serial(port, baudrate, timeout=10)
        time.sleep(2)
        print(f"[ARDUINO] 시퀀스 2: 시리얼 포트 {port}를 다시 열었습니다.")

        print("[SERVER] 아두이노로 시퀀스 2 시작 신호(2000) 전송")
        ser.write(b'2000\n')
        
        print("[SERVER] 아두이노로 추가 신호(20) 전송")
        ser.write(b'20\n')

        target_age = sequence_1_result["target_age"]
        gender = sequence_1_result["gender"]
        theme = sequence_1_result["theme"]
        
        first_voice, speaker = get_first_voice(target_age, gender, theme)
        print(f"[SERVER] 첫 번째 음성 파일: {first_voice}")

        face2 = run_veo3_with_sam(target_age=target_age, face_path=face1)
        talking_video = veo3_with_sadtalker(theme=theme, first_voice=first_voice, face2=face2)  
        
        result_queue = Queue()
        video_process = Process(target=video_playback_worker, args=(talking_video, result_queue))
        video_process.start()
        result = result_queue.get() 
        video_process.join()

        if isinstance(result, Exception):
            raise result
        else:
            talking_no_voice = result
        
        subtitle_text = get_subtitle(theme)
        user_input = mic_listen(
            loading_video=r"C:\Artech5\Image_Box\MIC_Loading.mp4",
            ready_video=r"C:\Artech5\Image_Box\mic_listening.mp4",
            duration=10, subtitle_text=subtitle_text
        )

        voice = get_answer(user_input, theme, target_age, gender, speaker)
        IsReplySuccess = AI_reply(talking_no_voice, voice)
        
        if IsReplySuccess:
            user_input = mic_listen(
                loading_video=r"C:\Artech5\Image_Box\MIC_Loading.mp4",
                ready_video=r"C:\Artech5\Image_Box\mic_listening.mp4",
                duration=10, subtitle_text=None
            )
            voice = get_answer(user_input, theme, target_age, gender, speaker)

        AI_reply(talking_no_voice, voice)  
        IsEnd = ending_with_button(ser)
        
        if IsEnd:
            print("콘텐츠 종료")
        
        return IsEnd

    except serial.SerialException as e:
        print(f"❌ [ARDUINO] 시퀀스 2 에러: 포트 {port}를 열 수 없습니다. {e}")
    except Exception as e:
        print(f"❌ [SERVER] 시퀀스 2 실행 중 에러 발생: {e}")
    finally:
        if ser and ser.is_open:
            ser.close()
            print("[ARDUINO] 시퀀스 2: 시리얼 포트를 닫았습니다.")

if __name__ == "__main__":
    run_artech5()
