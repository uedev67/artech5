# artech_test2.py (개별 통신 방식으로 수정됨)

import multiprocessing
import subprocess
import sys
import os
import time
import serial # serial 모듈을 다시 import 합니다.
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


def send_to_arduino(data, port='COM3', baudrate=9600):
    """
    [헬퍼 함수] 아두이노에 데이터를 보낼 때마다 포트를 열고 닫습니다.
    """
    try:
        with serial.Serial(port, baudrate) as ser:
            time.sleep(2)  # 아두이노 리셋 및 안정화를 위한 필수 대기
            message = str(data) + '\n'
            ser.write(message.encode('utf-8'))
            print(f"[ARDUINO] 포트 {port}로 데이터 '{data}' 전송 성공")
    except serial.SerialException as e:
        print(f"❌ [ARDUINO] 에러: 포트 {port}를 열 수 없습니다. {e}")


def opening_with_button(survey_age, video_path=r"C:\Artech5\Image_Box\loading.mp4"):
    """
    이 함수는 이제 다시 원래의 subprocess 방식으로 동작합니다.
    내부적으로 'interactive_player_worker.py'가 자체적으로 통신합니다.
    """
    print("[SERVER] 오프닝 시퀀스를 시작합니다. (통합 Worker 호출)")
    main_path = os.path.dirname(os.path.abspath(sys.argv[0]))
    worker_path = os.path.join(main_path, 'interactive_player_worker.py')
    
    # [수정] --age 인자를 다시 추가하여 survey_age 값을 전달합니다.
    # [이유] interactive_player_worker.py 스크립트는 --age 인자를 필수로 요구합니다.
    #       이 값을 전달해야 워커가 정상적으로 실행되고, 버튼 입력을 처리할 수 있습니다.
    #       subprocess로 전달하는 인자는 모두 문자열이어야 하므로 str()로 변환합니다.
    command = [sys.executable, worker_path, '--path', video_path, '--age', str(survey_age)]
    
    proc = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = proc.communicate()

    if proc.returncode == 0 and stdout:
        try:
            target_age = int(stdout.decode().strip())
            print(f"[SERVER] 버튼 입력을 통해 새로운 나이대를 받았습니다: {target_age}")
            return target_age
        except ValueError:
            print(f"[SERVER] Worker로부터 예상치 못한 값을 받았습니다: {stdout.decode().strip()}")
            return survey_age
    else:
        print(f"[SERVER] 버튼 입력 없이 영상이 종료되었거나 Worker에서 오류가 발생했습니다.")
        # 오류 디버깅을 위해 stderr를 출력하는 것이 좋습니다.
        error_message = stderr.decode('utf-8', 'ignore').strip()
        if error_message:
            print(f"[SERVER] Worker 오류 내용: {error_message}")
        return survey_age


def video_playback_worker(video_path, result_queue):
    from multi3 import play_and_strip_audio
    try:
        output_path = play_and_strip_audio(video_path)
        result_queue.put(output_path)
    except Exception as e:
        result_queue.put(e)


def ending_with_button():
    # 이 함수도 자체적으로 통신하는 워커를 호출합니다.
    print("[SERVER] 엔딩 시퀀스를 시작합니다. (Worker 호출)")
    main_path = os.path.dirname(os.path.abspath(sys.argv[0]))
    worker_path = os.path.join(main_path, 'ending_with_button.py')
    command = [sys.executable, worker_path]
    proc = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    proc.communicate()
    return proc.returncode == 0


# [수정] 메인 실행함수가 더 이상 'ser' 객체를 받지 않습니다.
def run_artech5():
    multiprocessing.freeze_support()
    multiprocessing.set_start_method('spawn', force=True)
    
    survey_result = run_survey_server()   
    print(f"[SERVER] 설문 결과: {survey_result}")
    
    survey_age = survey_result.get("age")
    if isinstance(survey_age, str) and survey_age.endswith("대"):
        try:
            # "20대" -> 20 -> 2 로 변환
            survey_age = int(int(survey_age.replace("대", "")) / 10)
        except Exception:
            survey_age = 2 # 기본값 설정
    
    print("버튼을 눌러주세요")
    target_age = opening_with_button(survey_age) 
    target_age = target_age * 10 
    print(f"[SERVER] 버튼으로 받은 target_age: {target_age}")
    
    gender = survey_result.get("gender")
    theme = survey_result.get("theme")
    first_voice, speaker = get_first_voice(target_age, gender, theme)
    print(f"[SERVER] 첫 번째 음성 파일: {first_voice}")
    
    # [수정] 헬퍼 함수를 사용해 통신하고 포트를 바로 닫습니다.
    print("[SERVER] 카메라 조명 ON 신호(10) 전송")
    send_to_arduino(10)
    
    # 통신이 끊어진 상태에서 카메라를 실행합니다.
    face1 = capture() 
    
    # [수정] 카메라 작업 후, 다시 포트를 열어 통신합니다. (2초 딜레이 발생)
    print("[SERVER] 카메라 조명 OFF 신호(20) 전송")
    send_to_arduino(20)
    
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
    run_artech5()
