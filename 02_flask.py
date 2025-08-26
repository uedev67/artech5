# artech_test2.py (Flask 서버 통신 방식으로 수정됨)

import multiprocessing
import subprocess
import sys
import os
import time
import requests  # requests 모듈을 추가합니다.
import json      # json 모듈을 추가합니다.
from multiprocessing import Process, Queue, Event

# --- 필요한 모듈 Import ---
# 아래 모듈들은 프로젝트 내에 존재해야 합니다.
from survey_client import run_survey_server
from capture import capture
from veo3_sam import run_veo3_with_sam
from veo3_sadtalker import veo3_with_sadtalker
from get_first_voice import get_first_voice
from get_subtitle import get_subtitle
from stt_listen import mic_listen
from get_answer import get_answer
from ai_reply import AI_reply


def send_to_server(data, host='127.0.0.1', port=5001):
    """
    [헬퍼 함수] Flask 웹 서버로 제어 명령을 전송합니다. (데스크탑 -> 노트북)
    survey_client.py를 참고하여 클라이언트 역할을 수행합니다.
    """
    url = f"http://{host}:{port}/control"  # 제어를 위한 엔드포인트
    payload = {'command': data}
    headers = {'Content-Type': 'application/json'}
    try:
        # 서버에 POST 요청을 보냅니다.
        response = requests.post(url, data=json.dumps(payload), headers=headers, timeout=5)
        
        # 서버로부터 2xx 응답 코드를 받으면 성공으로 간주합니다.
        if 200 <= response.status_code < 300:
            print(f"[SERVER] {url}로 데이터 '{data}' 전송 성공. 응답: {response.text}")
        else:
            print(f"❌ [SERVER] 에러: 서버가 오류를 반환했습니다. 상태 코드: {response.status_code}, 응답: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ [SERVER] 에러: {url}에 연결할 수 없습니다. {e}")


def receive_from_server(host='0.0.0.0', port=5002):
    """
    [헬퍼 함수] 노트북(클라이언트)으로부터 데이터를 수신합니다. (노트북 -> 데스크탑)
    데이터를 한 번 수신하면 결과를 반환하고 서버는 종료됩니다.
    """
    from flask import Flask, request
    from threading import Thread, Event, Timer

    app = Flask(__name__)
    result_holder = {'data': None}
    done_event = Event()

    @app.route("/data", methods=["POST"])
    def data_receiver():
        data = request.json
        print(f"[DESKTOP] 데이터 수신: {data}")
        result_holder['data'] = data
        
        # 클라이언트에 응답을 보낸 후 서버 종료 신호를 보냅니다.
        def delayed_set():
            done_event.set()
        Timer(0.5, delayed_set).start()
        return "OK", 200

    def run_server():
        # Werkzeug 서버의 로그를 비활성화하여 콘솔을 깨끗하게 유지
        import logging
        log = logging.getLogger('werkzeug')
        log.setLevel(logging.ERROR)
        app.run(host=host, port=port)

    server_thread = Thread(target=run_server, daemon=True)
    server_thread.start()
    print(f"[DESKTOP] {port} 포트에서 데이터 수신 대기 중...")
    
    # 데이터가 수신될 때까지 대기
    done_event.wait()
    
    print("[DESKTOP] 데이터 수신 완료.")
    return result_holder['data']


def video_playback_worker(video_path, result_queue):
    from multi3 import play_and_strip_audio
    try:
        output_path = play_and_strip_audio(video_path)
        result_queue.put(output_path)
    except Exception as e:
        result_queue.put(e)

# --- 멀티프로세싱을 위한 워커 함수 정의 ---

def opening_communication_worker(survey_age, result_queue):
    """
    [Worker] 오프닝 시퀀스의 통신을 담당. survey_age를 보내고 target_age를 받습니다.
    """
    print(f"[OPEN_COMM_WORKER] 설문 나이({survey_age}) 전송")
    send_to_server(survey_age)

    print("[OPEN_COMM_WORKER] 노트북으로부터 target_age 수신 대기 중...")
    received_data = receive_from_server()

    # 노트북에서 {'target_age': 2} 와 같은 형태로 데이터를 보낼 것으로 가정
    if received_data and 'target_age' in received_data:
        target_age = received_data.get('target_age')
        print(f"[OPEN_COMM_WORKER] target_age ({target_age}) 수신 완료.")
        result_queue.put(target_age)
    else:
        print(f"[OPEN_COMM_WORKER] 예상치 못한 데이터 수신: {received_data}. 나이 값 반환 실패.")
        result_queue.put(None) # 실패 시 None을 큐에 넣음

def communication_worker(result_queue):
    """
    [Worker] 엔딩 시퀀스의 통신을 담당하는 프로세스. 30을 보내고 100을 기다립니다.
    """
    print("[COMM_WORKER] 엔딩 신호(30) 전송")
    send_to_server(30)
    
    print("[COMM_WORKER] 노트북으로부터 종료 확인 신호(100) 대기 중...")
    received_data = receive_from_server()
    
    if received_data and received_data.get('command') == 100:
        print("[COMM_WORKER] 종료 확인 신호(100) 수신 완료.")
        result_queue.put(True)
    else:
        print(f"[COMM_WORKER] 예상치 못한 데이터 수신: {received_data}. 종료 실패.")
        result_queue.put(False)

