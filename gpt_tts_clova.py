import os
import io
import sys
import wave
import argparse
import tempfile
import urllib.parse
import requests

# 선택) 16 kHz 보장을 위해 필요 시 리샘플링
#   - API에서 바로 wav(16k)가 안 오는 경우 대비
#   - soundfile+numpy 조합 (pip install soundfile numpy)
import numpy as np
import soundfile as sf

CLOVA_TTS_URL = "https://naveropenapi.apigw.ntruss.com/tts-premium/v1/tts"
# 참고: 프리미엄 엔드포인트와 헤더 키명
#  - X-NCP-APIGW-API-KEY-ID, X-NCP-APIGW-API-KEY
#  - form-data/body: speaker, text, format, speed, pitch, volume, emotion, style 등
# 출처: 예제/블로그에 동일 형식으로 기재. (문서 링크 접속 불가 시 대체 출처 참조)
#   https://manvscloud.com ... "tts-premium/v1/tts", 헤더 키명 예시
#   https://zel0rd.tistory.com/84  프리미엄/일반 엔드포인트와 헤더 키명

def _env(var: str, default: str = "") -> str:
    v = os.getenv(var, default).strip()
    if not v:
        raise RuntimeError(f"환경변수 {var} 가 비어 있습니다.")
    return v

def request_clova_tts(
    text: str,
    speaker: str = "nara",     # 예: nara, jinho, matt 등 (계정/상품에 따라 가용 스피커 상이)
    format_: str = "wav",      # wav/mp3/ogg 등
    speed: int = 0,            # -5 ~ 5
    pitch: int = 0,            # -5 ~ 5
    volume: int = 0,           # 0 ~ 5 (문서에 따라 범위 다를 수 있음)
    emotion: str | None = None,# 예: neutral/joy/sad/angry (스피커별 지원 여부 상이)
    style: str | None = None,  # 예: normal/friendly/calm 등 (옵션/스피커별 상이)
) -> bytes:
    """
    CLOVA Voice TTS Premium 호출. 바이너리 오디오 데이터를 반환.
    """
    client_id = _env("NCP_CLOVA_TTS_CLIENT_ID")
    client_secret = _env("NCP_CLOVA_TTS_CLIENT_SECRET")

    headers = {
        "X-NCP-APIGW-API-KEY-ID": client_id,
        "X-NCP-APIGW-API-KEY": client_secret,
    }

    # 주의: text는 URL 인코딩 or form data 로 안전하게 전달
    # 대부분의 공식 예제는 application/x-www-form-urlencoded 포맷을 사용
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

    # 요청
    resp = requests.post(
        CLOVA_TTS_URL,
        headers=headers,
        data=data,  # form-encoded
        timeout=60
    )
    if resp.status_code != 200:
        # API 에러 확인용
        raise RuntimeError(
            f"[CLOVA TTS] HTTP {resp.status_code} / body={resp.text}"
        )
    return resp.content  # 오디오 바이너리


def ensure_wav_16k(audio_bytes: bytes, input_format: str) -> bytes:
    """
    입력 포맷이 mp3/ogg/wav(8k/22k 등)일 수 있으므로,
    최종적으로 WAV 16k 모노 16-bit PCM 으로 변환해 돌려준다.
    """
    # soundfile 는 mp3 직접 읽기 어려움. 가급적 API format=wav 사용 권장.
    # 그래도 혹시 모를 케이스 대비해 다음 로직 시도:
    audio_buf = io.BytesIO(audio_bytes)

    # WAV일 가능성이 높으므로 우선 시도
    try:
        data, sr = sf.read(audio_buf, dtype="float32", always_2d=True)
    except Exception as e:
        raise RuntimeError(f"오디오 로드 실패: {e}")

    # 모노 믹스
    if data.shape[1] > 1:
        data = data.mean(axis=1, keepdims=True)
    else:
        data = data[:, 0:1]

    target_sr = 16000
    if sr != target_sr:
        # 간단한 리샘플링 (linear)
        # 고품질이 필요하면 librosa 또는 resampy 사용 가능
        # 여기서는 종속성 최소화를 위해 soundfile + numpy 로 간단 처리
        duration = data.shape[0] / sr
        new_length = int(round(duration * target_sr))
        x_old = np.linspace(0.0, 1.0, num=data.shape[0], endpoint=False)
        x_new = np.linspace(0.0, 1.0, num=new_length, endpoint=False)
        data = np.interp(x_new, x_old, data[:, 0]).astype(np.float32).reshape(-1, 1)

    # float32 -> int16
    data_i16 = np.clip(data * 32767.0, -32768, 32767).astype(np.int16)

    # WAV로 직렬화
    out_buf = io.BytesIO()
    with wave.open(out_buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)  # 16-bit
        wf.setframerate(target_sr)
        wf.writeframes(data_i16.tobytes())

    return out_buf.getvalue()


def synthesize_to_file(
    text: str,
    out_path: str,
    speaker: str = "nara",
    speed: int = 0,
    pitch: int = 0,
    volume: int = 0,
    emotion: str | None = None,
    style: str | None = None,
    force_16k_wav: bool = True,
):
    """
    텍스트를 TTS로 합성해서 out_path(WAV) 로 저장.
    force_16k_wav=True 이면 16kHz PCM WAV로 강제 변환.
    """
    # API는 wav/mp3 등 다양한 포맷 가능. 여기선 wav 요청을 기본으로.
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

    # 디렉토리 생성
    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    with open(out_path, "wb") as f:
        f.write(raw)
    return out_path


def main():
    parser = argparse.ArgumentParser(description="NAVER CLOVA TTS (Premium) → WAV 16k")
    parser.add_argument("--text", required=True, help="합성할 텍스트")
    parser.add_argument("--out", default="voice.wav", help="저장 경로(.wav)")
    parser.add_argument("--speaker", default="nara", help="스피커 ID (계정/상품별 지원 목록 상이)")
    parser.add_argument("--speed", type=int, default=0, help="-5~5")
    parser.add_argument("--pitch", type=int, default=0, help="-5~5")
    parser.add_argument("--volume", type=int, default=0, help="0~5")
    parser.add_argument("--emotion", default=None, help="예: neutral/joy/sad/angry (스피커별 지원)")
    parser.add_argument("--style", default=None, help="예: normal/friendly/calm 등 (스피커별 지원)")
    parser.add_argument("--no-force-16k", action="store_true", help="16kHz 강제 변환 비활성화")
    args = parser.parse_args()

    path = synthesize_to_file(
        text=args.text,
        out_path=args.out,
        speaker=args.speaker,
        speed=args.speed,
        pitch=args.pitch,
        volume=args.volume,
        emotion=args.emotion,
        style=args.style,
        force_16k_wav=not args.no_force_16k,
    )
    print(f"[OK] 저장 완료: {path}")


if __name__ == "__main__":
    main()
