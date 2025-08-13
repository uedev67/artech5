# 모듈 임포트
import threading
from queue import Queue
from survey_client import run_survey_server
from button import button   # button_test.py로 변경해야함.
from capture import capture
from get_first_voice import get_first_voice
from veo3 import play_veo3
from sam import run_sam
from sadtalker import run_sadtalker
from remove_audio import remove_audio   
from gpt import ask_gpt
from gpt_stt import gpt_listen
from clova import clova
from ai_reply import AI_reply




def samtalker(target_age, first_voice):
    face2 = run_sam(target_age)                 # SAM
    talking_video = run_sadtalker(face2, first_voice)  # SadTalker
    return talking_video

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
            survey_age = int(survey_age.replace("대", ""))
        except Exception:
            survey_age = None
     
     
    # 스레딩 0 ; 오프닝 + 버튼 유도
    target_age = button(survey_age)    
    gender = survey_result.get("gender")    # 설문 결과 : 성별
    theme = survey_result.get("theme")      # 설문 결과 : 테마
    
    first_voice = get_first_voice(target_age, gender, theme)    # 설문 결과에 따라 기생성된 음성 파일 불러오기
    
    # 신원 확인 : 카메라로 얼굴 캡쳐
    face1 = capture()
    
    
    # ============ 스레딩1 (veo3 + sam/sadtalker) : 함수화해서 실행부에서는 함수 호출만! ============
    
    # play_veo3() 에서 테마에 따른 영상 선택 로직 작성해야함 + 테마/성별/나이대에 따른 first_voice 미리 만들어둬야 함.
    talking_video = veo3_with_samtalker(theme=theme, target_age=target_age, first_voice=first_voice)  
    
        
    # ============ 스레딩2 (sadtalker영상 실행 + 영상에서 음성만 제외하고 따로 저장) =============
    
    # talking_video를 실행 : 이거 따로 실행하는 함수 파일을 따로 제작하기
    # 동시에 talking_video에서 음성만 삭제된 영상(talking_no_voice)을 따로 저장
    talking_no_voice = remove_audio(talking_video)
    
    
    # ======================== ai와 관객의 상호 대화 파트 ==================================
    
    # 노화된 얼굴 face2는 화질이 좋으니, veo3 끝나고 잠시동안(한 2초?) 전체화면으로 보여주자.
    # sadtalker 영상은 화질이 다소 떨어지니, 왼쪽 화면 일부에서 재생, 오른쪽 화면엔 노화된 얼굴과 테마 설명글 배치.(신원증처럼)

    # 이미 스레딩2에서 ai가 먼저 말을 걸었음. 
    # 관객이 ai에게 답변(마이크 활성화)
    user_input = gpt_listen(duration=5)
    answer = ask_gpt(user_input, theme)
    # 클로바 tts 파일 함수화(target_age,gender,answer를 인자로 받는)하기. 
    voice = clova(target_age, gender, answer)   # 인자에 목소리 톤,속도,감정 추가 가능함.

    # voice + talking_no_voice를 합친 영상을 출력하고 성공하면 true를 반환
    IsReplySuccess = AI_reply(talking_no_voice, voice)   # cv2 기반

    # 관객이 다시 ai에게 답변
    if IsReplySuccess:
        user_input = gpt_listen(duration=5)
        answer = ask_gpt(user_input, theme)
        voice = clova(target_age, gender, answer)

    AI_reply(talking_no_voice, voice)

    # 시공간이 흔들리는 연출 + 돌아갈 시간이라며 관객에게 B1을 누르도록 유도
    
    

    