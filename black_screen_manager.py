import tkinter as tk
from multiprocessing import Queue
import queue # for the Empty exception
import sys
import traceback

def run_black_screen_process(command_queue: Queue):
    """
    명령 큐(Queue)를 통해 'hide', 'show' 명령을 받아 검은 화면을 제어하는 프로세스입니다.
    """
    try:
        root = tk.Tk()
        
        # --- [수정된 부분] ---
        # 1. 먼저 창을 전체 화면으로 만듭니다.
        root.attributes('-fullscreen', True)
        # 2. 그 다음에 창의 테두리를 제거합니다. (오류 해결)
        root.overrideredirect(True)
        # --- 수정 끝 ---
        
        # 검은 배경색
        root.configure(bg='black')
        
        # 항상 다른 창들 위에 있도록 설정하여 화면을 완전히 가립니다.
        root.wm_attributes("-topmost", 1)

        def check_queue():
            """ 0.1초마다 큐를 확인하여 명령을 처리하는 함수입니다. """
            try:
                command = command_queue.get_nowait()
                if command == 'hide':
                    root.withdraw() # 창을 보이지 않게 숨깁니다.
                    print("[Black Screen] Window hidden.")
                elif command == 'show':
                    root.deiconify() # 숨겨진 창을 다시 표시합니다.
                    print("[Black Screen] Window shown.")
            except queue.Empty:
                # 큐가 비어있으면 아무것도 하지 않습니다.
                pass
            finally:
                # 0.1초 후에 다시 큐를 확인하도록 예약합니다.
                root.after(100, check_queue)

        # 큐 확인 루프를 시작합니다.
        check_queue()
        # tkinter 창을 실행합니다.
        root.mainloop()
    except Exception as e:
        # 멀티프로세스에서 발생하는 숨겨진 오류를 추적하기 위해 파일에 로그를 남깁니다.
        with open("black_screen_error.log", "w", encoding='utf-8') as f:
            f.write(f"An error occurred in black_screen_process:\n")
            f.write(f"{str(e)}\n")
            f.write(traceback.format_exc())
        # 오류 발생 시 프로세스 종료
        sys.exit(1)


