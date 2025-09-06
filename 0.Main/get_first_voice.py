
from typing import Dict, Tuple, Optional


THEME_KEYMAP: Dict[str, str] = {
    "지하벙커 생존자 커뮤니티": "bunker",
    "사이버펑크": "cyberpunk",
    "에코 스마트시티": "eco_city",
    "화성 이주": "mars",
}


def normalize_gender(gender: str) -> str:
    if gender not in ("남자", "여자"):
        raise ValueError(f"Unknown gender: {gender}")
    return "male" if gender == "남자" else "female"

def normalize_theme(theme: str) -> str:
    if theme not in THEME_KEYMAP:
        raise ValueError(f"Unknown theme: {theme}")
    return THEME_KEYMAP[theme]

def normalize_age_bucket(target_age: int) -> str:
    # 10,20 / 30,40 / 50,60 / 70,80
    if target_age in (10, 20):
        return "10_20"
    if target_age in (30, 40):
        return "30_40"
    if target_age in (50, 60):
        return "50_60"
    if target_age in (70, 80):
        return "70_80"
    raise ValueError(f"Unexpected target_age: {target_age}")



#  실제 파일 경로를 아래에 전부 채워 넣으세요.
#  make_clova_voice.py 에서 생성 가능합니다.
VOICE_MAP: Dict[Tuple[str, str, str], str] = {
    # bunker
    ("bunker",    "10_20",  "male"):   r"c:\Artech5\Image_Box\clova_sample\지하벙커 생존자 커뮤니티_남자_10대.wav",
    ("bunker",    "10_20",  "female"): r"c:\Artech5\Image_Box\clova_sample\지하벙커 생존자 커뮤니티_여자_10대.wav",
    ("bunker",    "30_40",  "male"):   r"c:\Artech5\Image_Box\clova_sample\지하벙커 생존자 커뮤니티_남자_30~40대.wav",
    ("bunker",    "30_40",  "female"): r"c:\Artech5\Image_Box\clova_sample\지하벙커 생존자 커뮤니티_여자_30~40대.wav",
    ("bunker",    "50_60",  "male"):   r"c:\Artech5\Image_Box\clova_sample\지하벙커 생존자 커뮤니티_남자_50~60대.wav",
    ("bunker",    "50_60",  "female"): r"c:\Artech5\Image_Box\clova_sample\지하벙커 생존자 커뮤니티_여자_50~60대.wav",
    ("bunker",    "70_80",  "male"):   r"c:\Artech5\Image_Box\clova_sample\지하벙커 생존자 커뮤니티_남자_70~80대.wav",
    ("bunker",    "70_80",  "female"): r"c:\Artech5\Image_Box\clova_sample\지하벙커 생존자 커뮤니티_여자_70~80대.wav",

    # cyberpunk
    ("cyberpunk", "10_20",  "male"):   r"c:\Artech5\Image_Box\clova_sample\사이버펑크_남자_10대.wav",
    ("cyberpunk", "10_20",  "female"): r"c:\Artech5\Image_Box\clova_sample\사이버펑크_여자_10대.wav",
    ("cyberpunk", "30_40",  "male"):   r"c:\Artech5\Image_Box\clova_sample\사이버펑크_남자_30~40대.wav",
    ("cyberpunk", "30_40",  "female"): r"c:\Artech5\Image_Box\clova_sample\사이버펑크_여자_30~40대.wav",
    ("cyberpunk", "50_60",  "male"):   r"c:\Artech5\Image_Box\clova_sample\사이버펑크_남자_50~60대.wav",
    ("cyberpunk", "50_60",  "female"): r"c:\Artech5\Image_Box\clova_sample\사이버펑크_여자_50~60대.wav",
    ("cyberpunk", "70_80",  "male"):   r"c:\Artech5\Image_Box\clova_sample\사이버펑크_남자_70~80대.wav",
    ("cyberpunk", "70_80",  "female"): r"c:\Artech5\Image_Box\clova_sample\사이버펑크_여자_70~80대.wav",

    # eco_city
    ("eco_city",  "10_20",  "male"):   r"c:\Artech5\Image_Box\clova_sample\에코 스마트시티_남자_10대.wav",
    ("eco_city",  "10_20",  "female"): r"c:\Artech5\Image_Box\clova_sample\에코 스마트시티_여자_10대.wav",
    ("eco_city",  "30_40",  "male"):   r"c:\Artech5\Image_Box\clova_sample\에코 스마트시티_남자_30~40대.wav",
    ("eco_city",  "30_40",  "female"): r"c:\Artech5\Image_Box\clova_sample\에코 스마트시티_여자_30~40대.wav",
    ("eco_city",  "50_60",  "male"):   r"c:\Artech5\Image_Box\clova_sample\에코 스마트시티_남자_50~60대.wav",
    ("eco_city",  "50_60",  "female"): r"c:\Artech5\Image_Box\clova_sample\에코 스마트시티_여자_50~60대.wav",
    ("eco_city",  "70_80",  "male"):   r"c:\Artech5\Image_Box\clova_sample\에코 스마트시티_남자_70~80대.wav",
    ("eco_city",  "70_80",  "female"): r"c:\Artech5\Image_Box\clova_sample\에코 스마트시티_여자_70~80대.wav",

    # mars
    ("mars",      "10_20",  "male"):   r"c:\Artech5\Image_Box\clova_sample\화성 이주_남자_10대.wav",
    ("mars",      "10_20",  "female"): r"c:\Artech5\Image_Box\clova_sample\화성 이주_여자_10대.wav",
    ("mars",      "30_40",  "male"):   r"c:\Artech5\Image_Box\clova_sample\화성 이주_남자_30~40대.wav",
    ("mars",      "30_40",  "female"): r"c:\Artech5\Image_Box\clova_sample\화성 이주_여자_30~40대.wav",
    ("mars",      "50_60",  "male"):   r"c:\Artech5\Image_Box\clova_sample\화성 이주_남자_50~60대.wav",
    ("mars",      "50_60",  "female"): r"c:\Artech5\Image_Box\clova_sample\화성 이주_여자_50~60대.wav",
    ("mars",      "70_80",  "male"):   r"c:\Artech5\Image_Box\clova_sample\화성 이주_남자_70~80대.wav",
    ("mars",      "70_80",  "female"): r"c:\Artech5\Image_Box\clova_sample\화성 이주_여자_70~80대.wav",
}



# target_age, gender, theme 3개 인자를 받아 음성 파일 경로 반환
def get_first_voice(target_age: int, gender: str, theme: str,
                    voice_map: Dict[Tuple[str, str, str], str] = VOICE_MAP) -> Optional[str]:

    gender_key = normalize_gender(gender)
    theme_key  = normalize_theme(theme)
    age_bucket = normalize_age_bucket(int(target_age))
    return voice_map.get((theme_key, age_bucket, gender_key))



if __name__ == "__main__":
    # 예시 호출
    path = get_first_voice(50, "여자", "에코 스마트시티")
    print("선택된 음성 파일:", path)

