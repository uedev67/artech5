# upscale_video_realesrgan.py (with audio mux)
import os
import subprocess
import sys
import uuid
import shutil
from typing import Optional

# 사용 편의를 위한 모델명 매핑
_MODEL_NAME_MAP = {
    "realesrgan-x4plus": "RealESRGAN_x4plus",
    "realesrgan_x4plus": "RealESRGAN_x4plus",
    "realesrnet-x4plus": "RealESRNet_x4plus",
    "realesrnet_x4plus": "RealESRNet_x4plus",
    "anime6b": "RealESRGAN_x4plus_anime_6B",
    "realesr-animevideov3": "realesr-animevideov3",
    "realesr_general_x4v3": "realesr-general-x4v3",
    "realesr-general-x4v3": "realesr-general-x4v3",
    "realesrgan_x2plus": "RealESRGAN_x2plus",
    "realesrgan-x2plus": "RealESRGAN_x2plus",
}

def _normalize_model_name(name: Optional[str]) -> str:
    if not name:
        return "RealESRGAN_x4plus"
    k = name.strip().lower().replace(" ", "")
    return _MODEL_NAME_MAP.get(k, name)

def _ffmpeg_bin() -> str:
    # 환경변수로 지정되어 있으면 우선 사용
    return os.environ.get("FFMPEG_BIN", "ffmpeg")

def mux_audio(upscaled_path: str,
              source_path: str,
              audio_bitrate: str = "192k",
              volume: Optional[float] = None) -> str:
    """
    업스케일된 영상(upscaled_path)에 source_path의 오디오를 붙여 새 파일 반환.
    실패하면 upscaled_path 그대로 반환.
    """
    if not os.path.exists(upscaled_path) or not os.path.exists(source_path):
        return upscaled_path

    out_with_audio = os.path.splitext(upscaled_path)[0] + "_withaudio.mp4"
    tmp_out = os.path.join(os.path.dirname(upscaled_path), f"._mux_{uuid.uuid4().hex}.mp4")

    cmd = [
        _ffmpeg_bin(), "-y",
        "-i", upscaled_path,        # 0: 비디오
        "-i", source_path,          # 1: 오디오 소스
        "-map", "0:v:0",
        "-map", "1:a:0",
        "-c:v", "copy",
        "-c:a", "aac", "-b:a", audio_bitrate,
        "-shortest",
    ]
    if volume is not None:
        cmd.extend(["-filter:a", f"volume={volume}"])
    cmd.append(tmp_out)

    try:
        proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if proc.returncode != 0 or not os.path.exists(tmp_out):
            # 원본에 오디오가 없거나 ffmpeg 미설치/실패 시 무음 영상 유지
            return upscaled_path
        # 목적지에 같으면 교체
        if os.path.exists(out_with_audio):
            try:
                os.remove(out_with_audio)
            except Exception:
                pass
        os.replace(tmp_out, out_with_audio)
        return out_with_audio
    except Exception:
        # ffmpeg 자체가 없거나 실행 실패
        return upscaled_path
    finally:
        try:
            if os.path.exists(tmp_out):
                os.remove(tmp_out)
        except Exception:
            pass

