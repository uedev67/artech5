# clova.py
# NAVER CLOVA TTS(Premium) - WAV(16k) 저장 유틸
# 입력: target_age, gender('남자'|'여자'), theme('사이버펑크'|'지하 커뮤니티'|'화성 이주'|'에코 스마트시티'), answer
# 출력: out_path에 WAV 저장
# speaker/speed/pitch 세트는 (1020/3040/5060/7080 × 남성/여성) 버킷과 theme 기반으로 "랜덤" 선택

import os
import io
import sys
import wave
import argparse
import requests
import numpy as np
import soundfile as sf
import random
from typing import Optional, List, Dict, Tuple

CLOVA_TTS_URL = "https://naveropenapi.apigw.ntruss.com/tts-premium/v1/tts"

# -----------------------
# Theme 정규화
# -----------------------
_CANONICAL_THEMES = {
    "사이버펑크": {"사이버펑크", "사펑", "cyberpunk"},
    "지하 커뮤니티": {"지하벙커 생존자 커뮤니티", "지하", "underground"},
    "화성 이주": {"화성 이주", "화성", "mars"},
    "에코 스마트시티": {"에코 스마트시티", "에코", "ecosmart", "eco smart city"},
}
_ALL_THEMES = set(_CANONICAL_THEMES.keys())

def _canon_theme(theme: str) -> str:
    t = (theme or "").strip().lower().replace(" ", "")
    for canon, aliases in _CANONICAL_THEMES.items():
        if t in {a.lower().replace(" ", "") for a in aliases}:
            return canon
    raise ValueError(f"지원하지 않는 theme: {theme} (허용: {sorted(_ALL_THEMES)})")

# -----------------------
# 1020/3040/5060/7080 × 남성/여성 버킷별 프리셋
# 각 항목: {"speaker": str, "speed": int, "pitch": int, "themes": List[str] | ['*']}
# -----------------------
SPEAKER_PRESETS: Dict[str, List[Dict]] = {
    # 7080 남성
    "7080남성": [
        {"speaker": "nwoosik",   "speed": 0,  "pitch": 2,  "themes": ["에코 스마트시티"]},
        {"speaker": "nwontak",   "speed": -1, "pitch": -1, "themes": ["화성 이주", "사이버펑크", "지하 커뮤니티"]},
        {"speaker": "nseungpyo", "speed": -1, "pitch": 0,  "themes": ["에코 스마트시티"]},
        {"speaker": "nkyungtae", "speed": -1, "pitch": 1,  "themes": ["지하 커뮤니티", "사이버펑크", "화성 이주"]},
        {"speaker": "nyoungil",   "speed": -1, "pitch": 0, "themes": ["사이버펑크","지하 커뮤니티","화성 이주"]},
    ],
    # 5060 남성
    "5060남성": [
        {"speaker": "nsiyoon",   "speed": -1, "pitch": 1,  "themes": ["사이버펑크", "화성 이주", "지하 커뮤니티"]},
        {"speaker": "nreview",   "speed": -1, "pitch": 2,  "themes": ["사이버펑크", "에코 스마트시티", "화성 이주","지하 커뮤니티"]},
        {"speaker": "nminsang",  "speed": -1, "pitch": -1, "themes": ["사이버펑크"]},
        {"speaker": "nraewon",   "speed": -1, "pitch": 1,  "themes": ["지하 커뮤니티"]},
        {"speaker": "nkitae",    "speed": -1, "pitch": 2,  "themes": ["에코 스마트시티"]},
    ],
    # 3040 남성
    "3040남성": [
        {"speaker": "nsiyoon",    "speed": -1, "pitch": -1, "themes": ["사이버펑크", "지하 커뮤니티"]},
        {"speaker": "nmovie",     "speed": -1, "pitch": 0, "themes": ["사이버펑크", "에코 스마트시티", "화성 이주","지하 커뮤니티"]},
        {"speaker": "jinho",      "speed": -1, "pitch": 0,  "themes": ["에코 스마트시티", "화성 이주"]},
        {"speaker": "njonghyeok", "speed": -1, "pitch": 2,  "themes": ["화성 이주"]},
        {"speaker": "nseonghoon", "speed": -1, "pitch": 0,  "themes": ["지하 커뮤니티", "화성 이주"]},
        {"speaker": "nkitae",     "speed": -1, "pitch": 1,  "themes": ["에코 스마트시티"]},
        {"speaker": "njihwan",    "speed": -1, "pitch": 0,  "themes": ["지하 커뮤니티"]},
    ],
    # 1020 남성
    "1020남성": [
        {"speaker": "nkyuwon",    "speed": -1, "pitch": 0,  "themes": ["사이버펑크", "에코 스마트시티", "화성 이주","지하 커뮤니티"]},
        {"speaker": "ngyeongjun", "speed": -1, "pitch": -1,  "themes": ["지하 커뮤니티", "사이버펑크", "화성 이주"]},
    ],
    # 7080 여성
    "7080여성": [
        {"speaker": "nsunhee", "speed": -1, "pitch": -2, "themes": ["사이버펑크", "에코 스마트시티", "화성 이주","지하 커뮤니티"]},
        {"speaker": "nheera",  "speed": -1, "pitch": 1,  "themes": ["사이버펑크", "에코 스마트시티", "화성 이주"]},
    ],
    # 5060 여성
    "5060여성": [
        {"speaker": "napple",   "speed": -1, "pitch": 1,  "themes": ["사이버펑크", "에코 스마트시티", "화성 이주"]},
        {"speaker": "nkyunglee","speed": 0, "pitch": 0,  "themes": ["지하 커뮤니티"]},
        {"speaker": "nheera",   "speed": -1, "pitch": 0,  "themes": ["사이버펑크", "에코 스마트시티", "화성 이주"]},
        {"speaker": "njiyun",   "speed": -1, "pitch": 1,  "themes": ["지하 커뮤니티"]},
        {"speaker": "njangj",   "speed": -1, "pitch": 1,  "themes": ["사이버펑크", "화성 이주"]},
    ],
    # 3040 여성
    "3040여성": [
        {"speaker": "napple",      "speed": -1, "pitch": 0,  "themes": ["사이버펑크", "에코 스마트시티", "화성 이주","지하 커뮤니티"]},
        {"speaker": "nkyunglee",   "speed": 0, "pitch": -1, "themes": ["지하 커뮤니티"]},
        {"speaker": "nheera",      "speed": -1, "pitch": -1, "themes": ["사이버펑크", "에코 스마트시티", "화성 이주"]},
        {"speaker": "njiyun",      "speed": -1, "pitch": 0,  "themes": ["지하 커뮤니티"]},
        {"speaker": "nsujin",      "speed": -1, "pitch": 0,  "themes": ["지하 커뮤니티", "사이버펑크"]},
        {"speaker": "njangj",      "speed": -1, "pitch": 0,  "themes": ["사이버펑크", "화성 이주"]},
    ],
    # 1020 여성
    "1020여성": [
        {"speaker": "nkyunglee","speed": -1, "pitch": -2, "themes": ["사이버펑크", "에코 스마트시티", "화성 이주","지하 커뮤니티"]},
        {"speaker": "nheera",   "speed": -1, "pitch": -2, "themes": ["사이버펑크", "에코 스마트시티", "화성 이주"]},
    ],
}

