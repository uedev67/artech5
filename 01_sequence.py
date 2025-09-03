# artech_test2.py (수정된 버전)

import multiprocessing
import subprocess
import sys
import os
import time
import serial
import threading # threading 모듈 추가
from multiprocessing import Process, Queue
import vlc

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
from black_screen_manager import run_black_screen_process


def send_int(ser, n: int):
    """주어진 정수를 아두이노로 전송합니다."""
    try:
        ser.write(f"{n}\n".encode())
        ser.flush()
        print(f"[ARDUINO] 데이터 전송: {n}")
    except serial.SerialException as e:
        print(f"❌ [ERROR] 데이터 전송 실패: {e}", file=sys.stderr)


def recv_int(ser, timeout_s=30):
    """아두이노로부터 정수를 수신합니다. timeout 시간 동안 대기합니다."""
    deadline = time.time() + timeout_s
    buf = b""
    while time.time() < deadline:
        try:
            if ser.in_waiting:
                buf += ser.read(ser.in_waiting)
                if b"\n" in buf:
                    line, _, buf = buf.partition(b"\n")
                    s = line.decode(errors="ignore").strip()
                    try:
                        val = int(s)
                        print(f"[ARDUINO] 데이터 수신: {val}")
                        return val
                    except ValueError:
                        # 파싱할 수 없는 데이터는 무시
                        buf = b""
            else:
                time.sleep(0.01)
        except serial.SerialException as e:
            print(f"❌ [ERROR] 데이터 수신 중 예외 발생: {e}", file=sys.stderr)
            # 장치가 잠시 끊겼을 수 있으므로 잠시 대기 후 재시도
            time.sleep(0.1)
    
    print(f" [ARDUINO] {timeout_s}초 내에 데이터를 수신하지 못했습니다 (Timeout).", file=sys.stderr)
    return None


