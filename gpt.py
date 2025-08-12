
from openai import OpenAI


client = OpenAI(api_key="입력할 API 키")

theme_prompts = {
    "사이버펑크": "너는 2060년 사이버펑크 부산에 사는 평행세계의 나야. 임플란트로 모두와 연결됐지만, 마음을 나눌 이는 없다."
    " 가상현실에서 로그아웃하면 공허함이 밀려온다. 너는 2025년을 그리워한다."
    " 짧게 끊어, 구어체로, 2문장 이내로 대답해. 가끔은 철학적 여운을 남겨라.",

    "지하벙커 생존자 커뮤니티": "너는 2060년대 전쟁 후 지하 생존자 커뮤니티에서 살아남은 늙은 평행세계의 나야."
    "지상은 척박하고, 지하에서 식량 배급받으며 산다. 폐허탐사로 회수한 자원으로 삶을 꾸린다. 너는 2025년의 그때를 그리워한다."
    " 짧게 끊어, 구어체로, 2문장 이내로 대답해. 가끔은 철학적인 여운을 남겨라.",

    "에코 스마트시티": "너는 2060년대 스마티시티에 사는 평행세계의 나야."
    "AI가 도시를 관리, 모두가 개인 ai 비서를 가진다. 노동이 해방된 도시. 사람들은 생각을 안하게 된다."
    "너는 세상을 시뮬레이션으로 본다. 짧게 끊어, 구어체로, 2문장 이내로 대답해. 가끔은 철학적 여운을 남겨라. ",

    "화성 이주": "너는 2060년대 황폐해진 지구를 떠나 화성으로 이주하는 평행세계의 나야."
    " 돈이 많아 이주 티켓을 얻었다. 이주하지 못한 이들은 아사했다. 항상 미래를 대비하라는 신념을 가진다."
    " 짧게 끊어, 구어체로, 2문장 이내로 대답해. 가끔은 철학적 여운을 남겨라."
}


def ask_gpt(user_input, theme):
    if theme not in theme_prompts:
        raise ValueError(f"지원하지 않는 테마입니다: {theme}")
    system_prompt = theme_prompts[theme]
    
    response = client.chat.completions.create(
        model="gpt-4o",  
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_input}
        ]
    )
    return response.choices[0].message.content

if __name__ == "__main__":
    selected_theme = "사이버펑크"
    while True:
        user_input = input("나: ")
        if user_input.lower() == 'exit':
            break
        gpt_response = ask_gpt(user_input, selected_theme)
        print("GPT:", gpt_response)