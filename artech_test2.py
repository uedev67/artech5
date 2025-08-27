import multiprocessing
import subprocess
import sys
import os
from multiprocessing import Process, Queue

from survey_client import run_survey_server
from button_test import button
from capture import capture
from veo3_sam import run_veo3_with_sam
from veo3_sadtalker import veo3_with_sadtalker
from get_first_voice import get_first_voice
from stt_listen import mic_listen
from get_answer import get_answer
from ai_reply import AI_reply



def opening_with_button(survey_age, video_path=r"C:\Artech5\Image_Box\loading.mp4"):
    """
    영상 재생과 버튼 입력을 동시에 처리하는 통합 Worker('interactive_player_worker.py')를 실행합니다.
    """
    print("[SERVER] 오프닝 시퀀스를 시작합니다. (통합 Worker 호출)")
    
    # __file__은 현재 실행 중인 스크립트의 절대 경로를 나타냅니다.
    main_path = os.path.dirname(os.path.abspath(sys.argv[0]))
    # 호출할 통합 워커 스크립트의 경로를 정확히 지정합니다.
    worker_path = os.path.join(main_path, 'interactive_player_worker.py')

    # 실행할 명령어와 인자들을 리스트로 구성합니다.
    command = [
        sys.executable,
        worker_path,
        '--path', video_path,
        '--age', str(survey_age)
    ]
    
    # 통합 Worker를 실행하고, 끝날 때까지 기다린 후, 결과(stdout)와 에러(stderr)를 가져옵니다.
    proc = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = proc.communicate()

    # Worker가 정상적으로 종료되었고(returncode 0), 결과를 출력했다면(stdout)
    if proc.returncode == 0 and stdout:
        # Worker가 출력한 값을 정수로 변환하여 저장합니다.
        target_age = int(stdout.decode().strip())
        print(f"[SERVER] 버튼 입력을 통해 새로운 나이대를 받았습니다: {target_age}")
        return target_age
    else:
        # Worker가 결과를 출력하지 않았거나 오류로 종료된 경우
        # (예: 사용자가 버튼을 안 누르고 영상이 자연스럽게 끝난 경우)
        print(f"[SERVER] 버튼 입력 없이 영상이 종료되었습니다. stderr: {stderr.decode('utf-8', 'ignore').strip()}")
        # 이 경우, 설문으로 받은 나이대를 그대로 사용하도록 기본값을 반환합니다.
        return survey_age



def video_playback_worker(video_path, result_queue):
    """
    영상 재생 및 오디오 제거를 별도 프로세스에서 실행하는 함수.
    'spawn' 방식에서는 필요한 모듈을 이 함수 안에서 import 해야 합니다.
    """
    from multi3 import play_and_strip_audio
    try:
        # play_and_strip_audio 함수를 실행하고 결과(오디오 제거된 파일 경로)를 얻습니다.
        output_path = play_and_strip_audio(video_path)
        # 결과를 Queue에 넣어 부모 프로세스에 전달합니다.
        result_queue.put(output_path)
    except Exception as e:
        # 오류가 발생하면 오류 객체를 Queue에 넣어 전달합니다.
        print(f"[WORKER_ERROR] 영상 처리 중 오류 발생: {e}")
        result_queue.put(e)
        
        


