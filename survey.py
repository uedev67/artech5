import tkinter as tk
from tkinter import messagebox
import socket, json

SERVER_HOST = "192.168.0.10"   # ← 데스크탑의 로컬 IP로 바꾸세요
SERVER_PORT = 50555
SOCKET_TIMEOUT = 5

def send_result(result: dict, host: str, port: int) -> bool:
    """설문 결과를 TCP로 한 줄 JSON 전송"""
    try:
        payload = json.dumps(result, ensure_ascii=False) + "\n"
        with socket.create_connection((host, port), timeout=SOCKET_TIMEOUT) as s:
            s.sendall(payload.encode("utf-8"))
        return True
    except Exception as e:
        messagebox.showwarning("전송 실패", f"결과 전송 중 오류: {e}")
        return False

def run_survey():
    result = {}
    IsEnterOK = False

    def submit_answer():
        nonlocal IsEnterOK
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

        result["q1"] = selected1
        result["q2"] = selected2
        result["q3"] = selected3
        IsEnterOK = True
        result["IsEnterOK"] = IsEnterOK

        # 전송 시도
        ok = send_result(result, SERVER_HOST, SERVER_PORT)
        if ok:
            messagebox.showinfo("설문 결과", "전송 완료!\n" +
                                f"1번: {selected1}\n2번: {selected2}\n3번: {selected3}")
        root.destroy()

    root = tk.Tk()
    root.title("설문조사")
    root.geometry("1200x700")

    label_font = ("맑은 고딕", 18)
    radio_font = ("맑은 고딕", 18)

    # 1번
    tk.Label(
        root,
        text="1. 당신의 얼굴과 이야기를 빌려, 이 세계 속 또 다른 '나'를 만들어도 될까요? ...\n(방문자의 얼굴 정보 및 설문 결과를 기반으로 AI 이미지가 생성됩니다. 이에 동의하십니까?)",
        font=label_font, anchor='w', justify='left'
    ).pack(pady=15, fill='x')
    var1 = tk.StringVar(value="")
    for choice in ["예", "아니오"]:
        tk.Radiobutton(root, text=choice, variable=var1, value=choice, font=radio_font).pack(anchor='w')

    # 2번
    tk.Label(root, text="2. 당신의 성별은?", font=label_font, anchor='w', justify='left').pack(pady=15, fill='x')
    var2 = tk.StringVar(value="")
    for choice in ["남자", "여자"]:
        tk.Radiobutton(root, text=choice, variable=var2, value=choice, font=radio_font).pack(anchor='w')

    # 3번
    tk.Label(root, text="3. 당신이 생각하는 미래사회의 모습은?", font=label_font, anchor='w', justify='left').pack(pady=15, fill='x')
    var3 = tk.StringVar(value="")
    for choice in ["지하벙커 생존자 커뮤니티", "사이버펑크", "에코 스마트시티", "화성 이주"]:
        tk.Radiobutton(root, text=choice, variable=var3, value=choice, font=radio_font).pack(anchor='w')

    tk.Button(root, text="제출", command=submit_answer, font=("맑은 고딕", 24), width=15, height=2).pack(pady=30)

    root.mainloop()
    if "IsEnterOK" not in result:
        result["IsEnterOK"] = False
    return result

if __name__ == "__main__":
    res = run_survey()
    print("설문 결과:", res)
