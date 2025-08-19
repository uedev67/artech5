import multiprocessing
import subprocess
#from multiprocessing import Process, Queue

import queue
from survey_client import run_survey_server
from button_test import button
from capture import capture
from veo3_sadtalker import veo3_with_samtalker
from get_first_voice import get_first_voice
from remove_audio import play_and_process_concurrently 




def opening_with_button(survey_age, video_path="C:\\Artech5\\Image_Box\\loadinig.mp4"):

    # 프로세스 간 통신을 위한 Queue 생성
    result_q = multiprocessing.Queue()
    error_q = multiprocessing.Queue()

    # 작업1: 아두이노 통신 (별도 프로세스에서 실행)
    def button_task(age, res_q, err_q):
        try:
            target_age = button(age)
            res_q.put(target_age)
        except Exception as e:
            err_q.put(("button", e))

    # 작업2: 오프ニング 영상 재생 (별도 프로세스에서 실행)
    def video_task(path, err_q):
        try:
            # ffplay로 영상 재생, 영상이 끝날 때까지 블로킹
            subprocess.run(
                ["ffplay", "-autoexit", "-fs", path],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
        except Exception as e:
            err_q.put(("video", e))

    # 각 작업을 수행할 프로세스 생성
    p_button = multiprocessing.Process(target=button_task, args=(survey_age, result_q, error_q), daemon=True)
    p_video  = multiprocessing.Process(target=video_task, args=(video_path, error_q))

    # 두 프로세스 시작
    p_button.start()
    p_video.start()

    # 버튼 입력 프로세스가 끝날 때까지 대기
    p_button.join()

    # 오류가 발생했는지 확인
    if not error_q.empty():
        who, err = error_q.get()
        # 다른 프로세스가 계속 실행되는 것을 막기 위해 종료시킴
        p_video.terminate() 
        raise RuntimeError(f"{who} 작업 중 오류 발생: {err}") from err

    # 결과 큐에서 target_age 가져오기
    target_age = result_q.get() if not result_q.empty() else None

    # 영상이 끝까지 재생되도록 대기
    p_video.join()

    return target_age



def main():
    # =============== 관객 입장 전 ========================
        survey_result = run_survey_server()   # 결과 변수는 gender, age, theme 의 이름으로 저장됨.
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
        
        
        # 스레딩 0 : 오프닝 + 버튼 유도
        #target_age = opening_with_button(survey_age) 
        #target_age = target_age * 10 
        target_age = 50
        print(f"[SERVER] 버튼으로 받은 target_age: {target_age}")
        gender = survey_result.get("gender")    # 설문 결과 : 성별
        theme = survey_result.get("theme")      # 설문 결과 : 테마
        
        first_voice = get_first_voice(target_age, gender, theme)    # 설문 결과에 따라 기생성된 음성 파일 불러오기
        print(f"[SERVER] 첫 번째 음성 파일: {first_voice}")
        
        # 신원 확인 : 카메라로 얼굴 캡쳐
        face1 = capture()  
        
        
        # ============ 스레딩1 (veo3 + sam/sadtalker) : 함수화해서 실행부에서는 함수 호출만! ============
        
        talking_video = veo3_with_samtalker(theme=theme, target_age=target_age, first_voice=first_voice)  
        
            
        # ============ 스레딩2 (sadtalker영상 실행 + 오디오제거작업 + whisper 모델 미리 로드) =============
        
        talking_no_voice,whisper = play_and_process_concurrently(talking_video)
        
        # 조명부에 통신 넣는 코드 추가하기
        
        # 아두이노로부터 B1 관련된 메시지 받으면 체험 종료로 인식하는 코드 작성하기
    
    
    
    
    
    
if __name__ == "__main__":

    # 모든 코드 실행 전에 멀티프로세싱 시작 방식을 'spawn'으로 명시합니다 : 라이브러리 충돌을 예방합니다.
    multiprocessing.set_start_method('spawn', force=True)

    main()    