# 모듈 임포트
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
from gpt import ask_gpt
from gpt_stt import gpt_listen
from clova import clova
from ai_reply import AI_reply
import time







def samtalker(target_age, first_voice):
    face2 = run_sam(target_age)                 # SAM
    talking_video = run_sadtalker(face2, first_voice)  # SadTalker
    return talking_video


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


# 스레딩1
def veo3_with_samtalker(theme, target_age, first_voice):
    result_q, error_q = Queue(), Queue()

    # 작업1 : veo3 영상 재생
    def video_task():
        try:
            # 주의: play_veo3(theme)은 내부에서 동영상이 끝날 때까지 블로킹/루프 후
            # 창/프로세스를 스스로 정리하고 return 해야 함 (중간 강제종료 X).
            play_veo3(theme)
        except Exception as e:
            error_q.put(("video", e))

    # 작업2 : SAM + SadTalker
    def work_task():
        try:
            out = samtalker(target_age, first_voice)
            result_q.put(out)
        except Exception as e:
            error_q.put(("work", e))

    t_video = threading.Thread(target=video_task, daemon=False)  # 자연 종료 기다림
    t_work  = threading.Thread(target=work_task,  daemon=True)   # 작업만 끝나면 됨. veo3 영상은 계속 재생

    t_video.start()
    t_work.start()

    # 작업(샘토커) 완료까지 기다려 결과 확보
    t_work.join()
    # 에러 체크
    if not error_q.empty():
        who, err = error_q.get()
        # 영상은 계속 재생해야 하므로 여기서 중단 신호는 보내지 않음
        raise err

    talking_video = result_q.get() if not result_q.empty() else None

    # ② 영상은 끝까지 재생해야 하므로 여기서도 기다림
    t_video.join()

    return talking_video  # 반환값 : saddtalker 결과값


# 대화부 : 관객 음성 듣고, ai 음성을 반환
def mic_listen_and_reply(theme,target_age,gender,whisper):
    
    while whisper is None:
        time.sleep(0.1)
    
    user_input = gpt_listen(duration=7, whisper_model=whisper)  # whisper 모델이 준비된 후 gpt_listen 실행
    answer = ask_gpt(user_input, theme)
    voice = clova(target_age, gender, theme, answer)    # 인자에 speed,pitch,speaker 추가
    
    return voice




# 실행부
if __name__ == "__main__":
    

# =============== 관객 입장 전 ========================
    survey_result = run_survey_server()   # 결과 변수는 gender, age, theme 의 이름으로 저장됨.
    print(f"[SERVER] 설문 결과: {survey_result}")


# ============= 관객 입장 후  =========================
    
    
    survey_age = survey_result.get("age")    # 설문 결과 : 관객 나이대 받기   

    # survey_age에는 "20대"처럼 string으로 저장됨. 이걸 int 타입으로 변환해줌.
    if isinstance(survey_age, str) and survey_age.endswith("대"):
        try:
            survey_age = int(survey_age.replace("대", ""))/10
        except Exception:
            survey_age = None
     
    
    # 스레딩 0 : 오프닝 + 버튼 유도
    target_age = opening_with_button(survey_age) 
    target_age = target_age * 10 
    gender = survey_result.get("gender")    # 설문 결과 : 성별
    theme = survey_result.get("theme")      # 설문 결과 : 테마
    
    first_voice = get_first_voice(target_age, gender, theme)    # 설문 결과에 따라 기생성된 음성 파일 불러오기
    
    # 신원 확인 : 카메라로 얼굴 캡쳐
    face1 = capture()   # 전체화면, 1:1 비율 화면으로 모니터에 띄우기
    
    
    # ============ 스레딩1 (veo3 + sam/sadtalker) : 함수화해서 실행부에서는 함수 호출만! ============
    
    # play_veo3() 에서 테마에 따른 영상 선택 로직 작성해야함 + 테마/성별/나이대에 따른 first_voice 미리 만들어둬야 함.
    talking_video = veo3_with_samtalker(theme=theme, target_age=target_age, first_voice=first_voice)  
    
        
    # ============ 스레딩2 (sadtalker영상 실행 + 오디오제거작업 + whisper 모델 미리 로드) =============
    
    talking_no_voice,whisper = play_and_remove_audio_concurrently(talking_video)
    # 조명부에 통신 넣는 코드 추가하기
    
    
    # ======================== ai와 관객의 상호 대화 파트 ==================================

    # 이미 스레딩2에서 ai가 먼저 말을 걸었음. 

    # 관객이 ai에게 답변하는 부분
    voice = mic_listen_and_reply(theme,target_age,gender,whisper_model=whisper)    # 인자에 목소리 톤,속도,감정 추가 가능함.

    # voice + talking_no_voice를 합친 영상을 출력하고 성공하면 true를 반환
    IsReplySuccess = AI_reply(talking_no_voice, voice)   # cv2 기반
    
    # 관객이 다시 ai에게 답변
    if IsReplySuccess:
        voice = mic_listen_and_reply(theme,target_age,gender)

    AI_reply(talking_no_voice, voice)

    # 시공간이 흔들리는 연출 + 돌아갈 시간이라며 관객에게 B1을 누르도록 유도
    
    # 아두이노로부터 B1 관련된 메시지 받으면 체험 종료로 인식하는 코드 작성하기
    
    


    