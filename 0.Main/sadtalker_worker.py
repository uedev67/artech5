# sadtalker_worker.py

import argparse
import os
import sys
import traceback

# [수정] face_path 인자를 받도록 함수 정의 변경
def run_isolated_sadtalker(driven_audio, result_dir, face_path):
    """
    외부에서 전달받은 얼굴 이미지(face_path)로 SadTalker를 실행하는 함수.
    """
    print(f"[WORKER] 외부로부터 얼굴 이미지를 전달받아 SadTalker를 실행합니다.")
    print(f"   - 사용할 이미지: {face_path}")

    # 파일이 실제로 존재하는지 확인
    if not os.path.exists(face_path):
        print(f"[WORKER_ERROR] 지정된 얼굴 이미지 파일을 찾을 수 없습니다: {face_path}", file=sys.stderr)
        return None

    # SadTalker 실행
    result_path = None
    try:
        from sadtalker import run_sadtalker
        print("[WORKER_SADTALKER] 비디오 생성을 시작합니다.")
        result_path = run_sadtalker(
            face_path=face_path, # [수정] 전달받은 face_path 경로를 사용
            audio_path=driven_audio,
            result_dir=result_dir,
            size=256,
            preprocess="crop",
            verbose=True
        )
        if result_path:
            print(f"[WORKER_SADTALKER] 비디오 생성 완료: {result_path}")
        else:
            print("[WORKER_SADTALKER] 비디오 생성 실패.", file=sys.stderr)
    except Exception as e:
        print(f"[WORKER_SADTALKER] SadTalker 실행 중 오류 발생: {e}", file=sys.stderr)
        return None

    return result_path


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run SadTalker in an isolated process.")
    # [수정] 사용할 얼굴 이미지 경로를 인자로 받도록 --face_path 추가
    parser.add_argument("--audio", type=str, required=True, help="Path to the driven audio file.")
    parser.add_argument("--result_dir", type=str, required=True, help="Directory to save the result video.")
    parser.add_argument("--face_path", type=str, required=True, help="Path to the face image for SadTalker.")
    
    args = parser.parse_args()

    # [수정] 변경된 인자에 맞게 함수 호출
    final_video_path = run_isolated_sadtalker(args.audio, args.result_dir, args.face_path)

    if final_video_path:
        print(final_video_path)