# -----------------------
# 유틸: 환경변수 로드
# -----------------------
def _env(var: str, default: str = "") -> str:
    v = os.getenv(var, default).strip()
    if not v:
        raise RuntimeError(f"환경변수 {var} 가 비어 있습니다.")
    return v

# -----------------------
# CLOVA API
# -----------------------
def request_clova_tts(
    text: str,
    speaker: str,
    format_: str = "wav",
    speed: int = 0,
    pitch: int = 0,
    volume: int = 0,
    emotion: Optional[str] = None,
    style: Optional[str] = None,
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

# -----------------------
# 오디오 변환 (모노 16kHz WAV)
# -----------------------
def ensure_wav_16k(audio_bytes: bytes, input_format: str) -> bytes:
    audio_buf = io.BytesIO(audio_bytes)
    try:
        data, sr = sf.read(audio_buf, dtype="float32", always_2d=True)
    except Exception as e:
        raise RuntimeError(f"오디오 로드 실패: {e}")

    # 모노화
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

    # float32 -> int16
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
    speed: int,
    pitch: int,
    volume: int = 0,
    emotion: Optional[str] = None,
    style: Optional[str] = None,
    force_16k_wav: bool = True,
) -> str:
    raw = request_clova_tts(
        text=text,
        speaker=speaker,
        format_="wav",
        speed=speed,
        pitch=pitch,
        volume=volume,
        emotion=emotion,
        style=style,
    )
    if force_16k_wav:
        raw = ensure_wav_16k(raw, input_format="wav")

    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    with open(out_path, "wb") as f:
        f.write(raw)
    return out_path

