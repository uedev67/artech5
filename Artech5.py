# 모듈 임포트
from survey_client import run_survey_server
from button import button
from capture import capture
from sam import run_sam
from sadtalker import run_sadtalker




# 실행부
if __name__ == "__main__":
    
# =============== 관객 입장 전 ========================
    survey_result = run_survey_server()   # 성별, 테마 설문 결과를 수신
    print(f"[SERVER] 설문 결과: {survey_result}")


# ============= 관객 입장 후  =========================
    
    # 설문 결과에서 관객 나이대 받기(survey.py의 q3을 나이대 질문으로 변경, q4를 테마 질문으로 변경하기)
    survey_age = survey_result.get("q3")
    # 오프닝 멘트 쳐주면서 관객이 버튼을 누르도록 유도
    target_age = button(survey_age)
    print(f"[BUTTON] 선택된 target_age: {target_age}")
    
    # 신원 확인 : 카메라로 얼굴 캡쳐
    face1 = capture()
    
    
    # ============ 스레딩1 (veo3 + sam/sadtalker) : 함수화해서 실행부에서는 함수 호출만! ============
    
    # 시간 끌기 컨텐츠 : veo3 영상 출력 함수 ( 입력 파라미터는 설문에서 받은 q4, 리턴값은 없음)
    
    face2 = run_sam(target_age)

    # first_voice = get_first_voice()  survey_result의 q3,q4를 받아서 기생성된 음성 파일을 가져오는 부분.(아직 구현 안됨)
    talking_video = run_sadtalker(face2, first_voice)

    
    # ============ 스레딩2 (sadtalker영상 실행 + 영상에서 음성만 제외하고 따로 저장) =============
    
    # talking_video를 실행
    # 동시에 talking_video에서 음성만 삭제된 영상(talking_no_voice)을 따로 저장
    
    
    # ======================== ai와 관객의 상호 대화 파트 ==================================
    
    # 이미 스레딩2에서 ai가 먼저 말을 걸었음. 
    # 관객이 ai에게 답변(마이크 활성화)
    # ai 답변 음성 + talking_no_voice를 합친 영상을 출력
    # 관객이 다시 ai에게 답변
    # 시공간이 흔들리는 연출 + 돌아갈 시간이라며 관객에게 B1을 누르도록 유도
    