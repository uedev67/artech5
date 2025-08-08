import serial
import time


# 1. 설문에서 나이대 입력받음 
def visitor_age(age: int) -> int:
    """
    23 -> 2(20대), 45 -> 4(40대) 처럼 '연령대 버튼(1~9)'로 변환.
    범위를 벗어나면 1~9로 클램프.
    """
    btn = age // 10  # 23 -> 2, 45 -> 4
    return btn


# 2. 입력받은 나이대로 활성화할 버튼 범위 계산 
def activate_button_range(baseline_btn: int, window: int = 5) -> set:
    """
    baseline_btn ± window 범위를 1~9에서 클램프해 활성 버튼 집합 반환.
    예: baseline=2, window=5 -> {1,2,3,4,5,6,7}
    """
    start = max(1, baseline_btn - window)
    end   = min(9, baseline_btn + window)
    return set(range(start, end + 1))


# 3. 활성화된 버튼 중 눌린 버튼값 반환
def wait_selection_from_arduino(port: str, baud: int, enabled: set, 
                                notify_arduino: bool = True, timeout: int | None = None):

    with serial.Serial(port=port, baudrate=baud, timeout=1) as ser:
        time.sleep(2)  # 포트 안정화

        # 아두이노에 활성 범위 알려주기
        if notify_arduino:
            start, end = min(enabled), max(enabled)
            ser.write(f"EN:{start}-{end}\n".encode())

        print(f"[INFO] 활성 버튼: {sorted(enabled)} (비활성은 눌러도 무시)")
        start_time = time.time() # 여기서부터 run_flow()의 타이머 시작

        while True:
            if timeout and (time.time() - start_time) > timeout:
                print("[WARN] 시간 초과")
                return None

            if ser.in_waiting > 0:
                raw = ser.readline().decode(errors="ignore").strip()
                if not raw.isdigit():
                    continue

                btn = int(raw)
                if btn < 1 or btn > 9:
                    continue

                if btn in enabled:
                    target_age = btn * 10
                    print(f"[OK] 선택됨: 버튼 {btn} → target_age={target_age}")
                    return target_age
                else:
                    print(f"[BLOCK] 비활성 버튼 {btn} 입력 감지 → 무시")
                    # (옵션) 아두이노에 삑/LED 신호 요청 가능: ser.write(b"BUZ\n")


# 4. 1~3번 함수를 조합한 실행 함수
def run_flow(survey_age: int, port: str = "COM3", baud: int = 9600, timeout: int | None = None):

    baseline_btn = visitor_age(survey_age)     # 1번 함수
    enabled = activate_button_range(baseline_btn, 5)     # 2번 함수

    target_age = wait_selection_from_arduino(
        port=port,
        baud=baud,
        enabled=enabled,
        notify_arduino=True,  # LED 제어 등 필요없으면 False
        timeout=timeout
    )
    return target_age


# 실행부 : 관객 나이에 따른 버튼 활성화 + 버튼값 받기
if __name__ == "__main__":
    
    survey_age = 23 # 다른 파일에서 설문 나이를 받았다고 가정 (예: 23세)

    target_age = run_flow(survey_age=survey_age, port="COM3", baud=9600, timeout=20)
    print(target_age)