def opening_with_button(survey_age, ser, video_path=r"C:\Artech5\Image_Box\opening.mp4"):

    print("[SERVER] 오프닝 시퀀스를 시작합니다.")

    vlc_proc = None
    # 결과를 담을 컨테이너 (스레드 간 공유를 위해 리스트 사용)
    result_container = [survey_age] 

    def arduino_communication_worker():
        """
        백그라운드 스레드에서 아두이노 통신을 담당하는 워커 함수.
        1. survey_age를 아두이노로 전송
        2. 버튼 입력을 대기
        """
        nonlocal vlc_proc
        
        print("[WORKER] 아두이노 통신 스레드 시작.")
        
        # 1. 아두이노로 설문 결과(나이대) 전송
        send_int(ser, survey_age)
        
        # 2. 아두이노로부터 버튼 입력 값 수신 대기 (영상 길이만큼 또는 충분히 길게)
        #    영상 재생 시간보다 길게 설정하여 사용자가 충분히 누를 시간을 줍니다.
        target_age = recv_int(ser, timeout_s=60) 
        
        # 3. 결과 처리
        if target_age is not None:
            # 새로운 버튼 값이 들어온 경우
            result_container[0] = target_age
            print(f"[WORKER] 버튼 입력 감지! 새로운 나이대: {target_age}")
            # 버튼이 눌리면 즉시 영상 종료
            if vlc_proc and vlc_proc.poll() is None:
                print("[WORKER] 버튼 입력으로 영상 재생을 중단합니다.")
                vlc_proc.terminate()
        else:
            # 타임아웃된 경우 (버튼 입력이 없는 경우)
            print("[WORKER] 버튼 입력 없이 타임아웃되었습니다.")
            
    # 아두이노 통신을 위한 백그라운드 스레드 생성 및 시작
    listener_thread = threading.Thread(target=arduino_communication_worker, daemon=True)
    listener_thread.start()

    # 메인 스레드에서는 영상 재생
    try:
        print("[VLC] 영상 재생을 시작합니다.")
        vlc_command = [
            "C:\\Program Files\\VideoLAN\\VLC\\vlc.exe",
            '--fullscreen', '--quiet', '--no-video-title-show', video_path, 'vlc://quit'
        ]
        vlc_proc = subprocess.Popen(vlc_command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        vlc_proc.wait() # 영상이 끝나거나, 스레드에서 terminate() 될 때까지 대기
        print("[VLC] 영상 재생이 종료되었습니다.")

    except FileNotFoundError:
        print("❌ [ERROR] VLC를 찾을 수 없습니다. 경로를 확인하세요: C:\\Program Files\\VideoLAN\\VLC\\vlc.exe", file=sys.stderr)
    except Exception as e:
        print(f"❌ [ERROR] VLC 재생 중 오류 발생: {e}", file=sys.stderr)

    # 스레드가 아직 실행 중일 수 있으므로 잠시 대기 후 최종 결과 반환
    listener_thread.join(timeout=0.5) 
    
    final_target_age = result_container[0]
    if final_target_age != survey_age:
        print(f"✅ [SERVER] 최종 나이대가 '{final_target_age}'로 변경되었습니다.")
    else:
        print(f"✅ [SERVER] 최종 나이대가 초기값 '{survey_age}'로 유지되었습니다.")

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
        ser = serial.Serial(port, baudrate, timeout=30)
        time.sleep(2)
        print(f"[ARDUINO] 시퀀스 1: 시리얼 포트 {port}를 열었습니다.")

        survey_result = run_survey_server()   
        print(f"[SERVER] 설문 결과: {survey_result}")
        
        survey_age = survey_result.get("age")
        if isinstance(survey_age, str) and survey_age.endswith("대"):
            try:
                survey_age = int(int(survey_age.replace("대", "")) / 10)
            except Exception:
                survey_age = 3
        
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

    # --- 검은 화면 프로세스 시작 ---
    print("[SYSTEM] 검은 화면 프로세스를 시작합니다.")
    black_screen_proc = Process(target=run_black_screen_process, daemon=True)
    black_screen_proc.start()
    # 창이 완전히 뜰 때까지 잠시 대기합니다.
    time.sleep(1)

    try:
        # --- 기존의 시퀀스 로직 ---
        sequence_1_result = run_sequence_1()
        if not sequence_1_result:
            print("❌ [SERVER] 시퀀스 1 실행에 실패하여 전체 프로그램을 종료합니다.")
            return

        # --- 캡처를 위해 검은 화면 종료 ---
        print("[SYSTEM] 캡처를 위해 검은 화면을 일시적으로 종료합니다.")
        if black_screen_proc and black_screen_proc.is_alive():
            black_screen_proc.terminate()
            black_screen_proc.join()
        
        time.sleep(2)
        face1 = capture()
        if not face1:
            print("❌ [SERVER] 얼굴 캡처에 실패하여 시퀀스를 중단합니다.")
            return

        # --- 캡처 후 검은 화면 다시 시작 ---
        print("[SYSTEM] 캡처 완료 후 검은 화면을 다시 시작합니다.")
        black_screen_proc = Process(target=run_black_screen_process, daemon=True)
        black_screen_proc.start()
        time.sleep(1) # 창이 뜰 시간을 줍니다.

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
            
            user_input = mic_listen(
                loading_video=r"C:\Artech5\Image_Box\MIC_Loading.mp4",
                ready_video=r"C:\Artech5\Image_Box\mic_listening.mp4",
                duration=15, subtitle_text="평행세계 연결중... 잠시 기다리면 마이크가 활성화됩니다."
            )

            voice = get_answer(user_input, theme, target_age, gender, speaker)
            IsReplySuccess = AI_reply(talking_no_voice, voice)
            
            if IsReplySuccess:
                subtitle_text = get_subtitle(theme)
                user_input = mic_listen(
                    loading_video=r"C:\Artech5\Image_Box\MIC_Loading.mp4",
                    ready_video=r"C:\Artech5\Image_Box\mic_listening.mp4",
                    duration=15, subtitle_text=subtitle_text
                )
                voice = get_answer(user_input, theme, target_age, gender, speaker)

            AI_reply(talking_no_voice, voice)  
            IsEnd = ending_with_button(ser)
            
            if IsEnd:
                
                video_path = r"C:\Artech5\Image_Box\이용종료.mp4"

                # VLC 인스턴스 생성
                instance = vlc.Instance()

                # 미디어 플레이어 생성
                player = instance.media_player_new()

                # 재생할 미디어 설정
                media = instance.media_new(video_path)

                # 미디어 플레이어에 미디어 할당
                player.set_media(media)

                # 영상 재생
                player.play()

                time.sleep(7) # 7초간 재생 후 종료

                # 재생 중지
                player.stop()
            
            

        except serial.SerialException as e:
            print(f"❌ [ARDUINO] 시퀀스 2 에러: 포트 {port}를 열 수 없습니다. {e}")
        except Exception as e:
            print(f"❌ [SERVER] 시퀀스 2 실행 중 에러 발생: {e}")
        finally:
            if ser and ser.is_open:
                ser.close()
                print("[ARDUINO] 시퀀스 2: 시리얼 포트를 닫았습니다.")
            
    finally:
        # --- 모든 작업 완료 후 검은 화면 프로세스 종료 ---
        print("[SYSTEM] 검은 화면 프로세스를 종료합니다.")
        if 'black_screen_proc' in locals() and black_screen_proc and black_screen_proc.is_alive():
            black_screen_proc.terminate()
            black_screen_proc.join()


if __name__ == "__main__":
    run_artech5()