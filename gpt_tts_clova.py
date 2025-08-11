import os
import io
import sys
import wave
import argparse
import requests
import numpy as np
import soundfile as sf

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

def request_clova_tts(text: str, speaker: str, format_: str = "wav", speed: int = 0, pitch: int = 0, volume: int = 0, emotion: str | None = None, style: str | None = None) -> bytes:
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


def synthesize_to_file(text: str, out_path: str, speaker: str, speed: int = 0, pitch: int = 0, volume: int = 0, emotion: str | None = None, style: str | None = None, force_16k_wav: bool = True):
    raw = request_clova_tts(text=text, speaker=speaker, format_="wav", speed=speed, pitch=pitch, volume=volume, emotion=emotion, style=style)
    if force_16k_wav:
        raw = ensure_wav_16k(raw, input_format="wav")
    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    with open(out_path, "wb") as f:
        f.write(raw)
    return out_path


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
    out_path = r"C:\ARTECH_3\Image_Box\image2\voice\output.wav"
    path = synthesize_to_file(text=text, out_path=out_path, speaker=speaker, speed=args.speed, pitch=args.pitch, volume=args.volume, emotion=args.emotion, style=args.style, force_16k_wav=not args.no_force_16k)
    print(f"[OK] 저장 완료: {path}")

if __name__ == "__main__":
    main()
