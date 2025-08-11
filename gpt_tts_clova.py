import os
import io
import sys
import wave
import argparse
import requests
import numpy as np
import soundfile as sf
from typing import Optional


CLOVA_TTS_URL = "https://naveropenapi.apigw.ntruss.com/tts-premium/v1/tts"


AGE_GENDER_SPEAKERS = {
    "소년": ["nhajun", "nwoof"],
    "소녀": ["ndain", "ngaram", "nmeow"],
    "청년남성": ["jinho", "ndaeseong", "ndonghyun", "ngyeongjun", "nian", "njaewook", "njihun", "njihwan", "njonghyeok", "njonghyun", "njooahn", "njoonyoung", "nkitae", "nkyungtae", "nkyuwon"],
    "청년여성": ["mijin", "nara", "nbora", "nes_c_mikyung", "neunyoung", "ngoeun", "nihyun", "njiwon", "njiyun", "nminseo", "nminyoung", "nyeji", "nyejin", "nyujin", "nyuna"],
    "중년남성": ["nes_c_kihyo", "nmovie", "nsangdo", "nseonghoon", "nseungpyo", "nsinu", "nsiyoon", "ntaejin", "nwontak", "nwoosik", "nyoungil"],
    "중년여성": ["dara_ang", "napple", "nara_call", "nes_c_sohyun", "neunseo", "nheera", "nsujin", "nsunhee", "nsunkyung", "ntiffany", "nyounghwa", "nyoungmi"]
}

def _env(var: str, default: str = "") -> str:
    v = os.getenv(var, default).strip()
    if not v:
        raise RuntimeError(f"환경변수 {var} 가 비어 있습니다.")
    return v


# 음성 파라미터는 여기서 설정
def request_clova_tts(
    text: str, speaker: str,
    format_: str = "wav",
    speed: int = 0,
    pitch: int = 0,
    volume: int = 0,
    emotion: Optional[str] = None,
    style: Optional[str] = None
) -> bytes:
    
    client_id = _env("NCP_CLOVA_TTS_CLIENT_ID")  # 환경 변수에 미리 입력
    client_secret = _env("NCP_CLOVA_TTS_CLIENT_SECRET")  # 환경 변수에 미리 입력
    headers = {
        "X-NCP-APIGW-API-KEY-ID": client_id,  # 여긴 건드리지 않기
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


# 오디오 변환 함수
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


# 받은 값을 tts에 넘겨주는 함수
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
    # 파라미터값을 받아서
    raw = request_clova_tts(text=text, speaker=speaker, format_="wav", speed=speed, pitch=pitch, volume=volume, emotion=emotion, style=style)
    if force_16k_wav:
        # 16k로 변환
        raw = ensure_wav_16k(raw, input_format="wav")
    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    with open(out_path, "wb") as f:
        f.write(raw)
    return out_path  # 저장된 파일 경로를 반환


# 실행 함수
def main():
    age_gender = input("나이대 및 성별을 입력하세요 (소년/소녀/청년남성/청년여성/중년남성/중년여성): ").strip()
    speakers = AGE_GENDER_SPEAKERS.get(age_gender)
    if not speakers:
        print("[ERROR] 잘못된 입력입니다.")
        sys.exit(1)
    import random
    speaker = random.choice(speakers)
    text = input("TTS로 변환할 문장을 입력하세요: ").strip()
    if not text:
        print("[ERROR] 변환할 문장이 없습니다.")
        sys.exit(1)
    parser = argparse.ArgumentParser(description="NAVER CLOVA TTS (Premium) → WAV 16k")
    parser.add_argument("--speed", type=int, default=0)
    parser.add_argument("--pitch", type=int, default=0)
    parser.add_argument("--volume", type=int, default=0)
    parser.add_argument("--emotion", default=None)
    parser.add_argument("--style", default=None)
    parser.add_argument("--no-force-16k", action="store_true")
    args = parser.parse_args()
    out_path = r"C:\Artech5\Image_Box\Image2\voice\voice.wav"
    
    # 음성 합성 및 저장함수 호출
    path = synthesize_to_file(text=text, out_path=out_path, speaker=speaker, speed=args.speed, pitch=args.pitch, volume=args.volume, emotion=args.emotion, style=args.style, force_16k_wav=not args.no_force_16k)
    print(f"[OK] 저장 완료: {path}")

if __name__ == "__main__":
    main()