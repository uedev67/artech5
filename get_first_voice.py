
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
    if target_age == 10:
        return "child"   # 소년
    if target_age in (20, 30, 40):
        return "young"   # 청년
    if target_age >= 50:
        return "middle"  # 중년
    raise ValueError(f"Unexpected target_age: {target_age}")



# 3) 24개 음성 파일 경로 매핑
#    - 실제 파일 경로를 아래에 전부 채워 넣으세요.
VOICE_MAP: Dict[Tuple[str, str, str], str] = {
    # bunker
    # ("bunker",    "child",  "male"):   r"C:\voices\bunker_child_male.wav",
    # ("bunker",    "child",  "female"): r"C:\voices\bunker_child_female.wav",
    # ("bunker",    "young",  "male"):   r"C:\voices\bunker_young_male.wav",
    # ("bunker",    "young",  "female"): r"C:\voices\bunker_young_female.wav",
    # ("bunker",    "middle", "male"):   r"C:\voices\bunker_middle_male.wav",
    # ("bunker",    "middle", "female"): r"C:\voices\bunker_middle_female.wav",

    # cyberpunk
    # ("cyberpunk", "child",  "male"):   r"C:\voices\cyberpunk_child_male.wav",
    # ("cyberpunk", "child",  "female"): r"C:\voices\cyberpunk_child_female.wav",
    # ("cyberpunk", "young",  "male"):   r"C:\voices\cyberpunk_young_male.wav",
    # ("cyberpunk", "young",  "female"): r"C:\voices\cyberpunk_young_female.wav",
    # ("cyberpunk", "middle", "male"):   r"C:\voices\cyberpunk_middle_male.wav",
    # ("cyberpunk", "middle", "female"): r"C:\voices\cyberpunk_middle_female.wav",

    # eco_city
    # ("eco_city",  "child",  "male"):   r"C:\voices\eco_city_child_male.wav",
    # ("eco_city",  "child",  "female"): r"C:\voices\eco_city_child_female.wav",
    # ("eco_city",  "young",  "male"):   r"C:\voices\eco_city_young_male.wav",
    # ("eco_city",  "young",  "female"): r"C:\voices\eco_city_young_female.wav",
    # ("eco_city",  "middle", "male"):   r"C:\voices\eco_city_middle_male.wav",
    # ("eco_city",  "middle", "female"): r"C:\voices\eco_city_middle_female.wav",

    # mars
    # ("mars",      "child",  "male"):   r"C:\voices\mars_child_male.wav",
    # ("mars",      "child",  "female"): r"C:\voices\mars_child_female.wav",
    # ("mars",      "young",  "male"):   r"C:\voices\mars_young_male.wav",
    # ("mars",      "young",  "female"): r"C:\voices\mars_young_female.wav",
    # ("mars",      "middle", "male"):   r"C:\voices\mars_middle_male.wav",
    # ("mars",      "middle", "female"): r"C:\voices\mars_middle_female.wav",
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