def upscale_video_realesrgan(
    input_path: str,
    output_path: Optional[str] = None,
    realesrgan_dir: str = r"C:\ARTECH_3\Real-ESRGAN",
    model_name: str = "RealESRGAN_x4plus",
    scale: int = 4,
    fp16: bool = True,     # True면 half(기본). False면 --fp32 강제.
    tile: int = 0,         # VRAM 부족 시 256/512 권장
    keep_audio: bool = True,      # ✅ 업스케일 후 오디오 자동 합치기
    audio_bitrate: str = "192k",  # 오디오 비트레이트
    audio_volume: Optional[float] = None  # 1.0=그대로, 1.3=+3dB 정도
) -> str:
    """
    Real-ESRGAN의 'inference_realesrgan_video.py'를 subprocess로 호출해 동영상을 업스케일.
    """
    if not os.path.exists(input_path):
        raise FileNotFoundError(input_path)

    in_dir  = os.path.dirname(input_path) or "."
    in_name = os.path.splitext(os.path.basename(input_path))[0]

    if output_path is None:
        output_path = os.path.join(in_dir, f"{in_name}_x{scale}.mp4")

    # 같은 이름 파일이 이미 열려 있으면 Permission denied가 납니다.
    # 안전하게 임시 파일로 먼저 출력하고, 완료 후 교체합니다.
    out_dir = os.path.dirname(output_path) or "."
    os.makedirs(out_dir, exist_ok=True)

    # 실행 전 기존 출력 파일이 있으면 지우기(덮어쓰기 방지)
    if os.path.exists(output_path):
        try:
            os.remove(output_path)
        except PermissionError:
            # 탐색기/플레이어가 잡고 있을 수 있으니 다른 이름으로 교체 fallback
            base, ext = os.path.splitext(output_path)
            output_path = f"{base}_{uuid.uuid4().hex[:6]}{ext}"

    tmp_out = os.path.join(out_dir, f"._tmp_{uuid.uuid4().hex}.mp4")

    script = os.path.join(realesrgan_dir, "inference_realesrgan_video.py")
    if not os.path.exists(script):
        raise FileNotFoundError(f"스크립트를 찾을 수 없음: {script}")

    model_name = _normalize_model_name(model_name)

    # Windows에서 콘솔창 숨김
    creationflags = 0x08000000 if sys.platform.startswith("win") else 0  # CREATE_NO_WINDOW

    # 현재 버전 스크립트는 -o에 '출력 파일 경로'를 직접 받습니다.
    # file_url 초기화 문제를 피하기 위해 --extract_frame_first 사용.
    cmd = [
        sys.executable, script,
        "-n", model_name,
        "-i", input_path,
        "-o", tmp_out,
        "-s", str(scale),
        "--num_process_per_gpu", "1",
        "-t", str(tile),
        "--extract_frame_first",      # file_url 안전
        "--ext", "png",               # 프레임 확장자
    ]

    # fp16=True(기본 half)면 옵션 없음. fp16=False면 float32 강제.
    if not fp16:
        cmd.append("--fp32")

    proc = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        creationflags=creationflags,
        text=True
    )

    if proc.returncode != 0 or not os.path.exists(tmp_out):
        raise RuntimeError(f"Real-ESRGAN 실패\nSTDERR:\n{proc.stderr}")

    # 완료 후 원하는 파일명으로 이동(동일 드라이브면 rename, 아니면 copy)
    try:
        if os.path.exists(output_path):
            os.remove(output_path)
        os.replace(tmp_out, output_path)
    except Exception:
        shutil.copy2(tmp_out, output_path)
        try:
            os.remove(tmp_out)
        except Exception:
            pass

    # 🔊 업스케일 후 오디오 합치기
    if keep_audio:
        final_path = mux_audio(output_path, input_path,
                               audio_bitrate=audio_bitrate,
                               volume=audio_volume)
        return final_path

    return output_path


# ===== 사용 예시 =====
if __name__ == "__main__":
    src = r"C:\ARTECH_3\Image_Box\test_video.mp4"
    out = upscale_video_realesrgan(
        input_path=src,
        output_path=r"C:\ARTECH_3\Image_Box\test_video_x4.mp4",
        realesrgan_dir=r"C:\ARTECH_3\Real-ESRGAN",
        model_name="realesr-general-x4v3",
        scale=4,
        fp16=True,
        tile=256,
        keep_audio=True,          # ✅ 오디오 합치기 ON
        audio_bitrate="192k",
        audio_volume=None         # 필요하면 1.2 등으로 볼륨 증폭
    )
    print("업스케일 완료:", out)
