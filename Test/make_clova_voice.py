# clova.py  — 자동 배치 생성(--auto) 추가 버전

import os
import io
import sys
import wave
import argparse
import requests
import numpy as np
import random
import soundfile as sf
from typing import Optional

# =========================
# CLOVA 설정 (환경변수 필요)
# =========================
CLOVA_TTS_URL = "https://naveropenapi.apigw.ntruss.com/tts-premium/v1/tts"

def _env(var: str, default: str = "") -> str:
    v = os.getenv(var, default).strip()
    if not v:
        raise RuntimeError(f"환경변수 {var} 가 비어 있습니다.")
    return v

# =======================================
# 화자 풀(기존 로직 유지: 조건 내 랜덤 선택)
# =======================================
AGE_GENDER_SPEAKERS = {
    "소년": ["nhajun", "nwoof"],
    "소녀": ["ndain", "ngaram", "nmeow"],
    "청년남성": ["jinho", "ndaeseong", "ndonghyun", "ngyeongjun", "nian", "njaewook", "njihun", "njihwan", "njonghyeok", "njonghyun", "njooahn", "njoonyoung", "nkitae", "nkyungtae", "nkyuwon"],
    "청년여성": ["mijin", "nara", "nbora", "nes_c_mikyung", "neunyoung", "ngoeun", "nihyun", "njiwon", "njiyun", "nminseo", "nminyoung", "nyeji", "nyejin", "nyujin", "nyuna"],
    "중년남성": ["nes_c_kihyo", "nmovie", "nsangdo", "nseonghoon", "nseungpyo", "nsinu", "nsiyoon", "ntaejin", "nwontak", "nwoosik", "nyoungil"],
    "중년여성": ["dara_ang", "napple", "nara_call", "nes_c_sohyun", "neunseo", "nheera", "nsujin", "nsunhee", "nsunkyung", "ntiffany", "nyounghwa", "nyoungmi"]
}

# =========================
# CLOVA 요청 / 오디오 처리
# =========================
def request_clova_tts(
    text: str, speaker: str,
    format_: str = "wav",
    speed: int = 0,
    pitch: int = 0,
    volume: int = 0,
    emotion: Optional[str] = None,
    style: Optional[str] = None
) -> bytes:
    client_id = _env("NCP_CLOVA_TTS_CLIENT_ID")
    client_secret = _env("NCP_CLOVA_TTS_CLIENT_SECRET")
    headers = {
        "X-NCP-APIGW-API-KEY-ID": client_id,
        "X-NCP-APIGW-API-KEY": client_secret,
    }
    data = {
        "speaker": speaker,
        "speed": str(speed),
        "pitch": str(pitch),
        "volume": str(volume),
        "format": format_,
        "text": text,
    }
    if emotion:
        data["emotion"] = emotion
    if style:
        data["style"] = style

    resp = requests.post(CLOVA_TTS_URL, headers=headers, data=data, timeout=60)
    if resp.status_code != 200:
        raise RuntimeError(f"[CLOVA TTS] HTTP {resp.status_code} / body={resp.text}")
    return resp.content

