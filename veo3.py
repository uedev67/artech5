import cv2

import subprocess

def play_veo3(theme=None):
    # 테마별 영상 경로 매핑
    theme_video_map = {
        "지하벙커 생존자 커뮤니티": r"C:\Artech5\Image_Box\veo3\eco_smart.mp4",
        "사이버펑크": r"C:\Artech5\Image_Box\veo3\eco_smart.mp4",
        "에코 스마트시티": r"C:\Artech5\Image_Box\veo3\eco_smart.mp4",
        "화성 이주": r"C:\Artech5\Image_Box\veo3\eco_smart.mp4",
    }
    video_path = theme_video_map.get(theme, r"C:\Artech5\Image_Box\veo3\eco_smart.mp4")
    print(f"[INFO] 선택된 테마: {theme}, 영상 경로: {video_path}")
    try:
        subprocess.run([
            "ffplay", "-autoexit", "-fs", video_path
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception as e:
        print(f"[ERROR] ffplay 영상 실행 실패: {e}")

if __name__ == "__main__":
    video_path = r"C:\Artech5\Image_Box\veo3\eco_smart.mp4"
    play_veo3(theme)
