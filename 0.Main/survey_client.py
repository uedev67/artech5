
from flask import Flask, request

def run_survey_server(host="0.0.0.0", port=5000):
    """
    설문 결과를 한 번 수신하면 해당 결과를 반환하고 서버를 종료합니다.
    """
    from threading import Event
    app = Flask(__name__)
    result_holder = {'data': None}
    done_event = Event()

    @app.route("/survey", methods=["POST"])
    def survey():
        data = request.json
        #print(f"[SERVER] 설문 결과 수신: {data}")
        result_holder['data'] = data
        # 응답을 먼저 보내고, 서버 종료 신호는 약간 지연시킴
        from threading import Timer
        def delayed_set():
            done_event.set()
        Timer(0.5, delayed_set).start()  # 0.5초 후 서버 종료 신호
        return "OK", 200

    # Flask 서버를 별도 스레드에서 실행
    from threading import Thread
    def run():
        app.run(host=host, port=port)

    server_thread = Thread(target=run, daemon=True)
    server_thread.start()

    # 설문 결과가 올 때까지 대기
    done_event.wait()


    # 서버 종료 코드 제거: 설문 결과 반환 후 프로그램이 계속 실행됨
    # import os, signal
    # os.kill(os.getpid(), signal.SIGINT)

    return result_holder['data']