def ensure_wav_16k(audio_bytes: bytes, input_format: str) -> bytes:
    audio_buf = io.BytesIO(audio_bytes)
    try:
        data, sr = sf.read(audio_buf, dtype="float32", always_2d=True)
    except Exception as e:
        raise RuntimeError(f"오디오 로드 실패: {e}")

    if data.shape[1] > 1:
        data = data.mean(axis=1, keepdims=True)
    else:
        data = data[:, 0:1]

    target_sr = 16000
    if sr != target_sr:
        duration = data.shape[0] / sr
        new_length = int(round(duration * target_sr))
        x_old = np.linspace(0.0, 1.0, num=data.shape[0], endpoint=False)
        x_new = np.linspace(0.0, 1.0, num=new_length, endpoint=False)
        data = np.interp(x_new, x_old, data[:, 0]).astype(np.float32).reshape(-1, 1)

    data_i16 = np.clip(data * 32767.0, -32768, 32767).astype(np.int16)
    out_buf = io.BytesIO()
    with wave.open(out_buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(target_sr)
        wf.writeframes(data_i16.tobytes())
    return out_buf.getvalue()

def synthesize_to_file(
    text: str,
    out_path: str,
    speaker: str,
    speed: int = 0,
    pitch: int = 0,
    volume: int = 0,
    emotion: Optional[str] = None,
    style: Optional[str] = None,
    force_16k_wav: bool = True
):
    raw = request_clova_tts(text=text, speaker=speaker, format_="wav",
                            speed=speed, pitch=pitch, volume=volume,
                            emotion=emotion, style=style)
    if force_16k_wav:
        raw = ensure_wav_16k(raw, input_format="wav")
    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    with open(out_path, "wb") as f:
        f.write(raw)
    return out_path

# =========================
# 외부에서 쓰는 간단 API
# =========================
def clova(target_age: int, gender: str, answer: str,
          out_path: str = r"C:\Artech5\Image_Box\Image2\voice\voice.wav",
          speed: int = 1, pitch: int = -1, volume: int = 1,
          emotion: Optional[str] = None, style: Optional[str] = None,
          force_16k_wav: bool = True) -> str:
    """
    target_age: 10, 20, 30, 50, 70 ...
    gender: '남자' / '여자'
    answer: 변환할 문장
    out_path: 저장 경로
    """
    # 성별/나이대 → 화자군 선택
    if target_age == 10:
        age_gender_key = "소년" if gender == "남자" else "소녀"
    elif target_age in (20, 30, 40):
        age_gender_key = "청년남성" if gender == "남자" else "청년여성"
    elif target_age >= 50:
        age_gender_key = "중년남성" if gender == "남자" else "중년여성"
    else:
        raise ValueError(f"지원하지 않는 나이대: {target_age}")

    speakers = AGE_GENDER_SPEAKERS.get(age_gender_key)
    if not speakers:
        raise ValueError(f"지원하지 않는 age_gender: {age_gender_key}")

    speaker = random.choice(speakers)
    return synthesize_to_file(
        text=answer,
        out_path=out_path,
        speaker=speaker,
        speed=speed,
        pitch=pitch,
        volume=volume,
        emotion=emotion,
        style=style,
        force_16k_wav=force_16k_wav
    )

# =========================
# 선정된 40개 대본(최종안)
# =========================
# 나이키: 10/20/30/50/70
SCRIPTS = {
    "사이버펑크": {
        "남자": {
            10: "야, 여긴 부산의 미래다. 처음 보는 네온, 어때?",
            20: "너, 아직 자유가 남아있나? 아니면 벌써 뺏겼나?",
            30: "네가 기억하는 2025년… 여기선 찾을 수 없어. 보고 싶지 않아?",
            50: "가상에서 나오면 공허만 남지. 넌 그걸 견딜 수 있겠나?",
            70: "마지막으로 느낀 따뜻함이 언제였더라… 너는 기억하나?"
        },
        "여자": {
            10: "여긴 위험해, 하지만 재밌어. 너도 느껴보고 싶어?",
            20: "자유를 찾다 보면 길을 잃게 돼. 넌 감당할 수 있겠어?",
            30: "여기선 사랑도 데이터야. 넌 진짜를 믿니?",
            50: "현실에서만 웃던 시절이 있었어. 넌 그 시절을 그리워하니?",
            70: "빛도, 소리도… 다 흐려졌구나. 네 눈에는 어떻게 보여?"
        }
    },
    "지하벙커 생존자 커뮤니티": {
        "남자": {
            10: "밖은 죽음, 안은 배급뿐이야. 넌 밖에 나가볼래?",
            20: "벽 너머엔 폐허뿐이야. 넌 거길 건널 수 있겠나?",
            30: "지상은 꿈, 여긴 현실이야. 넌 어느 쪽에 살고 싶나?",
            50: "폐허 속에서 살아남았지. 너도 버틸 수 있겠어?",
            70: "햇빛? 이제는 설화지. 넌 기억하니?"
        },
        "여자": {
            10: "밖엔 아무것도 없어. 정말 아무것도. 넌 믿어져?",
            20: "여긴 아직 안전해. 너도 여길 택하겠어?",
            30: "바깥은 더 이상 우리 세상이 아니야. 넌 돌아갈 수 있겠니?",
            50: "그땐 하늘이 있었지. 너는 본 적 있나?",
            70: "햇빛을 본 지, 반세기는 됐구나. 넌 그 빛을 기억해?"
        }
    },
    "에코 스마트시티": {
        "남자": {
            10: "너, 스스로 판단할 줄은 알지? AI에게 맡겨볼래?",
            20: "AI가 날도, 너도 관리하지. 그게 편하니?",
            30: "여긴 완벽해… 그래서 허무해. 넌 어떠니?",
            50: "모든 게 예상 가능해. 지루하지 않겠어?",
            70: "AI도 내 주름은 못 지워. 넌 어떻게 늙고 싶니?"
        },
        "여자": {
            10: "모든 게 준비돼, 하지만 심심해. 넌 재미있겠어?",
            20: "여긴 완벽해, 그래서 무서워. 넌 느껴본 적 있니?",
            30: "내 하루는 AI가 짜놨어. 넌 따라올래?",
            50: "도시는 깨끗하지만, 마음은 황폐해. 넌 어떻게 생각해?",
            70: "AI도 내 기억 속 2025는 못 바꾸지. 네 기억은 어때?"
        }
    },
    "화성 이주": {
        "남자": {
            10: "지구는 더 이상 우리 집이 아니야. 넌 떠날 수 있겠니?",
            20: "이주 티켓, 내 인생의 전부였지. 너도 원하나?",
            30: "여긴 안전하지만, 숨이 얕아. 넌 견딜 수 있겠어?",
            50: "화성 이주 티켓이 없었으면 난 이미 죽었을거야.",
            70: "여긴 마지막 정거장이야. 너는 어디서 끝내고 싶니?"
        },
        "여자": {
            10: "여긴 지구가 아니야, 붉은 사막이야. 넌 와보고 싶어?",
            20: "이 티켓이 목숨을 살렸어. 너라면 어떻게 할래?",
            30: "화성 이주 티켓이 없었으면 난 이미 죽었을거야.",
            50: "지구의 푸른 빛이 그립네. 넌 그 빛을 기억하니?",
            70: "이 붉은 땅에서 눈을 감겠지. 넌 어디서 잠들고 싶니?"
        }
    }
}


# 저장 폴더
OUT_DIR = r"C:\Artech5\Image_Box\clova_sample"

def age_label_to_int(age_label: str) -> int:
    """ '10대','20대','30~40대','50~60대','70~80대' → 10/20/30/50/70 """
    if age_label == "10대": return 10
    if age_label == "20대": return 20
    if age_label == "30~40대": return 30
    if age_label == "50~60대": return 50
    if age_label == "70~80대": return 70
    raise ValueError(f"지원하지 않는 나이 라벨: {age_label}")

AGE_BUCKETS = ["10대", "20대", "30~40대", "50~60대", "70~80대"]

def safe_filename(s: str) -> str:
    for ch in r'\/:*?"<>|':
        s = s.replace(ch, "_")
    return s.strip()

def build_outpath(theme: str, gender: str, age_label: str) -> str:
    base = f"{safe_filename(theme)}_{safe_filename(gender)}_{safe_filename(age_label)}.wav"
    return os.path.join(OUT_DIR, base)

def run_batch_for_selected(speed: int = 0, pitch: int = 0, volume: int = 0):
    os.makedirs(OUT_DIR, exist_ok=True)
    total = 0
    for theme, by_gender in SCRIPTS.items():
        for gender, by_age in by_gender.items():
            for age_label in AGE_BUCKETS:
                age_int = age_label_to_int(age_label)
                text = by_age[age_int]
                out_path = build_outpath(theme, gender, age_label)
                clova(
                    target_age=age_int,
                    gender=gender,
                    answer=text,
                    out_path=out_path,
                    speed=speed, pitch=pitch, volume=volume,
                    emotion=None, style=None,
                    force_16k_wav=True
                )
                print(f"[OK] {out_path}")
                total += 1
    print(f"\n[DONE] 총 {total}개 파일 생성 완료 → {OUT_DIR}")

# =========================
# CLI
# =========================
def main():
    
    run_batch_for_selected(speed=0, pitch=0, volume=0)
    
    # parser = argparse.ArgumentParser(description="NAVER CLOVA TTS (Premium)")
    # parser.add_argument("--auto", action="store_true", help="선정된 40개 대본을 일괄 생성")
    # parser.add_argument("--speed", type=int, default=0)
    # parser.add_argument("--pitch", type=int, default=0)
    # parser.add_argument("--volume", type=int, default=0)
    # parser.add_argument("--emotion", default=None)
    # parser.add_argument("--style", default=None)
    # parser.add_argument("--no-force-16k", action="store_true")
    # args = parser.parse_args()

    # if args.auto:
    #     # 배치 생성 모드
    #     run_batch_for_selected(speed=args.speed, pitch=args.pitch, volume=args.volume)
    #     return

    # # 기존 단일 입력 모드(그대로 유지)
    # age_gender = input("나이대 및 성별을 입력하세요 (소년/소녀/청년남성/청년여성/중년남성/중년여성): ").strip()
    # speakers = AGE_GENDER_SPEAKERS.get(age_gender)
    # if not speakers:
    #     print("[ERROR] 잘못된 입력입니다.")
    #     sys.exit(1)
    # speaker = random.choice(speakers)
    # text = input("TTS로 변환할 문장을 입력하세요: ").strip()
    # if not text:
    #     print("[ERROR] 변환할 문장이 없습니다.")
    #     sys.exit(1)

    # out_path = r"C:\Artech5\Image_Box\Image2\voice\voice.wav"
    # path = synthesize_to_file(
    #     text=text, out_path=out_path, speaker=speaker,
    #     speed=args.speed, pitch=args.pitch, volume=args.volume,
    #     emotion=args.emotion, style=args.style,
    #     force_16k_wav=not args.no_force_16k
    # )
    # print(f"[OK] 저장 완료: {path}")

if __name__ == "__main__":
    main()


