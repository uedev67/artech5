import multiprocessing
import subprocess

from survey_client import run_survey_server
from capture import capture
from veo3_sam import run_veo3_with_sam
from veo3_sadtalker import veo3_with_sadtalker
from get_first_voice import get_first_voice
from remove_audio import play_and_process_concurrently 




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
    
    # 신원 확인 : 카메라로 얼굴 캡쳐
    face1 = capture() 
    
    # ============ 멀티1 (veo3 intro + sam) : 함수화해서 실행부에서는 함수 호출만! ============
    
    face2 = run_veo3_with_sam(target_age=target_age, face_path=face1)  # SAM을 통해 변환된 얼굴 이미지 경로
    
    
    # ============ 멀티2 (veo3 main + sadtalker) : 함수화해서 실행부에서는 함수 호출만! ============
    
    talking_video = veo3_with_sadtalker(theme=theme, first_voice=first_voice, face2 =face2)  
    
    # ============ 멀티3 (sadtalker영상 실행 + 오디오제거작업 + whisper 모델 미리 로드) =============
        
    talking_no_voice,whisper = play_and_process_concurrently(talking_video)
    print(f"작업 완료! 무음 파일 경로: {talking_no_voice}")
    print(f"로드된 모델: {whisper}")
    
    # 이슈 : whisper 모델 로드까지 멀티프로세싱하면 데드락이 걸림. 오디오제거까지만 하고 whisper 모델 로드는 모델 로드 + 로딩 중 영상 재생으로 따로 함수 제작?
    
    
    