
import multiprocessing
import subprocess
import sys
import os
import time
import serial
import threading
from multiprocessing import Process, Queue 

# 다른 파이썬 파일들도 main_process.py 와 같은 폴더에 넣어주세요! 
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from survey_client import run_survey_server
from veo3_sam import run_veo3_with_sam
from veo3_sadtalker import veo3_with_sadtalker
from get_first_voice import get_first_voice
from get_subtitle import get_subtitle
from stt_listen import mic_listen
from get_answer import get_answer
from ai_reply import AI_reply
from black_screen_simple import run_black_screen_simple


def send_int(ser, n: int):
    """주어진 정수를 아두이노로 전송합니다."""
    try:
        ser.write(f"{n}\n".encode())
        ser.flush()
        print(f"[ARDUINO] 데이터 전송: {n}")
    except serial.SerialException as e:
        print(f"❌ [ERROR] 데이터 전송 실패: {e}", file=sys.stderr)


def recv_int(ser, timeout_s=30):
    """아두이노로부터 정수를 수신합니다. timeout_s가 None이면 무한정 대기합니다."""
    deadline = None
    if timeout_s is not None:
        deadline = time.time() + timeout_s
    
    buf = b""
    while True:
        # 1. 타임아웃 처리
        if deadline is not None and time.time() > deadline:
            break
        
        # 2. 데이터 수신 처리
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
                        buf = b""  # 손상된 데이터는 무시하고 버퍼 비움
            else:
                time.sleep(0.01)
        except serial.SerialException as e:
            print(f"❌ [ERROR] 데이터 수신 중 예외 발생: {e}", file=sys.stderr)
            time.sleep(0.1) # 잠시 대기 후 재시도
    
    print(f" [ARDUINO] {timeout_s}초 내에 데이터를 수신하지 못했습니다 (Timeout).", file=sys.stderr)
    return None


