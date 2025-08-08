import socket, json

HOST = "0.0.0.0"   # 모든 인터페이스에서 수신
PORT = 50555

def run_server():
    print(f"[SERVER] Listening on {HOST}:{PORT}")
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as srv:
        srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        srv.bind((HOST, PORT))
        srv.listen(5)
        while True:
            conn, addr = srv.accept()
            with conn:
                print(f"[SERVER] Connected from {addr}")
                buf = b""
                # 클라이언트가 한 줄(JSON + \n) 보내고 종료
                while True:
                    chunk = conn.recv(4096)
                    if not chunk:
                        break
                    buf += chunk
                    # 줄단위 프로토콜
                    if b"\n" in buf:
                        line, _, rest = buf.partition(b"\n")
                        buf = rest
                        try:
                            data = json.loads(line.decode("utf-8"))
                            print("[RECV]", data)
                        except Exception as e:
                            print("[ERROR] Bad JSON:", e)

if __name__ == "__main__":
    run_server()
