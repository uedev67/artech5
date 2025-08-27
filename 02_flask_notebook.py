# 02_flask_notebook.py

import serial
import time
import requests
import json
from flask import Flask, request
from threading import Thread, Event
from queue import Queue


# --- 설정 ---
# 데스크탑의 IP 주소와 포트
DESKTOP_IP = '127.0.0.1'  # 실제 데스크탑의 IP 주소로 변경해야 합니다.
DESKTOP_PORT = 5002

# 이 노트북에서 실행할 서버의 포트
NOTEBOOK_PORT = 5001

# 아두이노 설정
ARDUINO_PORT = 'COM3'  # 실제 아두이노 포트로 변경해야 합니다.
BAUDRATE = 9600

# --- 전역 변수 ---
# 데스크탑으로부터 받은 데이터를 저장할 큐
desktop_data_queue = Queue()
# Flask 서버 종료를 위한 이벤트
shutdown_event = Event()

# --- 1. 데스크탑-노트북 통신 함수 ---

def send_to_desktop(data):
    """
    [클라이언트] 노트북에서 데스크탑으로 데이터를 전송합니다.
    """
    url = f"http://{DESKTOP_IP}:{DESKTOP_PORT}/data"
    headers = {'Content-Type': 'application/json'}
    try:
        response = requests.post(url, data=json.dumps(data), headers=headers, timeout=5)
        if response.status_code == 200:
            print(f"[NOTEBOOK] 데스크탑으로 데이터 전송 성공: {data}")
        else:
            print(f"❌ [NOTEBOOK] 데스크탑 전송 실패. 상태 코드: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"❌ [NOTEBOOK] 데스크탑에 연결할 수 없습니다: {e}")

def run_notebook_server():
    """
    [서버] 데스크탑으로부터 데이터를 수신하는 Flask 서버를 실행합니다.
    """
    app = Flask(__name__)

    @app.route("/control", methods=["POST"])
    def control_receiver():
        data = request.json
        print(f"[NOTEBOOK] 데스크탑으로부터 데이터 수신: {data}")
        # 수신한 데이터를 큐에 넣습니다.
        desktop_data_queue.put(data)
        return "OK", 200

    # 외부에서 서버를 종료할 수 있도록 셧다운 엔드포인트 추가
    @app.route('/shutdown', methods=['POST'])
    def shutdown():
        shutdown_event.set()
        return 'Server shutting down...'

    print(f"[NOTEBOOK] 0.0.0.0:{NOTEBOOK_PORT}에서 데스크탑의 연결을 기다립니다.")
    # host='0.0.0.0'으로 설정하여 모든 IP에서의 접근을 허용합니다.
    app.run(host='0.0.0.0', port=NOTEBOOK_PORT)

# --- 2. 노트북-아두이노 통신 함수 ---

def setup_arduino_connection(port, baudrate):
    """
    아두이노와의 시리얼 연결을 설정하고 객체를 반환합니다.
    """
    try:
        ser = serial.Serial(port, baudrate, timeout=1)
        time.sleep(2)  # 아두이노 리셋 및 안정화를 위한 대기
        print(f"[ARDUINO] {port} 포트 연결 성공.")
        return ser
    except serial.SerialException as e:
        print(f"❌ [ARDUINO] 에러: {port} 포트를 열 수 없습니다. {e}")
        return None

def send_to_arduino(ser, data):
    """
    아두이노로 데이터를 전송합니다.
    """
    if ser and ser.is_open:
        message = str(data) + '\n'
        ser.write(message.encode('utf-8'))
        print(f"[ARDUINO] 데이터 전송: {data}")
    else:
        print("❌ [ARDUINO] 연결이 끊어져 데이터를 보낼 수 없습니다.")

def receive_from_arduino(ser):
    """
    아두이노로부터 데이터가 들어올 때까지 기다렸다가 한 줄을 읽어 반환합니다.
    """
    if not ser or not ser.is_open:
        print("❌ [ARDUINO] 연결이 끊어져 데이터를 받을 수 없습니다.")
        return None
    
    print("[ARDUINO] 데이터 수신 대기 중...")
    while True:
        if ser.in_waiting > 0:
            line = ser.readline().decode('utf-8').strip()
            if line:
                print(f"[ARDUINO] 데이터 수신: {line}")
                return line
        time.sleep(0.1) # CPU 사용량을 줄이기 위한 짧은 대기

# --- 3. 메인 로직 ---

def main_logic(ser):
    """
    전체 통신 시퀀스를 관리합니다.
    """
    # 1. 아두이노로부터 'start' 신호 대기 및 데스크탑으로 전송
    while True:
        arduino_signal = receive_from_arduino(ser)
        if arduino_signal == 'start':
            send_to_desktop({'command': 'start'})
            break # 'start' 신호를 받으면 루프 탈출

    # 2. 오프닝 시퀀스: 데스크탑 -> 아두이노 -> 데스크탑
    print("[NOTEBOOK] 데스크탑으로부터 survey_age 대기 중...")
    desktop_data = desktop_data_queue.get() # 큐에서 데이터가 올 때까지 대기
    survey_age_str = desktop_data.get('command')
    
    age_to_arduino = None
    # [수정] '20대' 같은 문자열을 숫자로 변환
    if isinstance(survey_age_str, str) and survey_age_str.endswith("대"):
        try:
            # '20대' -> '20' -> 20 -> 2
            age_to_arduino = int(survey_age_str.replace("대", "")) // 10
        except ValueError:
            print(f"❌ [NOTEBOOK] 수신된 나이 값을 숫자로 변환할 수 없습니다: {survey_age_str}")
    else:
        # 예상치 못한 형식이거나, 이미 숫자로 들어온 경우를 대비
        age_to_arduino = survey_age_str

    if age_to_arduino is not None:
        send_to_arduino(ser, age_to_arduino)
    else:
        # 변환 실패 시 기본값 또는 에러 처리
        print("❌ [NOTEBOOK] 아두이노로 보낼 나이 값을 결정할 수 없어 0을 보냅니다.")
        send_to_arduino(ser, 0) # 예: 기본값으로 0 전송
    
    target_age = receive_from_arduino(ser)
    try:
        # 아두이노에서 받은 값이 숫자인지 확인
        target_age_int = int(target_age)
        send_to_desktop({'target_age': target_age_int})
    except (ValueError, TypeError):
        print(f"❌ [NOTEBOOK] 아두이노로부터 유효하지 않은 target_age 수신: {target_age}")


    # 3. 카메라 조명 제어
    print("[NOTEBOOK] 데스크탑으로부터 카메라 조명(10) 신호 대기 중...")
    desktop_data = desktop_data_queue.get()
    if desktop_data.get('command') == 10:
        send_to_arduino(ser, 10)

    print("[NOTEBOOK] 데스크탑으로부터 카메라 조명(20) 신호 대기 중...")
    desktop_data = desktop_data_queue.get()
    if desktop_data.get('command') == 20:
        send_to_arduino(ser, 20)

    # 4. 엔딩 시퀀스
    print("[NOTEBOOK] 데스크탑으로부터 엔딩(30) 신호 대기 중...")
    desktop_data = desktop_data_queue.get()
    if desktop_data.get('command') == 30:
        send_to_arduino(ser, 30)

    # 아두이노로부터 종료 확인 신호 대기
    end_signal = receive_from_arduino(ser)
    if end_signal == '100': # 아두이노에서 '100'을 보내기로 약속
        send_to_desktop({'command': 100})

    print("[NOTEBOOK] 모든 시퀀스가 완료되었습니다.")


if __name__ == "__main__":
    # 1. 아두이노 연결 시도
    arduino_ser = setup_arduino_connection(ARDUINO_PORT, BAUDRATE)

    if arduino_ser:
        # 2. Flask 서버를 별도의 스레드에서 시작
        server_thread = Thread(target=run_notebook_server)
        server_thread.daemon = True
        server_thread.start()
        
        # 3. 메인 로직 실행
        try:
            main_logic(arduino_ser)
        except KeyboardInterrupt:
            print("\n[NOTEBOOK] 프로그램 종료 중...")
        finally:
            # 4. 프로그램 종료 시 아두이노 연결 해제
            arduino_ser.close()
            print("[ARDUINO] 포트 연결 해제.")
            # Flask 서버 종료 요청
            try:
                requests.post(f'http://127.0.0.1:{NOTEBOOK_PORT}/shutdown')
            except requests.exceptions.RequestException:
                pass # 서버가 이미 꺼져있을 수 있음
            print("[NOTEBOOK] 서버 종료.")

