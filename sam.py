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


# 1️⃣ 로컬 이미지 → base64 인코딩
image_path = r"C:\ARTECH_3\Image_Box\image1\face_1.jpg"
with open(image_path, "rb") as f:
    encoded_image = base64.b64encode(f.read()).decode("utf-8")


# 2️⃣ 원하는 나이대 (None이면 default → GIF 출력)
target_age = 65  # 예: 65세 모습만 보고 싶다면


# SAM API 요청용 입력 JSON
input_data = {
    "image": f"data:image/jpeg;base64,{encoded_image}"
}
if target_age:
    input_data["target_age"] = target_age  # 나이대 추가


# 3️⃣ SAM API 호출
response = requests.post(
    "http://localhost:5000/predictions",
    json={"input": input_data}
)

result = response.json()
print(result)  # 구조 확인용


# 4️⃣ JSON 안에서 base64 이미지 찾기
final_base64 = find_base64(result)


if final_base64:
    save_dir = r"C:\ARTECH_3\Image_Box\image2"
    os.makedirs(save_dir, exist_ok=True)
    # age 값이 있으면 파일명에 포함
    filename = f"image_age_{target_age}.jpg" if target_age else "image_age_progression.gif"
    save_path = os.path.join(save_dir, filename)

    # base64 → 바이너리로 디코딩 후 저장
    with open(save_path, "wb") as f:
        f.write(base64.b64decode(final_base64.split(",")[-1]))

    print(f"✅ 결과 이미지 저장 완료: {save_path}")
else:
    print("❌ SAM 응답에서 base64 이미지를 찾지 못했습니다.")
