import openai


openai.api_key = "YOUR_API_KEY"  # 실제 API 키 입력


theme_prompts = {
    "사이버펑크": "",
    "지하 커뮤니티": "",
    "에코 스마트시티": ""
}


selected_theme = "사이버펑크"  # 이건 나중에 함수화해서 survey로부터 값을 할당받기


system_prompt = theme_prompts[selected_theme]

def ask_gpt(user_input):
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_input}
        ]
    )
    return response['choices'][0]['message']['content']

# 테스트 실행부
if __name__ == "__main__":
    print(f"테마: {selected_theme} / GPT 대화 시작")
    while True:
        user_input = input("나: ")
        if user_input.lower() == 'exit':
            break
        gpt_response = ask_gpt(user_input)
        print("GPT:", gpt_response)
