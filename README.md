# 아트텍 5조 밀실사건전담반
부산대 2025 ARTECH 'AI와 인간'을 주제로 대상(1등)을 받은 5조 밀실사건전담반의 소프트웨어 파트입니다.

실행부는 Main 폴더에 있습니다.

작업 기간 : 2025.06.29 ~ 2025.08.31
<details>
  <summary> 클릭하시면 사진이 펼쳐집니다.</summary>
  <p align="center">
    <img width="1400" height="1050" alt="image" src="https://github.com/user-attachments/assets/0d776055-443f-48db-a2eb-f008aafbc5ff" />
    <img width="1050" height="1400" alt="image" src="https://github.com/user-attachments/assets/523a6401-35a8-442e-935d-7748b38a244b" />
  </p>
</details>


## 관객 안내 매뉴얼

[콘텐츠 시작 전 세팅]
관객에게 노트북으로 설문을 시킵니다. 그리고 관객과 함께 밀실에 들어갑니다.

B1, 빛 들어온 버튼, 문닫힘 버튼 총 3개 버튼을 눌러서 리셋해줍니다.

capture.py 를 실행하여 관객 얼굴 정면 사진을 찍습니다.

main_process.py 를 실행합니다.(그리고 노트북에서 설문 결과를 제출해줍니다.) 검은 화면이 뜨면 세팅이 끝났습니다.

이제 관객이 문닫힘버튼을 누르면 콘텐츠가 자동 진행됩니다.

## 시연 영상 링크

아래 유튜브 링크를 방문하여 전체 시연 영상을 확인해보세요.


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


## 전체 흐름 및 기술적 해결결

01_sequence.py : 전체 흐름을 제어합니다. 각 유닛 코드 파일을 불러와서 사용합니다. 

### 멀티 프로세싱 방식

multiprocessing.set_start_method('spawn', force=True) 를 초기에 선언합니다. 

fork 대신에 spawn방식을 택한 이유는 sam, sadtalker의 라이브러리 충돌을 피하기 위해서입니다.

비록 속도는 fork방식보다 느리지만, 부모 프로세스 전체를 복제하여 충돌을 일으키지 않기 위해서 spawn 방식을 채택했습니다.

### 관객 입장 전

준비물은 노트북과 데스크톱 pc입니다. 노트북은 밀실 입장 전 관객이 설문조사하는 용도입니다. 데스크톱 pc에서는 설문 결과를 받아서 이를 토대로 개인 맞춤화된 컨텐츠를 진행합니다.

실행 순서는 다음과 같습니다.

노트북에서 survey.py를 실행합니다. 4가지 질문( 얼굴 사진 사용 여부 / 성별 / 나이대 / 원하는 미래세계 테마 )에 대한 답을 받아서 제출합니다.

survey.py에서는 flask 웹 서버가 0.0.0.0:5000 포트를 열어서 클라이언트 요청을 기다립니다. 같은 와이파이에 연결된 survey_client.py는 JSON 형식 데이터(답장)를 받으면 return "OK", 200 를 합니다.

### 관객 입장 후 

메인 콘텐츠가 진행됩니다.

### 멀티 1 : 오프닝 영상 + 엘리베이터 버튼 입력(아두이노 시리얼 통신)

기본적인 구조는 다음과 같습니다.

opening_with_button() 에서 subprocess.Popen로 command를 실행 

-> 적절한 cmd로 interactive_player_worker.py 를 별도의 프로세스로 실행

컴퓨터는 artech_test2.py(메인 실행 파일)로부터 interactive_player_worker.py(오프닝 + 버튼 입력 대기)를 안전하게 분리합니다.

이후 threading을 사용하여 interactive_player_worker.py 내에서 오프닝 영상 재생과 버튼 입력 대기를 동시에 진행합니다.

버튼이 눌려서 값을 받으면 재생 중인 영상을 강제로 종료시키고 다음 단계로 넘어갑니다.