def opening_with_button(survey_age, ser, video_path=r"C:\Artech5\Image_Box\opening.mp4"):
    """
    아두이노로부터 버튼 입력을 받을 때까지 지정된 비디오를 반복 재생합니다.
    버튼이 입력되면 비디오 재생을 즉시 중단하고 변경된 나이대를 반환합니다.
    """
    print("[SERVER] 오프닝 시퀀스를 시작합니다.")
    vlc_proc = None
    result_container = [survey_age] 
    
    # 메인 스레드와 워커 스레드 간의 신호를 위한 Event 객체 생성
    button_pressed_event = threading.Event()

    def arduino_communication_worker():
        nonlocal vlc_proc
        print("[WORKER] 아두이노 통신 스레드 시작.")
        send_int(ser, survey_age)
        
        # 버튼 입력이 있을 때까지 무한정 대기
        target_age = recv_int(ser, timeout_s=None) 
        
        if target_age is not None:
            result_container[0] = target_age
            print(f"[WORKER] 버튼 입력 감지! 새로운 나이대: {target_age}")
        else:
            print("[WORKER] 데이터 수신에 실패하여 초기값을 유지합니다.")
        
        # 메인 스레드에 버튼이 눌렸음을 알림 (영상 반복 중단용)
        button_pressed_event.set()
        
        # 현재 VLC가 실행 중이면 즉시 종료
        if vlc_proc and vlc_proc.poll() is None:
            print("[WORKER] 버튼 입력으로 영상 재생을 중단합니다.")
            vlc_proc.terminate()
            
    listener_thread = threading.Thread(target=arduino_communication_worker, daemon=True)
    listener_thread.start()

    # 버튼 입력 신호가 올 때까지 영상 재생을 반복
    while not button_pressed_event.is_set():
        try:
            print("[VLC] 영상 재생을 시작합니다. (루프)")
            vlc_command = ["C:\\Program Files\\VideoLAN\\VLC\\vlc.exe", '--fullscreen', '--quiet', '--no-video-title-show', video_path, 'vlc://quit']
            vlc_proc = subprocess.Popen(vlc_command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            # 영상이 끝나거나, 워커 스레드에 의해 강제 종료될 때까지 대기
            vlc_proc.wait()
            
            if button_pressed_event.is_set():
                print("[VLC] 버튼 입력 신호를 받아 영상 루프를 종료합니다.")
                break
            else:
                print("[VLC] 영상이 자연스럽게 종료되었습니다. 다시 재생합니다.")

        except FileNotFoundError:
            print("❌ [ERROR] VLC를 찾을 수 없습니다. 경로를 확인하세요: C:\\Program Files\\VideoLAN\\VLC\\vlc.exe", file=sys.stderr)
            button_pressed_event.set() # 오류 발생 시 루프 중단
            break
        except Exception as e:
            print(f"❌ [ERROR] VLC 재생 중 오류 발생: {e}", file=sys.stderr)
            button_pressed_event.set() # 오류 발생 시 루프 중단
            break

    listener_thread.join(timeout=0.5) 
    final_target_age = result_container[0]
    if final_target_age != survey_age:
        print(f"✅ [SERVER] 최종 나이대가 '{final_target_age}'(으)로 변경되었습니다.")
    else:
        print(f"✅ [SERVER] 최종 나이대가 초기값 '{survey_age}'(으)로 유지되었습니다.")
    return final_target_age


def video_playback_worker(video_path, result_queue):
    # ... (기존 코드와 동일, 변경 없음)
    from multi3 import play_and_strip_audio
    try:
        output_path = play_and_strip_audio(video_path)
        result_queue.put(output_path)
    except Exception as e:
        result_queue.put(e)
    

def ending_with_button(ser, video_path=r"C:\Artech5\Image_Box\Emergency.mp4"):
    # ... (기존 코드와 동일, 변경 없음)
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
        vlc_command = ["C:\\Program Files\\VideoLAN\\VLC\\vlc.exe", '--fullscreen', '--quiet', '--no-video-title-show', video_path, 'vlc://quit']
        vlc_proc = subprocess.Popen(vlc_command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        vlc_proc.wait()
    except FileNotFoundError:
        print(f"VLC를 찾을 수 없습니다. 경로를 확인하세요: C:\\Program Files\\VideoLAN\\VLC\\vlc.exe", file=sys.stderr)
    except Exception as e:
        print(f"VLC playback error: {e}", file=sys.stderr)
    
    listener.join(timeout=1.0)
    print("[SERVER] 엔딩 시퀀스 완료.")
    return True


# --- [수정] command_queue 파라미터 제거 ---
def run_sequence_1():
    ser = None
    port = 'COM3'
    baudrate = 9600
    try:
        ser = serial.Serial(port, baudrate, timeout=40)
        time.sleep(2)
        print(f"[ARDUINO] 시퀀스 1: 시리얼 포트 {port}를 열었습니다.")

        survey_result = run_survey_server()   
        print(f"[SERVER] 설문 결과: {survey_result}")
        
        survey_age = survey_result.get("age")
        survey_name = survey_result.get("name")
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
        
        # --- [삭제] command_queue 관련 코드 제거 ---
        target_age = opening_with_button(survey_age, ser) 

        target_age = target_age * 10 
        print(f"[SERVER] 버튼으로 받은 target_age: {target_age}")

        return {"target_age": target_age, "gender": survey_result.get("gender"), "theme": survey_result.get("theme"), "name": survey_result.get("name")}
    except serial.SerialException as e:
        print(f"❌ [ARDUINO] 에러: 포트 {port}를 열 수 없습니다. {e}")
        return None
    finally:
        if ser and ser.is_open:
            ser.close()
            print("[ARDUINO] 시퀀스 1: 시리얼 포트를 닫았습니다.")


# --- [핵심 수정] 함수 구조 변경 ---
def run_artech5():
    multiprocessing.freeze_support()
    multiprocessing.set_start_method('spawn', force=True)

    active_processes = []

    try:
        # --- [수정] 프로그램 시작과 함께 블랙스크린 실행 ---
        print("[SYSTEM] 단순 블랙스크린을 시작합니다.")
        black_screen_simple_proc = Process(target=run_black_screen_simple, daemon=True)
        black_screen_simple_proc.start()
        active_processes.append(black_screen_simple_proc)
        time.sleep(0.5)

        # --- 1단계: 사용자 정보 및 얼굴 캡처 ---
        sequence_1_result = run_sequence_1()
        if not sequence_1_result:
            print("❌ [SERVER] 시퀀스 1 실행에 실패하여 전체 프로그램을 종료합니다.")
            return

        face1 = r"C:\ARTECH5\Image_Box\image1\face_1.jpg"
        if not face1:
            print("❌ [SERVER] 얼굴 캡처에 실패하여 시퀀스를 중단합니다.")
            return
        
        # --- 2단계: 블랙스크린을 배경으로 AI 시퀀스 진행 ---
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
            name = sequence_1_result["name"]
            
            first_voice, speaker = get_first_voice(target_age, gender, theme)
            print(f"[SERVER] 첫 번째 음성 파일: {first_voice}")

            face2 = run_veo3_with_sam(target_age=target_age, face_path=face1)
            talking_video = veo3_with_sadtalker(theme=theme, first_voice=first_voice, face2=face2)  
            
            result_queue = Queue()
            video_process = Process(target=video_playback_worker, args=(talking_video, result_queue))
            video_process.start()
            active_processes.append(video_process)
            result = result_queue.get() 
            video_process.join()
            active_processes.remove(video_process)

            if isinstance(result, Exception): raise result
            else: talking_no_voice = result
            
            user_input = mic_listen(
                loading_video=r"C:\Artech5\Image_Box\MIC_Loading.mp4",
                ready_video=r"C:\Artech5\Image_Box\mic_listening.mp4",
                duration=15, subtitle_text="평행세계 연결중... 잠시 기다리면 마이크가 활성화됩니다."
            )

            voice = get_answer(user_input, theme, target_age, gender, speaker,name)
            IsReplySuccess = AI_reply(talking_no_voice, voice)
            
            if IsReplySuccess:
                subtitle_text = get_subtitle(theme)
                user_input = mic_listen(
                    loading_video=r"C:\Artech5\Image_Box\MIC_Loading.mp4",
                    ready_video=r"C:\Artech5\Image_Box\mic_listening.mp4",
                    duration=15, subtitle_text=subtitle_text
                )
                voice = get_answer(user_input, theme, target_age, gender, speaker,name)

            AI_reply(talking_no_voice, voice)  
            IsEnd = ending_with_button(ser)
            
            if IsEnd:
                import vlc # vlc 모듈을 사용할 때 import
                video_path = r"C:\Artech5\Image_Box\이용종료.mp4"
                instance = vlc.Instance()
                player = instance.media_player_new()
                media = instance.media_new(video_path)
                player.set_media(media)
                player.set_fullscreen(True)
                player.play()
                time.sleep(7)
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
        # --- 프로그램 종료 시 살아있는 모든 자식 프로세스 강제 종료 ---
        print("[SYSTEM] 프로그램 종료. 모든 자식 프로세스를 정리합니다...")
        for proc in active_processes:
            if proc.is_alive():
                print(f"[SYSTEM] 프로세스 {proc.pid}를 강제 종료합니다.")
                proc.terminate()
                proc.join(timeout=1) # 종료될 때까지 최대 1초 대기
        print("[SYSTEM] 모든 프로세스 정리 완료.")


if __name__ == "__main__":
    run_artech5()



