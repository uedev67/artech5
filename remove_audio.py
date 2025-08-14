import os
import subprocess
from typing import Optional


# 영상 재생 함수
def play_video_with_audio_ffplay(video_path: str, ffplay_bin: str = "ffplay", fullscreen: bool = False) -> subprocess.Popen:

    if not os.path.isfile(video_path):
        raise FileNotFoundError(f"입력 파일을 찾을 수 없습니다: {video_path}")

    cmd = [ffplay_bin, "-autoexit", "-loglevel", "error", video_path]
    if fullscreen:
        cmd.insert(2, "-fs")
    # 재생은 비차단으로 시작해서 Popen을 반환 (동시에 다른 작업 가능)
    return subprocess.Popen(cmd)


# 오디오 제거 함수
def remove_audio_ffmpeg(video_path: str, output_path: Optional[str] = None, ffmpeg_bin: str = "ffmpeg") -> subprocess.Popen:

    if not os.path.isfile(video_path):
        raise FileNotFoundError(f"입력 파일을 찾을 수 없습니다: {video_path}")

    base, ext = os.path.splitext(video_path)
    if not output_path:
        output_path = f"{base}_no_audio{ext if ext else '.mp4'}"

    cmd = [
        ffmpeg_bin, "-hide_banner", "-y",
        "-i", video_path,
        "-map", "0", "-map", "-0:a",
        "-c", "copy",
        output_path
    ]
    return subprocess.Popen(cmd)


# 스레딩2 : 영상 재생 + 오디오 제거
def play_and_remove_audio_concurrently(talking_video: str,
                                      ffplay_bin: str = "ffplay",
                                      ffmpeg_bin: str = "ffmpeg",
                                      fullscreen: bool = False) -> str:

    base, ext = os.path.splitext(talking_video)
    output_path = f"{base}_no_audio{ext if ext else '.mp4'}"

    # 동시 시작
    p_play = play_video_with_audio_ffplay(talking_video, ffplay_bin=ffplay_bin, fullscreen=fullscreen)
    p_strip = remove_audio_ffmpeg(talking_video, output_path=output_path, ffmpeg_bin=ffmpeg_bin)

    play_rc = p_play.wait()      # 재생 종료 대기
    strip_rc = p_strip.wait()    # 오디오 제거 후, 영상이 끝날 때까지 대기

    if play_rc != 0:
        print(f"[경고] 재생 프로세스 종료 코드: {play_rc}")
    if strip_rc != 0:
        raise RuntimeError(f"무음 변환 실패 (ffmpeg 종료 코드 {strip_rc})")

    return output_path   # 오디오 제거된 영상 경로 반환


# 사용 예시
if __name__ == "__main__":
    talking_video = "sample_4sec_with_audio.mp4"
    talking_no_voice = play_and_remove_audio_concurrently(
        talking_video,
        ffplay_bin="ffplay",   # PATH에 없다면 절대경로 지정 가능: "C:/ffmpeg/bin/ffplay.exe"
        ffmpeg_bin="ffmpeg",   # 예: "C:/ffmpeg/bin/ffmpeg.exe"
        fullscreen=False
    )
    print("무음 동영상 저장 경로:", talking_no_voice)
