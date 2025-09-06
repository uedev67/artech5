import serial, time
import sys

def open_arduino(port="COM3", baud=9600):
    ser = serial.Serial(port, baudrate=baud, timeout=0.1,
                        bytesize=serial.EIGHTBITS, parity=serial.PARITY_NONE,
                        stopbits=serial.STOPBITS_ONE,
                        xonxoff=False, rtscts=False, dsrdtr=False)
    # 리셋 안정화
    ser.setDTR(False); time.sleep(0.3); ser.setDTR(True)
    time.sleep(2.0)
    ser.reset_input_buffer(); ser.reset_output_buffer()
    return ser

def wait_ready(ser, wait_s=5):
    t0 = time.time()
    while time.time() - t0 < wait_s:
        try:
            line = ser.readline().decode(errors="ignore").strip()
            if line == "READY":
                return True
        except serial.SerialException:
            time.sleep(0.1)
    return False

def send_int(ser, n: int):
    ser.write(f"{n}\n".encode())
    ser.flush()

def recv_int(ser, timeout_s=10):
    deadline = time.time() + timeout_s
    buf = b""
    while time.time() < deadline:
        try:
            if ser.in_waiting:                    # 여기서 예외 나면 복구 시도
                buf += ser.read(ser.in_waiting)
                if b"\n" in buf:
                    line, _, buf = buf.partition(b"\n")
                    s = line.decode(errors="ignore").strip()
                    try:
                        return int(s)
                    except ValueError:
                        buf = b""                 # 쓰레기 라인 버림
            else:
                time.sleep(0.01)
        except serial.SerialException:
            # 장치가 잠깐 끊기면 버퍼 리셋 후 재시도
            try:
                ser.reset_input_buffer()
                ser.reset_output_buffer()
            except Exception:
                pass
            time.sleep(0.1)
    return None


# 외부에서 호출: target_age = button(survey_age)
def button(survey_age: int, port="COM3", baud=9600, timeout_s=15) -> int:
    ser = None
    try:
        ser = open_arduino(port, baud)
        # --- ▼▼▼ 수정된 부분 ▼▼▼ ---
        # 정보 메시지를 표준 에러(stderr)로 출력합니다.
        print(f"[INFO] 아두이노 포트 {port} 열림", file=sys.stderr)
        
        send_int(ser, survey_age)
        print(f"[INFO] 설문 나이대 {survey_age} 전송", file=sys.stderr)
        
        val = recv_int(ser, timeout_s=timeout_s)
        
        if val is None:
            print("[ERROR] 아두이노로부터 값을 시간 내에 받지 못했습니다.", file=sys.stderr)
            return survey_age
            
        return val

    finally:
        if ser and ser.is_open:
            ser.close()
            print(f"[INFO] 아두이노 포트 {port} 닫힘", file=sys.stderr)
        # --- ▲▲▲ 수정된 부분 ▲▲▲ ---




# 테스트용 코드
if __name__ == "__main__":
    survey_age = input("설문 나이대(예: 20): ")
    try:
        survey_age = int(survey_age)
    except Exception:
        print("[ERROR] 나이대는 숫자로 입력하세요.")
        exit(1)
    result = button(survey_age)
    print(f"[RESULT] 아두이노에서 받은 값: {result}")

