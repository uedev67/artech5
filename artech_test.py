import multiprocessing
from multiprocessing import Process, Queue
import threading

from queue import Queue
from survey_client import run_survey_server
from button_test import button
from capture import capture
from get_first_voice import get_first_voice
from veo3 import play_veo3
from sam import run_sam
from sadtalker import run_sadtalker
from remove_audio import play_and_remove_audio_concurrently  




def opening_with_button(survey_age, video_path="C:\Artech5\Image_Box\loadinig.mp4"):
    import threading
    from queue import Queue
    from button_test import button
    import subprocess
    result_q, error_q = Queue(), Queue()

    # 작업1: 아두이노 통신으로 target_age 받기
    def button_task():
        try:
            target_age = button(survey_age)
            result_q.put(target_age)
        except Exception as e:
            error_q.put(("button", e))

    # 작업2: 오프닝 영상 재생
    def video_task():
        try:
            # ffplay로 영상 재생, 영상 끝날 때까지 블로킹
            subprocess.run([
                "ffplay", "-autoexit", "-fs", video_path
            ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception as e:
            error_q.put(("video", e))

    t_button = threading.Thread(target=button_task, daemon=True)
    t_video  = threading.Thread(target=video_task, daemon=False)

    t_button.start()
    t_video.start()

    # target_age 받을 때까지 대기
    t_button.join()
    if not error_q.empty():
        who, err = error_q.get()
        raise err
    target_age = result_q.get() if not result_q.empty() else None

    # 영상은 끝까지 재생해야 하므로 기다림
    t_video.join()
    return target_age


def samtalker(target_age, first_voice):
    face2 = run_sam(target_age)                 # SAM
    print("sam 모델 실행 완료함. 다음 단계로 넘어가는지 확인하는 메시지")
    talking_video = run_sadtalker(face2, first_voice)  # SadTalker
    print("sadtalker 모델 실행 완료함. 다음 단계로 넘어가는지 확인하는 메시지")
    return talking_video



# 스레딩1 -> 멀티프로세싱으로 변경 (오류 처리 강화 버전)
def veo3_with_samtalker(theme, target_age, first_voice):
    result_q = Queue()

    # 작업1: veo3 영상 재생
    def video_task():
        try:
            play_veo3(theme)
        except Exception as e:
            # 영상 재생 프로세스에서 오류 발생 시, 큐에 에러를 넣어 알릴 수 있음
            # (필요에 따라 구현)
            print(f"[ERROR in video_task]: {e}")

    # 작업2: SAM + SadTalker (오류를 큐로 전달하도록 수정)
    def work_task(q):
        try:
            # 이 안에서 실행되는 samtalker 함수의 성공/실패가 중요
            print("[work_task] SAM+SadTalker 프로세스 시작")
            out = samtalker(target_age, first_voice)
            q.put(out) # 성공 시 결과물을 큐에 넣음
            print("[work_task] 작업 성공, 결과를 큐에 넣음")
        except Exception as e:
            print(f"[work_task] 작업 중 오류 발생: {e}")
            q.put(e) # 실패 시 예외(Exception) 객체 자체를 큐에 넣음

    # Process 객체 생성
    p_video = Process(target=video_task)
    p_work  = Process(target=work_task, args=(result_q,))

    print("veo3 및 samtalker 프로세스를 시작합니다.")
    p_video.start()
    p_work.start()

    # 작업(샘토커)이 끝날 때까지 큐에서 결과를 기다림 (가장 중요한 부분)
    print("메인 프로세스: samtalker의 결과를 기다리는 중...")
    result = result_q.get() # 여기서 블로킹되며, work_task가 결과를 넣을 때까지 대기
    print("메인 프로세스: 큐에서 결과를 받았습니다.")

    # 받은 결과가 예외 객체인지 확인
    if isinstance(result, Exception):
        print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
        print("!!! SadTalker 프로세스에서 오류가 발생했습니다 !!!")
        print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
        # p_video.terminate() # 영상 프로세스를 강제 종료할 필요가 있다면 주석 해제
        raise result # 받은 예외를 메인 프로세스에서 다시 발생시켜 오류를 명확히 확인

    # 모든 프로세스가 정상적으로 끝날 때까지 기다림
    p_work.join()
    p_video.join()
    print("모든 프로세스가 정상적으로 종료되었습니다.")

    return result # 성공적인 결과(talking_video 경로) 반환





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
        face1 = capture()   # 전체화면, 1:1 비율 화면으로 모니터에 띄우기
        
        
        
        # ============ 스레딩1 (veo3 + sam/sadtalker) : 함수화해서 실행부에서는 함수 호출만! ============
        
        # play_veo3() 에서 테마에 따른 영상 선택 로직 작성해야함 + 테마/성별/나이대에 따른 first_voice 미리 만들어둬야 함.
        talking_video = veo3_with_samtalker(theme=theme, target_age=target_age, first_voice=first_voice)  
        
            
        # ============ 스레딩2 (sadtalker영상 실행 + 오디오제거작업 + whisper 모델 미리 로드) =============
        
        talking_no_voice,whisper = play_and_remove_audio_concurrently(talking_video)
        # 조명부에 통신 넣는 코드 추가하기
        
        # 아두이노로부터 B1 관련된 메시지 받으면 체험 종료로 인식하는 코드 작성하기
    
    
    
    
    
if __name__ == "__main__":
    # !!! 가장 중요한 부분 !!!
    # 모든 코드 실행 전에 멀티프로세싱 시작 방식을 'spawn'으로 명시합니다.
    # Windows의 기본값이지만, 라이브러리 충돌을 피하기 위해 명시적으로 가장 먼저 호출합니다.
    multiprocessing.set_start_method('spawn', force=True)

    # 이제 main() 함수를 호출하여 프로그램을 실행합니다.
    main()    