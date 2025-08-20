import multiprocessing
import subprocess

from survey_client import run_survey_server
from capture import capture
from veo3_sam import run_veo3_with_sam
from veo3_sadtalker import veo3_with_sadtalker
from get_first_voice import get_first_voice
from multi3 import play_and_strip_audio
from stt_listen import mic_listen
from get_answer import get_answer
from ai_reply import AI_reply




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
    #target_age = opening_with_button(survey_age) 
    #target_age = target_age * 10 
    target_age = 50
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
        
    #talking_no_voice,whisper = play_and_process_concurrently(talking_video)
    
    # 이슈 있음!! 최초 ai 인간 등장 시, 영상 창이 숨기기 형태로 실행됨.

    talking_no_voice = play_and_strip_audio(talking_video)  # 영상 재생과 오디오 제거를 동시에 수행
    
    
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