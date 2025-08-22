from clova import clova


if __name__ == "__main__":


    target_age = 40
    gender = "남자"
    theme = "에코 스마트시티"
    answer = "노는게 제일 좋아. 친구들 모여라. 언제나 즐거워. 개구쟁이 뽀로로"
    voice = clova(target_age, gender, theme, answer)
    print(f"생성된 음성 파일 경로: {voice}")