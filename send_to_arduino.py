
import serial
import time

def send_to_arduino(data, port='COM3', baudrate=9600):

    try:
        ser = serial.Serial(port, baudrate)
        time.sleep(2)  # 시리얼 연결 안정화를 위한 대기
        
        ser.write(str(data).encode())
        print(f"포트 {port}로 데이터 '{data}' 전송 성공")
        
        ser.close()
        return True
    except serial.SerialException as e:
        print(f"에러: {port} 포트를 열 수 없습니다. {e}")
        return False



if __name__ == "__main__":
    
    
    # 함수 호출로 의도가 명확해짐
    is_success = send_to_arduino(10)
    
    if is_success:
        print("아두이노로 데이터 전송 완료")
    else:
        print("아두이노 통신 실패")
        
