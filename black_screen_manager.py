import tkinter as tk

class BlackScreen:
    """
    모니터 전체를 덮는 검은색 창을 생성하고 관리하는 클래스입니다.
    """
    def __init__(self):
        # tkinter 기본 윈도우 생성
        self.root = tk.Tk()
        
        # 1. 먼저 윈도우를 전체 화면으로 만듭니다.
        self.root.attributes('-fullscreen', True)
        
        # 2. 그 다음에 제목 표시줄과 테두리를 제거합니다.
        # 이 순서로 실행하면 첫 번째 오류(TclError)가 발생하지 않습니다.
        self.root.overrideredirect(True)
        
        # [중요] '항상 위' 속성을 제거하여, VLC 같은 다른 전체 화면 프로그램이
        # 이 검은 화면 위에 나타날 수 있도록 합니다.
        # self.root.wm_attributes('-topmost', 1) # <- 이 라인을 삭제하거나 주석 처리합니다.

        # 윈도우의 배경색을 검은색으로 설정합니다.
        self.root.configure(bg='black')
        
        # 다른 창에 의해 가려지더라도 포커스를 유지하려 시도합니다.
        self.root.focus_force()

    def start(self):
        """
        GUI 이벤트 루프를 시작하여 창을 화면에 계속 표시합니다.
        """
        self.root.mainloop()

def run_black_screen_process():
    """
    BlackScreen 인스턴스를 생성하고 시작하는 함수.
    """
    app = BlackScreen()
    app.start()

# 이 파일이 직접 실행될 경우 (테스트용)
if __name__ == '__main__':
    run_black_screen_process()