# artech_test2.py에 붙일 함수 : 마지막 엔딩을 실행하는 역할



def ending_with_button():
    """
    엔딩 시퀀스를 위해 Worker('ending_with_button.py')를 실행하고,
    성공 여부에 따라 True/False를 반환합니다.

    Returns:
        bool: IsEnd. Worker가 성공적으로 실행되면 True, 오류 발생 시 False.
    """
    print("[SERVER] 엔딩 시퀀스를 시작합니다. (Worker 호출)")
    
    # 현재 실행 중인 메인 스크립트의 디렉토리 경로를 가져옵니다.
    main_path = os.path.dirname(os.path.abspath(sys.argv[0]))
    # 호출할 Worker 스크립트의 전체 경로를 생성합니다.
    worker_path = os.path.join(main_path, 'ending_with_button.py')

    # Worker 스크립트 실행 명령어 (인자 없음)
    command = [
        sys.executable,
        worker_path
    ]
    
    # Worker를 별도 프로세스로 실행하고, 끝날 때까지 기다립니다.
    proc = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    _, stderr = proc.communicate()

    # Worker가 정상적으로 종료되었는지(returncode 0) 확인합니다.
    if proc.returncode == 0:
        print("[SERVER] 엔딩 시퀀스가 정상적으로 종료되었습니다.")
        IsEnd = True
        return IsEnd
    else:
        # Worker 실행 중 오류가 발생한 경우
        print(f"[SERVER] 엔딩 시퀀스 중 오류가 발생했습니다. stderr: {stderr.decode('utf-8', 'ignore').strip()}")
        IsEnd = False
        return IsEnd