이러한 구조를 사용하는 이유는, 파이썬의 Global Interpreter Lock 으로 인한 블로킹 현상 때문입니다.(하나의 작업이 끝날 때까지 나머지 작업들이 무한 대기)

멀티 프로세싱 대신에 스레딩을 사용한 이유는 아두이노 시리얼 통신은 단순 Input/Output 작업이기 때문입니다. 대부분이 통신 대기 시간이므로 자원을 공유해도 큰 문제가 없습니다.


### 정보 처리 : 첫 대사 결정 + 얼굴 사진 촬영

survey.py 에서 받은 gender, theme 값과 button_test.py(아두이노 통신)에서 받은 target_age 값으로 ai 목소리를 결정합니다. 예를 들어 '남자' 관객이 '사이버펑크' 테마로 본인의 '60대'의 모습을 원한다면, 그에 맞는 목소리를 get_first_voice.py로 결정해줍니다.

그리고 capture.py에서 받은 face1값은 추후 sam, sadtalker에서 이미지 처리에 사용됩니다.


### 멀티 2 : veo3 intro + sam

멀티 프로세싱과 큐를 통해 google veo3 ai 영상 재생과 sam(face1 관객 얼굴 사진을 타깃 나이대로 노화) 작업을 동시에 진행합니다.

멀티 프로세싱(multi processing) : 2개의 다른 프로세스로 쪼개어서 cpu 자원을 각각 할당받습니다. cpu는 영상 재생(A)과 sam 모델(B)을 A,B,A,B... 순서대로 쪼개어 처리하나, 그 속도가 매우 빨라서 인간은 이를 멀티 태스킹으로 인식합니다.

큐(Queue) : sam 모델은 독립된 프로세스라 메인 프로세스(artech_test2.py)가 이를 확인하지 못합니다. 이때, sam의 반환 결과를 Queue에 넣어주면 메인 프로세스가 종료 시점을 판단할 수 있습니다.

### 멀티 3 : veo3 main + sadtalker

sadtalker_worker.py로 독립적인 프로세스를 만들어서 실행합니다. 영상 재생도 멀티 프로세싱으로 동시에 진행합니다.

멀티 프로세싱을 담당하는 코드는 다음과 같습니다.

video_process = multiprocessing.Process(target=play_veo3, args=(theme,)) 

video_process.start()

sadtalker_proc = subprocess.Popen(...)

### 멀티 4 : 영상 실행 + 오디오 제거 작업

동일하게 멀티 프로세싱을 사용합니다.

제작된 sadtalker(인간 ai 말하는 동영상) 동영상에서 오디오만 제거하는 작업을 하는 이유는 다음과 같습니다.

1. 뒤에 나올 인간 - AI 상호 대화 파트에서 매 대화마다 sadtalker 모델을 실행하면 GPU 연산의 한계로 인해 실시간 상호작용이 불가능합니다.

2. 따라서 오디오만 제거한 영상을 재활용합니다. 매 대화마다 응답 + 오디오만 생성하는 작업은 6초 이내로 가능하므로 실시간 상호작용이 가능합니다.

### 멀티 5 : 대화부 -  관객의 질문과 AI 응답 처리

관객과 ai가 실시간 대화를 하는 부분입니다. 멀티 5는 ai가 관객의 질문에 답을 하는 부분입니다.

voice = get_answer(user_input,theme,target_age,gender) 에서 모니터에 영상 재생 + 응답 생성을 동시에 진행합니다.

모니터에 영상을 재생하는 이유는 응답 생성에 6초 이내의 시간이 소요되기 때문에 관객의 시각적 주의를 다른 영상으로 끌 필요가 있습니다.

영상 내용은 '평행세계의 나와 통신하는데 약간의 시간이 걸림'을 표현하는데 초점을 맞췄습니다.

