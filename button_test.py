import serial, time

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

if __name__ == "__main__":
    ser = open_arduino("COM3", 9600)
    # 아두이노 setup()에서 READY를 보내게 해두면 안정적
    wait_ready(ser)  # 실패해도 계속 진행하고 싶으면 선택적으로 사용

    age = 3
    send_int(ser, age)
    print(f"[SEND] {age} 전송")
    time.sleep(5)
    print("[RECV] 대기…")
    val = recv_int(ser, timeout_s=10)
    print("[MAIN] 받은 숫자:", val)
    ser.close()
