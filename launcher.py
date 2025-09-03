# launcher.py (로직 수정 버전)

import serial
import time
import artech_test2

SERIAL_PORT = 'COM3'  
BAUD_RATE = 9600

print(f"🚀 실행기(Launcher)가 시작되었습니다. {SERIAL_PORT} 포트에서 'START' 신호를 기다립니다...")

while True:
    ser = None
    try:
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
        print("✅ 아두이노가 연결되었습니다. 신호 대기 중...")
        
        # [수정] 이 내부 루프는 이제 종료되지 않고 계속 신호를 기다립니다.
        while True:
            line = ser.readline().decode('utf-8').strip()
            
            if line == "START":
                print(" 'START' 신호를 받았습니다! 체험을 시작합니다.")
                ser.close() # 통신은 artech_test2에서 개별적으로 하므로 여기서 닫습니다.
                
                try:
                    is_finished = artech_test2.run_artech5()
                    
                    if is_finished:
                        print("✅ 체험이 정상적으로 종료되었습니다.")
                    else:
                        print("⚠️ 체험이 비정상적으로 종료되었습니다.")
                
                except Exception as e:
                    print(f"❌ 체험 실행 중 오류 발생: {e}")
                
                # [수정] break를 제거하고, 다시 루프의 시작으로 돌아가 포트를 열고 신호를 기다립니다.
                print("\n다음 'START' 신호를 위해 재연결합니다...")
                break # 내부 루프를 탈출하여 바깥 루프에서 재연결하도록 함

    except serial.SerialException:
        print(f"❌ 오류: 아두이노를 {SERIAL_PORT}에서 찾을 수 없습니다. 5초 후 재시도합니다.")
        time.sleep(5)
    except Exception as e:
        print(f"❌ 예상치 못한 오류 발생: {e}")
        time.sleep(5)
    finally:
        if ser and ser.is_open:
            ser.close()
