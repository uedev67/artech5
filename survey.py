import json
from datetime import datetime
import tkinter as tk
from tkinter import messagebox
import requests

# ================== 설정 ==================
# 데스크탑 Flask 서버 주소로 바꾸세요. 예) http://192.168.0.188:5000/survey
SERVER_URL = "http://192.168.0.188:5000/survey"
TIMEOUT = 5         # 요청 타임아웃(초)
RETRIES = 2     # 재시도 횟수
BACKUP_FILE = "survey_backup.jsonl"  # 전송 실패 시 로컬 백업

def post_json(url: str, payload: dict, timeout: int, retries: int) -> bool:
    for attempt in range(1, retries + 1):
        try:
            resp = requests.post(url, json=payload, timeout=timeout)
            resp.raise_for_status()
            return True
        except requests.exceptions.RequestException as e:
            print(f"[CLIENT] 전송 오류 ({attempt}/{retries}): {e}")
    return False

def backup_locally(payload: dict, path: str) -> None:
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(payload, ensure_ascii=False) + "\n")

def run_gui():
    result = {}

    def submit_answer():
        selected1 = var1.get()
        selected2 = var2.get()
        selected3 = var3.get()

        if not selected1:
            messagebox.showwarning("경고", "1번 질문에 답변해주세요.")
            return
        if not selected2:
            messagebox.showwarning("경고", "2번 질문에 답변해주세요.")
            return
        if not selected3:
            messagebox.showwarning("경고", "3번 질문에 답변해주세요.")
            return

        # payload 구성
        result.clear()
        result["q1"] = selected1
        result["q2"] = selected2
        result["q3"] = selected3
        result["IsEnterOK"] = True
        result["meta"] = {
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "client": "notebook",
            "version": "1.0-http-gui"
        }

        # 전송 시도
        ok = post_json(SERVER_URL, result, timeout=TIMEOUT, retries=RETRIES)
        if ok:
            messagebox.showinfo(
                "설문 결과",
                "전송 완료!\n"
                f"1번: {selected1}\n"
                f"2번: {selected2}\n"
                f"3번: {selected3}"
            )
        else:
            backup_locally(result, BACKUP_FILE)
            messagebox.showwarning(
                "전송 실패",
                f"서버 전송에 실패하여 로컬로 백업했습니다.\n파일: {BACKUP_FILE}"
            )
        root.destroy()

    # GUI
    root = tk.Tk()
    root.title("설문조사")
    root.geometry("1200x700")

    label_font = ("맑은 고딕", 18)
    radio_font = ("맑은 고딕", 18)

    # 1번 (동의)
    tk.Label(
        root,
        text="1. 당신의 얼굴과 이야기를 빌려, 이 세계 속 또 다른 '나'를 만들어도 될까요? ...\n(방문자의 얼굴 정보 및 설문 결과를 기반으로 AI 이미지가 생성됩니다. 이에 동의하십니까?)",
        font=label_font, anchor='w', justify='left', wraplength=1100
    ).pack(pady=15, fill='x')
    var1 = tk.StringVar(value="")
    for choice in ["예", "아니오"]:
        tk.Radiobutton(root, text=choice, variable=var1, value=choice, font=radio_font).pack(anchor='w')

    # 2번 (성별)
    tk.Label(root, text="2. 당신의 성별은?", font=label_font, anchor='w', justify='left').pack(pady=15, fill='x')
    var2 = tk.StringVar(value="")
    for choice in ["남자", "여자"]:
        tk.Radiobutton(root, text=choice, variable=var2, value=choice, font=radio_font).pack(anchor='w')

    # 3번 (미래사회 테마)
    tk.Label(root, text="3. 당신이 생각하는 미래사회의 모습은?", font=label_font, anchor='w', justify='left').pack(pady=15, fill='x')
    var3 = tk.StringVar(value="")
    for choice in ["지하벙커 생존자 커뮤니티", "사이버펑크", "에코 스마트시티", "화성 이주"]:
        tk.Radiobutton(root, text=choice, variable=var3, value=choice, font=radio_font).pack(anchor='w')

    tk.Button(root, text="제출", command=submit_answer, font=("맑은 고딕", 24), width=15, height=2).pack(pady=30)

    root.mainloop()

if __name__ == "__main__":
    run_gui()