get_answer()함수는 마이크로 user_input(관객 질문)을 받아서, target_age,gender로 알맞은 목소리를 매핑 후, theme에 따라서 각 테마에 특화된 응답을 생성하는 함수입니다.

clova.py와 gpt.py의 기능이 통합된 함수입니다.

### 멀티 5 : 대화부 - AI 응답 표출 및 대화 반복

IsReplySuccess = AI_reply(talking_no_voice, voice) 에서 talking_no_voice(영상 부분만 재활용) + voice(새로 생성한 오디오 ai 응답)을 조합하여 모니터에 재생합니다.

결과값으로 true를 반환하면 다음 줄에서 한 번 더 mic_listen() 과 get_answer()을 실행하여 관객이 ai와 대화를 주고받을 수 있게끔 설계하였습니다.


## 기능 설명

survey.py + survey_client.py : 방문자가 밀실 입장 전, 설문지를 작성합니다. 성별, 나이대, 테마를 선택합니다. 설문 결과는 타임머신 안에서의 콘텐츠에 영향을 줍니다.

button_test.py : 사용자로부터 원하는 미래 시기를 선택받습니다. 6층을 누르면 60대의 나를 만날 수 있습니다.

capture.py : 사용자의 얼굴 정면을 캡쳐합니다.

sam.py :  앞서 누른 버튼값 정보로 사용자의 얼굴을 노화시킵니다. 미래의 나를 만나는 초석이죠. sam 모델은 깃허브 오픈소스를 사용했습니다. 
https://github.com/yuval-alaluf/SAM 윈도우 환경에서 충돌이 발생할 수 있으니, Docker에서 컨테이너를 생성해서 사용하는 것을 권장합니다.

sadtalker.py : 노화된 얼굴 사진과 ai 목소리를 인자로 받아서 사람이 말하는 합성 영상을 제작합니다. sadtalker모델도 깃허브 오픈소스를 사용했습니다. https://github.com/OpenTalker/SadTalker

gpt.py : openai api키를 받아서 방문자와 대화하는 역할을 합니다. 설문에서 받은 테마를 적용하여 말해줍니다.

multi3.py : 영상에서 오디오 제거 작업을 실시합니다. artech_test2.py에서 video_playback_worker() 함수 안에서 로컬 임포트로 사용됩니다.

stt_listen.py : 타임머신 안에는 마이크가 있습니다. 평행세계의 나와 대화하기 위한 수단이죠. 이 파일은 마이크로부터 방문자의 말을 받아서 gpt.py에게 넘겨줍니다.

gpt_clova_tts.py : 평행세계의 나의 목소리를 구현합니다. 100가지가 넘는 다양한 음성으로 성별, 나이대를 지정할 수 있습니다. 네이버 클로바 tts를 사용하였습니다.



## 사용된 기술들

멀티 프로세싱 + 로컬 임포트 : 동시에 여러 일을 해야하는 타이밍이 있습니다. 그중 하나가 veo3 + samtalker 실행입니다. 두 작업 모두 GPU를 사용합니다. 스레딩으로는 윈도우 6 핸들 에러가 발생합니다.
이를 방지하기 위해서 2가지 기술을 사용합니다.
1. 멀티 프로세싱 : veo3 영상 재생과 sam + sadtalker 작업을 분리된 2개의 독립 공간에서 실행하도록 합니다. 여기서 두 task의 충돌을 예방합니다. 실행 방식은 multiprocessing.set_start_method('spawn') 으로 정합니다.
2. 로컬 임포트 : from 파일명 import 함수명 은 보통 파일의 최상단에 선언합니다. sam,sadtalker를 최상단에 import하면 앞서 선언된 실행 방식과 충돌이 일어날 수 있습니다. 따라서 로컬 임포트하여 필요할 때만 실행되도록 하였습니다.



## 기타 정보
네이버 콘솔(몰라도 됩니다.)
https://console.ncloud.com/naver-service/application  
