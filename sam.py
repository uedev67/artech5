
import requests
import base64
import os

def find_base64(data):
    """응답 JSON 안에서 base64 이미지 문자열을 재귀적으로 찾아내기"""
    if isinstance(data, str):
        if data.startswith("data:image"):
            return data
    elif isinstance(data, dict):
        for v in data.values():
            found = find_base64(v)
            if found:
                return found
    elif isinstance(data, list):
        for item in data:
            found = find_base64(item)
            if found:
                return found
    return None

# 얼굴 나이 변환 함수
def run_sam(target_age, face_path=None):
    """
    target_age: 변환할 나이 (예: 65)
    face_path: 입력 얼굴 이미지 경로 (None이면 기본값 사용)
    return: 결과 이미지 경로 (성공 시), 실패 시 None
    """
    if face_path is None:
        face_path = r"C:\ARTECH5\Image_Box\image1\face_1.jpg"
    # 1. 로컬 이미지 → base64 인코딩
    try:
        with open(face_path, "rb") as f:
            encoded_image = base64.b64encode(f.read()).decode("utf-8")
    except Exception as e:
        print(f"[ERROR] 얼굴 이미지 파일 열기 실패: {e}")
        return None

    # 2. SAM API 요청용 입력 JSON
    input_data = {
        "image": f"data:image/jpeg;base64,{encoded_image}"
    }
    if target_age:
        input_data["target_age"] = target_age

    # 3. SAM API 호출 (수정된 버전)
    try:
        response = requests.post(
            "http://localhost:5000/predictions",
            json={"input": input_data},
            timeout=300  # 선택 사항: 응답이 길어질 경우를 대비해 타임아웃 설정
        )
        # 요청이 성공했는지 상태 코드로 먼저 확인 (200 = 성공)
        if response.status_code == 200:
            result = response.json()
        else:
            # 실패 시, 상태 코드와 서버가 보낸 실제 응답 내용을 출력
            print(f"❌ SAM API 요청 실패 (HTTP Status: {response.status_code})")
            print("👇 서버 응답 내용:")
            print(response.text) # 서버의 에러 로그(HTML 또는 텍스트)를 그대로 출력
            return None

    except requests.exceptions.RequestException as e:
        print(f"[ERROR] SAM API 네트워크 연결 실패: {e}")
        return None
    except ValueError as e: # response.json() 실패 시 발생하는 에러
        print(f"[ERROR] 서버 응답이 올바른 JSON 형식이 아닙니다: {e}")
        print("👇 서버 응답 내용:")
        print(response.text)
        return None


    # 4. JSON 안에서 base64 이미지 찾기
    final_base64 = find_base64(result)
    if final_base64:
        save_dir = r"C:\ARTECH5\Image_Box\image2"
        os.makedirs(save_dir, exist_ok=True)
        filename = f"image_age_{target_age}.jpg" if target_age else "image_age_progression.gif"
        save_path = os.path.join(save_dir, filename)
        try:
            with open(save_path, "wb") as f:
                f.write(base64.b64decode(final_base64.split(",")[-1]))
            print(f"✅ 결과 이미지 저장 완료: {save_path}")
            return save_path
        except Exception as e:
            print(f"[ERROR] 결과 이미지 저장 실패: {e}")
            return None
    else:
        print("❌ SAM 응답에서 base64 이미지를 찾지 못했습니다.")
        return None


if __name__ == "__main__":
    path = r"C:\Artech5\Image_Box\Image1\face_1.jpg"
    run_sam(50,path)