# -----------------------
# 버킷 결정 & 음성 세트 선택 (랜덤)
# -----------------------
def _bucket_from_age_gender(target_age: int, gender: str) -> str:
    if target_age < 30:
        decade = "1020"
    elif target_age < 50:
        decade = "3040"
    elif target_age < 70:
        decade = "5060"
    else:
        decade = "7080"
    sex = "남성" if gender == "남자" else "여성"
    return f"{decade}{sex}"

def select_voice(target_age: int, gender: str, theme: str) -> Tuple[str, int, int]:
    """
    반환: (speaker, speed, pitch)
    1) theme 일치 후보들 중 랜덤 선택
    2) 없으면 '*'(모든 테마) 후보들 중 랜덤 선택
    3) 없으면 ValueError
    """
    bucket = _bucket_from_age_gender(target_age, gender)
    canon_theme = _canon_theme(theme)
    presets = SPEAKER_PRESETS.get(bucket, [])
    if not presets:
        raise ValueError(f"버킷 {bucket} 에 대한 프리셋이 없습니다.")

    theme_matches = [p for p in presets if canon_theme in p["themes"]]
    if theme_matches:
        choice = random.choice(theme_matches)
        return choice["speaker"], choice["speed"], choice["pitch"]

    wildcard_matches = [p for p in presets if "*" in p["themes"]]
    if wildcard_matches:
        choice = random.choice(wildcard_matches)
        return choice["speaker"], choice["speed"], choice["pitch"]

    raise ValueError(f"버킷 {bucket}에서 theme '{canon_theme}'에 맞는 프리셋이 없습니다.")

# -----------------------
# 외부 진입점
# -----------------------



def clova(
    target_age: int,
    gender: str,
    theme: str,
    answer: str,
    out_path: str = r"C:\Artech5\Image_Box\clova_voice\voice.wav", 
    force_16k_wav: bool = True,
    volume: int = 0,
    emotion: Optional[str] = None,  # 기본 None 권장
    style: Optional[str] = None,    # 기본 None 권장
) -> str:
    speaker, speed, pitch = select_voice(target_age, gender, theme)
    # out_path가 폴더이거나 기본값일 때 speaker명.wav로 저장
    out_path_is_dir = False
    if out_path.endswith(os.sep) or (not os.path.splitext(out_path)[1]):
        out_path_is_dir = True
    if out_path_is_dir:
        os.makedirs(out_path, exist_ok=True)
        out_path = os.path.join(out_path, f"{speaker}.wav")
    else:
        # 파일명에 speaker가 없으면 자동 추가
        base, ext = os.path.splitext(out_path)
        if speaker not in os.path.basename(base):
            out_path = base + f"_{speaker}" + ext
    return synthesize_to_file(
        text=answer,
        out_path=out_path,
        speaker=speaker,
        speed=speed,
        pitch=pitch,
        volume=volume,
        emotion=emotion,
        style=style,
        force_16k_wav=force_16k_wav,
    )

# -----------------------
# CLI 테스트
# -----------------------
def main():
    """
    예) python clova.py --age 37 --gender 남자 --theme 사이버펑크 --text "안녕하세요"
    """
    parser = argparse.ArgumentParser(description="NAVER CLOVA TTS (Premium) → WAV 16k")
    parser.add_argument("--age", type=int, required=True, help="예: 25, 37, 58, 72")
    parser.add_argument("--gender", type=str, required=True, choices=["남자", "여자"])
    parser.add_argument("--theme", type=str, required=True, help="사이버펑크 | 지하 커뮤니티 | 화성 이주 | 에코 스마트시티")
    parser.add_argument("--text", type=str, required=True, help="합성할 문장")
    parser.add_argument("--outdir", type=str, default=r"C:\Artech5\Image_Box\clova_voice\voice.wav")  # 폴더만 지정
    parser.add_argument("--no-force-16k", action="store_true")
    parser.add_argument("--volume", type=int, default=0)
    parser.add_argument("--emotion", type=str, default=None)
    parser.add_argument("--style", type=str, default=None)

    args = parser.parse_args()
    try:
        # 먼저 어떤 speaker가 선택되는지 확인
        speaker, speed, pitch = select_voice(args.age, args.gender, args.theme)

        # 저장 경로에 speaker 포함
        os.makedirs(args.outdir, exist_ok=True)
        out_path = os.path.join(args.outdir, f"{speaker}.wav")

        path = clova(
            target_age=args.age,
            gender=args.gender,
            theme=args.theme,
            answer=args.text,
            out_path=out_path,
            force_16k_wav=not args.no_force_16k,
            volume=args.volume,
            emotion=args.emotion,
            style=args.style,
        )
        print(f"[OK] 저장 완료: {path}")
    except Exception as e:
        print(f"[ERROR] {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