def play_video_looper_worker(video_path, stop_event):
    """
    [Worker] stop_event가 설정될 때까지 영상을 반복 재생합니다.
    Windows 환경에 최적화되어 있습니다.
    """
    print(f"[VIDEO_WORKER] 비디오 반복 재생 시작: {video_path}")
    while not stop_event.is_set():
        try:
            print(f"[VIDEO_WORKER] 영상 한 사이클 재생...")
            # subprocess.run은 프로세스가 끝날 때까지 기다립니다 (blocking).
            # start /wait는 지정된 프로그램/명령을 실행하고 끝날 때까지 기다립니다.
            subprocess.run(f'start /wait "" "{video_path}"', shell=True, check=True)
        except subprocess.CalledProcessError:
            # 사용자가 비디오 플레이어를 수동으로 닫았을 때 발생할 수 있습니다.
            # 이 경우 루프를 계속하여 다시 재생합니다.
            print(f"[VIDEO_WORKER] 영상 플레이어가 닫혔습니다. 다시 재생합니다.")
            if not stop_event.is_set():
                time.sleep(0.5) # 짧은 대기
        except Exception as e:
            print(f"❌ [VIDEO_WORKER] 영상 재생 중 심각한 오류 발생: {e}")
            break # 다른 오류 발생 시 루프 중단
    print("[VIDEO_WORKER] 영상 반복 재생 종료.")


def opening_with_button(survey_age, video_path=r"C:\Artech5\Image_Box\loading.mp4"):
    """
    [수정] 통신이 완료될 때까지 영상을 반복 재생합니다.
    """
    print("[SERVER] 오프닝 시퀀스를 시작합니다.")
    result_queue = Queue()
    stop_event = Event()

    # 1. 통신을 위한 프로세스 생성
    comm_process = Process(target=opening_communication_worker, args=(survey_age, result_queue))
    
    # 2. 영상 반복 재생을 위한 프로세스 생성
    video_process = Process(target=play_video_looper_worker, args=(video_path, stop_event))
    
    # 두 프로세스를 동시에 시작
    comm_process.start()
    video_process.start()
    
    # 통신 프로세스가 끝날 때까지 기다립니다.
    comm_process.join()
    
    # 통신이 끝나면 영상 재생 프로세스에 종료 신호를 보냅니다.
    print("[SERVER] 통신 완료. 영상 재생 중지 신호 전송.")
    stop_event.set()

    # 영상 재생 프로세스가 완전히 종료될 때까지 기다립니다.
    video_process.join()
    
    # 통신 결과를 큐에서 가져옵니다.
    target_age = result_queue.get()

    if target_age is not None:
        print(f"[SERVER] 버튼 입력을 통해 새로운 나이대({target_age})를 받았습니다.")
        return target_age
    else:
        print(f"[SERVER] 버튼 입력 없이 영상이 종료되었거나 통신에 실패했습니다.")
        return survey_age # 실패 시 원래 나이 값을 반환

def ending_with_button():
    """
    [수정] 통신이 완료될 때까지 영상을 반복 재생합니다.
    """
    print("[SERVER] 엔딩 시퀀스를 시작합니다.")
    
    ending_video_path = r"C:\Artech5\Image_Box\Emergency.mp4"
    
    result_queue = Queue()
    stop_event = Event()
    
    # 1. 통신을 위한 프로세스 생성
    comm_process = Process(target=communication_worker, args=(result_queue,))
    
    # 2. 영상 반복 재생을 위한 프로세스 생성
    video_process = Process(target=play_video_looper_worker, args=(ending_video_path, stop_event))
    
    # 두 프로세스를 동시에 시작
    comm_process.start()
    video_process.start()
    
    # 통신 프로세스가 끝날 때까지 기다립니다.
    comm_process.join()
    
    # 통신이 끝나면 영상 재생 프로세스에 종료 신호를 보냅니다.
    print("[SERVER] 통신 완료. 영상 재생 중지 신호 전송.")
    stop_event.set()

    # 영상 재생 프로세스가 완전히 종료될 때까지 기다립니다.
    video_process.join()
    
    # 통신 결과를 큐에서 가져옵니다.
    is_success = result_queue.get()
    
    return is_success


def run_artech5():
    multiprocessing.freeze_support()
    multiprocessing.set_start_method('spawn', force=True)
    
    survey_result = run_survey_server()   
    print(f"[SERVER] 설문 결과: {survey_result}")
    
    survey_age = survey_result.get("age")
    if isinstance(survey_age, str) and survey_age.endswith("대"):
        try:
            survey_age = int(int(survey_age.replace("대", "")) / 10)
        except Exception:
            survey_age = None
            
    # [추가] 노트북에서 'start' 신호를 받을 때까지 대기
    print("[SERVER] 노트북으로부터 시작 신호('start') 대기 중...")
    while True:
        start_signal = receive_from_server()
        if start_signal and start_signal.get('command') == 'start':
            print("[SERVER] 시작 신호('start') 수신 완료.")
            break
        else:
            print(f"[SERVER] 예상치 못한 데이터 수신: {start_signal}. 다시 대기합니다.")

    
    print("버튼을 눌러주세요")
    target_age = opening_with_button(survey_age) 
    target_age = target_age * 10 
    print(f"[SERVER] 버튼으로 받은 target_age: {target_age}")
    
    gender = survey_result.get("gender")
    theme = survey_result.get("theme")
    first_voice, speaker = get_first_voice(target_age, gender, theme)
    print(f"[SERVER] 첫 번째 음성 파일: {first_voice}")
    
    # Flask 서버로 통신하는 함수를 호출합니다.
    print("[SERVER] 카메라 조명 ON 신호(10) 전송")
    send_to_server(10)
    
    face1 = capture() 
    
    # Flask 서버로 통신하는 함수를 호출합니다.
    print("[SERVER] 카메라 조명 OFF 신호(20) 전송")
    send_to_server(20)
    
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
    IsEnd = ending_with_button()
    
    if IsEnd:
        print("콘텐츠 종료")
    
    return IsEnd

if __name__ == "__main__":
    # 이 코드를 실행하기 전에 requests와 flask 라이브러리를 설치해야 합니다.
    # pip install requests flask
    run_artech5()
