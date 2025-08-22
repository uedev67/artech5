# 아트텍 5조 밀실사건전담반
부산대 2025 ARTECH 'AI와 인간'을 주제로 하는 5조 밀실사건전담반의 소프트웨어 파트입니다.
artech_test2.py를 읽어주세요. 콘텐츠 전반을 관리하는 핵심 파일입니다.


## 개발자 메모장

veo3_sadtalker, veo3_sam, sadtalker_worker 이렇게 3개 파일에서 초기 영상 처리를 담당합니다.
현재 whisper 모델 로드 멀티프로세싱시에, 데드락 이슈가 해결되지 않아서, (sadtalker + 오디오제거) 다음에 (whisper 로드 + 로딩중 영상 재생) 이렇게 수정 생각중입니다.

[ 테스트 바람 ]

multi3.py : sadtalker 영상 재생 + 소리 제거 작업( 해결 )

whisper.py : whisper 모델 로딩 + (로딩 중 영상 및 마이크 녹음 영상 재생)  (해결)

upscale.py를 veo3_sadtalker에 이식.

artech_test2.py : 70번 줄에 이슈 해결하기. 영상이 창 숨기기 형태로 재생됨.


[ 8.22 새로운 이슈와 해결 사항]

artech_test2.py 의 opening_with_button() 실행 에러 이슈 : 아두이노 버튼 파이시리얼 통신 + 영상 재생이 동시 실행 불가능 이슈가 있었습니다.

button_test.py 최상단 import sys 누락 이슈 (추가함) // interactive_player_worker.py를 opening_with_button()에서 cmd로 호출 -> args.path 인자로(opening_with_button에 인자로 받은 지정 영상) 영상을 vlc로 재생.


## 소개글
당신은 타임머신을 탈 기회를 얻었습니다. 타임머신 내부 버튼을 보면 층수가 있습니다. 큰 숫자를 누를수록 미래로 향합니다.
미래는 어떤 모습일까요? 기술의 고도화와 노동의 종말, 육체의 편안함, 사고과정의 퇴행, 혹은 인간의 욕심이 낳은 전쟁으로 피난처에서 모여 살 수도 있습니다.
선택지는 방문자분께 드리죠. 당신이 원하는 미래의 모습으로 떠나보세요. 그곳에선 또다른 내가 있을겁니다.



## upscale.py 사용 전 세팅(파워쉘 명령어)
git clone https://github.com/xinntao/Real-ESRGAN.git
cd Real-ESRGAN
pip install -r requirements.txt
pip install -e .
python scripts/download_models.py


## 환경 설정

아나콘다 파이썬 3.8 가상환경에서 실행하세요. requirements.txt를 참고해주세요. 

파이썬 3.8 환경을 사용하는 이유는 sadtalker가 3.8 기반으로 만들어졌기 때문입니다.

cuda 설정처럼 개인 PC마다 상이한 설정은 따로 바꿔서 설치해주셔야 합니다.


## 전체 흐름

artech_test2.py : 전체 흐름을 제어합니다. 각 유닛 코드 파일을 불러와서 사용합니다. 

### 멀티 프로세싱 방식

multiprocessing.set_start_method('spawn', force=True) 를 초기에 선언합니다. 

fork 대신에 spawn방식을 택한 이유는 sam, sadtalker의 라이브러리 충돌을 피하기 위해서입니다.

비록 속도는 fork방식보다 느리지만, 부모 프로세스 전체를 복제하여 충돌을 일으키지 않기 위해서 spawn 방식을 채택했습니다.


## 기능 설명

survey.py + survey_client.py : 방문자가 밀실 입장 전, 설문지를 작성합니다. 성별, 나이대, 테마를 선택합니다. 설문 결과는 타임머신 안에서의 콘텐츠에 영향을 줍니다.

button_test.py : 사용자로부터 원하는 미래 시기를 선택받습니다. 6층을 누르면 60대의 나를 만날 수 있습니다.

capture.py : 사용자의 얼굴 정면을 캡쳐합니다.

sam.py :  앞서 누른 버튼값 정보로 사용자의 얼굴을 노화시킵니다. 미래의 나를 만나는 초석이죠. sam 모델은 깃허브 오픈소스를 사용했습니다. 
https://github.com/yuval-alaluf/SAM 윈도우 환경에서 충돌이 발생할 수 있으니, Docker에서 컨테이너를 생성해서 사용하는 것을 권장합니다.

sadtalker.py : 노화된 얼굴 사진과 ai 목소리를 인자로 받아서 사람이 말하는 합성 영상을 제작합니다. sadtalker모델도 깃허브 오픈소스를 사용했습니다. https://github.com/OpenTalker/SadTalker

gpt.py : openai api키를 받아서 방문자와 대화하는 역할을 합니다. 설문에서 받은 테마를 적용하여 말해줍니다.

gpt_stt.py : 타임머신 안에는 마이크가 있습니다. 평행세계의 나와 대화하기 위한 수단이죠. 이 파일은 마이크로부터 방문자의 말을 받아서 gpt.py에게 넘겨줍니다.

gpt_clova_tts.py : 평행세계의 나의 목소리를 구현합니다. 100가지가 넘는 다양한 음성으로 성별, 나이대를 지정할 수 있습니다. 네이버 클로바 tts를 사용하였습니다.



## 사용된 기술들

멀티 프로세싱 + 로컬 임포트 : 동시에 여러 일을 해야하는 타이밍이 있습니다. 그중 하나가 veo3 + samtalker 실행입니다. 두 작업 모두 GPU를 사용합니다. 스레딩으로는 윈도우 6 핸들 에러가 발생합니다.
이를 방지하기 위해서 2가지 기술을 사용합니다.
1. 멀티 프로세싱 : veo3 영상 재생과 sam + sadtalker 작업을 분리된 2개의 독립 공간에서 실행하도록 합니다. 여기서 두 task의 충돌을 예방합니다. 실행 방식은 multiprocessing.set_start_method('spawn') 으로 정합니다.
2. 로컬 임포트 : from 파일명 import 함수명 은 보통 파일의 최상단에 선언합니다. sam,sadtalker를 최상단에 import하면 앞서 선언된 실행 방식과 충돌이 일어날 수 있습니다. 따라서 로컬 임포트하여 필요할 때만 실행되도록 하였습니다.



## 기타 정보
네이버 콘솔(몰라도 됩니다.)
https://console.ncloud.com/naver-service/application  
