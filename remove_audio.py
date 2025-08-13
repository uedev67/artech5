import os
import subprocess
from typing import Optional

def remove_audio(video_path: str, output_path: Optional[str] = None, ffmpeg_bin: str = "ffmpeg") -> str:

    if not os.path.isfile(video_path):
        raise FileNotFoundError(f"입력 파일을 찾을 수 없습니다: {video_path}")

    base, ext = os.path.splitext(video_path)
    if not output_path:
        # 확장자 유지 (원본과 같은 컨테이너로 리무깅)
        output_path = f"{base}_no_audio{ext if ext else '.mp4'}"

    # ffmpeg 명령:
    # -hide_banner : 불필요한 배너 숨김
    # -y           : 출력 덮어쓰기
    # -i           : 입력
    # -map 0       : 모든 스트림 포함
    # -map -0:a    : 모든 오디오 스트림 제외
    # -c copy      : 재인코딩 없이 스트림 복사 (화질 100% 유지)
    cmd = [
        ffmpeg_bin, "-hide_banner", "-y",
        "-i", video_path,
        "-map", "0", "-map", "-0:a",
        "-c", "copy",
        output_path
    ]

    try:  
        subprocess.run(cmd, check=True)  # 큰 로그를 캡처하지 않고 바로 표준 에러로 출력되게 함
    except FileNotFoundError:
        raise RuntimeError("ffmpeg이 시스템 PATH에 없거나 ffmpeg_bin 경로가 올바르지 않습니다.")
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"ffmpeg 실행 실패: {e}")

    return output_path

# 사용 예시
if __name__ == "__main__":
    talking_video = "sample.mp4"  # 원본 동영상 경로
    talking_no_voice = remove_audio(talking_video)  # 무음 동영상 경로 반환
    print("작업 완료")