if __name__ == "__main__":
    
    multiprocessing.freeze_support()
    multiprocessing.set_start_method('spawn', force=True)
    
    # =============== 관객 입장 전 ========================
    survey_result = run_survey_server()   
    print(f"[SERVER] 설문 결과: {survey_result}")
    
    
    # ============= 관객 입장 후  =========================
        
        
    survey_age = survey_result.get("age")    # 설문 결과 : 관객 나이대 받기   

    # survey_age에는 "20대"처럼 string으로 저장됨. 이걸 int 타입으로 변환해줌.
    if isinstance(survey_age, str) and survey_age.endswith("대"):
        try:
            survey_age = int(survey_age.replace("대", ""))/10
            survey_age = int(survey_age)  
        except Exception:
            survey_age = None
    
    
    # 멀티0 : 오프닝 + 버튼 유도
    print("버튼을 눌러주세요")
    target_age = opening_with_button(survey_age) 
    target_age = target_age * 10 
    #target_age = 50
    print(f"[SERVER] 버튼으로 받은 target_age: {target_age}")
    gender = survey_result.get("gender")    # 설문 결과 : 성별
    theme = survey_result.get("theme")      # 설문 결과 : 테마
    
    first_voice = get_first_voice(target_age, gender, theme)    # 설문 결과에 따라 기생성된 음성 파일 불러오기
    print(f"[SERVER] 첫 번째 음성 파일: {first_voice}")
    
    # 조명 1 : 조명부에 통신 넣는 코드 추가하기 (카메라 조명 켜기)
    # 신원 확인 : 카메라로 얼굴 캡쳐
    face1 = capture() 
    # 조명 2 : 조명부에 통신 넣는 코드 추가하기(카메라 조명 끄기)
    
    # ============ 멀티1 (veo3 intro + sam) : 함수화해서 실행부에서는 함수 호출만! ============
    
    face2 = run_veo3_with_sam(target_age=target_age, face_path=face1)  # SAM을 통해 변환된 얼굴 이미지 경로
    
    
    # ============ 멀티2 (veo3 main + sadtalker) : 함수화해서 실행부에서는 함수 호출만! ============
    
    talking_video = veo3_with_sadtalker(theme=theme, first_voice=first_voice, face2 =face2)  
    
    # ============ 멀티3 (sadtalker영상 실행 + 오디오제거작업 + whisper 모델 미리 로드) =============
        
    
    print("[SERVER] 영상 재생 및 오디오 제거를 위한 별도 프로세스를 시작합니다.")
    # 결과를 주고받기 위한 Queue 생성
    result_queue = Queue()

    # 영상 처리를 담당할 프로세스 생성 및 시작
    video_process = Process(target=video_playback_worker, args=(talking_video, result_queue))
    video_process.start()
    
    # Queue에서 결과가 올 때까지 기다립니다.
    result = result_queue.get() 
    # 프로세스가 완전히 종료될 때까지 기다립니다.
    video_process.join()

    # 결과가 오류 객체인지 확인합니다.
    if isinstance(result, Exception):
        raise result # 오류였다면 프로그램을 중단
    else:
        talking_no_voice = result # 정상 결과라면 변수에 저장
        print(f"[SERVER] 영상 처리 완료. 오디오 제거 파일: {talking_no_voice}")
    
    
    # ============ 멀티4 (음성 인식) : mic_listen 함수 호출 =========================
    
    user_input = mic_listen(
        loading_video=r"C:\Artech5\Image_Box\loading.mp4",
        ready_video=r"C:\Artech5\Image_Box\mic_listening.mp4",
        duration=10
    )


    # ============ 멀티5 (ai 답변 처리) : get_answer() = ask_gpt + clova  =========================
    
    voice = get_answer(user_input,theme,target_age,gender)
    
    print(f"[SERVER] 생성된 음성 파일 경로: {voice}")
    
    
    #voice + talking_no_voice를 합친 영상을 출력하고 성공하면 true를 반환
    IsReplySuccess = AI_reply(talking_no_voice, voice)   # cv2 기반
    
    # 바로 꺼지지 않고, 통신 에러(지지직) 등의 연출로 버무리기
    
    
    #관객이 다시 ai에게 답변
    if IsReplySuccess:
        
        user_input = mic_listen(
        loading_video=r"C:\Artech5\Image_Box\loading.mp4",
        ready_video=r"C:\Artech5\Image_Box\mic_listening.mp4",
        duration=10
        )
        
        voice = get_answer(user_input,theme,target_age,gender)


    AI_reply(talking_no_voice, voice)  
    
    # 조명 3 : 조명부에 통신 넣는 코드 추가하기(돌아갈 시간!)
    
    # 시공간이 흔들리는 연출 + 돌아갈 시간이라며 관객에게 B1을 누르도록 유도
    
    # 아두이노로부터 B1 관련된 메시지 받으면 체험 종료로 인식하는 코드 작성하기
    
    

