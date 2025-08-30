import tkinter as tk
import sys



def run_black_screen_simple():
    """
    단순히 전체 화면을 검은색으로 채우는 프로세스입니다.
    통신 기능이 없으며, 다른 전체 화면 창이 이 창 위에 표시될 수 있습니다.
    """
    try:
        root = tk.Tk()
        # 1. 먼저 창을 전체 화면으로 만듭니다.
        root.attributes('-fullscreen', True)
        # 2. 그 다음에 창의 테두리를 제거합니다.
        root.overrideredirect(True)
        root.configure(bg='black')
        
        # 중요: 'topmost' (항상 위) 속성을 설정하지 않아,
        # VLC 같은 다른 영상 플레이어가 이 화면 위에 나타날 수 있습니다.
        
        root.mainloop()
    except Exception as e:
        # 오류 발생 시 로그 파일에 기록합니다.
        with open("black_screen_simple_error.log", "w", encoding='utf-8') as f:
            f.write(f"An error occurred in run_black_screen_simple:\n{str(e)}\n")
        sys.exit(1)