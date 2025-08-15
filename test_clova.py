from clova import clova


if __name__ == "__main__":

    target_age = 80
    gender = "남자"
    theme = "에코 스마트시티"
    answer = "어쩌다가 이렇게 된 걸까.. 항상 미래를 대비해야해."

    voice = clova(target_age, gender, theme, answer)
    print(f"저장 완료: {voice}")