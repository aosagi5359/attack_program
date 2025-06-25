import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog, messagebox
import threading
import importlib.util
import os
import socket
from datetime import datetime
import random
import ipaddress
from urllib.parse import urlparse
import time

class AttackApp:
    def __init__(self, root):
        self.root = root
        self.root.title("多模組封包攻擊介面")
        self.root.geometry("1100x650")
        self.root.configure(bg="#2C2C2C")

        self.attack_modules = self.load_attack_modules()
        self.attack_threads = []
        self.stop_event = threading.Event()

        main_frame = tk.Frame(root, bg="#2C2C2C")
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # 左側：模組設定
        left_frame = tk.Frame(main_frame, bg="#2C2C2C", width=400)
        left_frame.pack(side="left", fill="y", padx=10)

        tk.Label(left_frame, text="輸入網址或主機名", bg="#2C2C2C", fg="#D3D3D3").pack(anchor="w", pady=(10, 0))
        self.url_entry = tk.Entry(left_frame, width=30, bg="#3C3C3C", fg="#D3D3D3", insertbackground="#D3D3D3")
        self.url_entry.pack(pady=5)

        self.attack_config_frame = tk.Frame(left_frame, bg="#2C2C2C")
        self.attack_config_frame.pack(fill="y", expand=True)

        self.module_rows = []
        self.add_attack_row()

        tk.Button(left_frame, text="新增攻擊模組", command=self.add_attack_row, bg="#444", fg="white").pack(pady=5)
        tk.Button(left_frame, text="開始所有攻擊", command=self.start_all_attacks, bg="#4C4C4C", fg="white").pack(pady=5)
        tk.Button(left_frame, text="停止所有攻擊", command=self.stop_all_attacks, bg="#662222", fg="white").pack(pady=5)
        tk.Button(left_frame, text="打開報告", command=self.view_report, bg="#4C4C4C", fg="white").pack(pady=5)

        # 右側：輸出區與命令
        right_frame = tk.Frame(main_frame, bg="#2C2C2C")
        right_frame.pack(side="right", fill="both", expand=True)

        self.output_text = scrolledtext.ScrolledText(right_frame, height=20, bg="#3C3C3C", fg="#D3D3D3", insertbackground="#D3D3D3")
        self.output_text.pack(fill="both", expand=True, padx=5, pady=10)

        command_frame = tk.Frame(right_frame, bg="#2C2C2C")
        command_frame.pack(fill="x", pady=(0, 10), padx=5)
        tk.Label(command_frame, text="命令輸入", bg="#2C2C2C", fg="#D3D3D3").pack(side="left")
        self.command_entry = tk.Entry(command_frame, width=60, bg="#3C3C3C", fg="#D3D3D3", insertbackground="#D3D3D3")
        self.command_entry.pack(side="left", padx=10)
        self.command_entry.bind("<Return>", self.process_command)

    def load_attack_modules(self):
        modules = {}
        attack_dir = "attack_tools"
        if not os.path.exists(attack_dir):
            os.makedirs(attack_dir)
        for file in os.listdir(attack_dir):
            if file.endswith(".py") and not file.startswith("__"):
                module_name = file[:-3]
                path = os.path.join(attack_dir, file)
                spec = importlib.util.spec_from_file_location(module_name, path)
                module = importlib.util.module_from_spec(spec)
                try:
                    spec.loader.exec_module(module)
                    if hasattr(module, "attack"):
                        modules[module_name] = module
                except Exception as e:
                    print(f"無法載入模組 {file}: {e}")
        return modules

    def add_attack_row(self):
        frame = tk.Frame(self.attack_config_frame, bg="#2C2C2C")
        frame.pack(fill="x", pady=5)

        module_cb = ttk.Combobox(frame, values=list(self.attack_modules.keys()), state="readonly", width=15)
        if self.attack_modules:
            module_cb.set(list(self.attack_modules.keys())[0])
        module_cb.pack(side="left", padx=2)

        ip_entry = tk.Entry(frame, width=18, bg="#3C3C3C", fg="white", insertbackground="white")
        ip_entry.insert(0, "目標 IP")
        ip_entry.pack(side="left", padx=2)

        pkt_entry = tk.Entry(frame, width=8, bg="#3C3C3C", fg="white", insertbackground="white")
        pkt_entry.insert(0, "10")
        pkt_entry.pack(side="left", padx=2)

        spoof_var = tk.BooleanVar(value=False)
        spoof_cb = tk.Checkbutton(frame, text="偽造IP", variable=spoof_var, bg="#2C2C2C", fg="white", selectcolor="#2C2C2C")
        spoof_cb.pack(side="left", padx=2)

        delete_btn = tk.Button(frame, text="刪除", command=lambda: self.delete_attack_row(frame, (module_cb, ip_entry, pkt_entry, spoof_var)), bg="#662222", fg="white", width=5)
        delete_btn.pack(side="left", padx=2)

        self.module_rows.append((module_cb, ip_entry, pkt_entry, spoof_var))

    def delete_attack_row(self, frame, row_tuple):
        if row_tuple in self.module_rows:
            self.module_rows.remove(row_tuple)
        frame.destroy()
        self.log("[資訊] 已刪除攻擊模組配置")

    def log(self, msg):
        self.output_text.insert(tk.END, msg + "\n")
        self.output_text.see(tk.END)

    def resolve_ip_from_url(self, url):
        try:
            parsed = urlparse(url if url.startswith("http") else "http://" + url)
            hostname = parsed.hostname
            return socket.gethostbyname(hostname)
        except Exception as e:
            self.log(f"[錯誤] 網址解析失敗：{e}")
            return None

    def start_all_attacks(self):
        self.stop_event.clear()
        self.attack_threads.clear()
        url = self.url_entry.get()
        target_ip = None

        if url:
            target_ip = self.resolve_ip_from_url(url)
            if not target_ip:
                self.log(f"[錯誤] 無法解析網址：{url}")
                return
            self.log(f"[資訊] 目標 IP 為 {target_ip}")

        for module_cb, ip_entry, pkt_entry, spoof_var in self.module_rows:
            name = module_cb.get()
            ip = ip_entry.get() if ip_entry.get() != "目標 IP" else target_ip
            try:
                packet_count = int(pkt_entry.get())
            except:
                self.log(f"[錯誤] 封包數格式錯誤：{pkt_entry.get()}")
                continue
            spoof_ip = self.generate_random_ip() if spoof_var.get() else None

            if not name or name not in self.attack_modules:
                self.log(f"[錯誤] 攻擊模組無效：{name}")
                continue
            if not ip:
                self.log("[錯誤] IP 為空")
                continue

            self.log(f"[準備] 攻擊 {ip} 使用 {name}，封包數：{packet_count} 偽造IP：{spoof_ip if spoof_ip else '否'}")

            t = threading.Thread(target=self.run_attack, args=(name, ip, packet_count, spoof_ip))
            t.daemon = True
            t.start()
            self.attack_threads.append(t)

    def stop_all_attacks(self):
        self.stop_event.set()
        active_threads = [t for t in self.attack_threads if t.is_alive()]
        if active_threads:
            self.log(f"[資訊] 正在請求終止 {len(active_threads)} 個攻擊線程...")
            # Wait briefly for threads to terminate
            for t in active_threads:
                t.join(timeout=3.0)  # Give threads up to 3 seconds to terminate
            # Check if any threads are still alive
            still_active = [t for t in active_threads if t.is_alive()]
            if still_active:
                self.log(f"[警告] {len(still_active)} 個攻擊線程未能及時終止，可能需要更新攻擊模組以支援停止功能")
        else:
            self.log("[資訊] 無活動攻擊線程")
        self.attack_threads.clear()
        self.log("[完成] 所有攻擊已請求停止")
        self.stop_event.clear()

    def run_attack(self, name, ip, packet_count, spoof_ip):
        module = self.attack_modules.get(name)
        report_lines = []
        try:
            if hasattr(module, "train_model"):
                self.log(f"[訓練] {name} 模組進行訓練中...")
                module.train_model()

            try:
                success = module.attack(ip, packet_count, lambda msg: self.log_and_collect(msg, report_lines), spoof_ip=spoof_ip, stop_event=self.stop_event)
            except TypeError:
                self.log(f"[警告] {name} 不支援停止事件，嘗試不帶 stop_event 執行")
                success = module.attack(ip, packet_count, lambda msg: self.log_and_collect(msg, report_lines), spoof_ip=spoof_ip)
                
            result = "成功" if success else "可能失敗"
            report_lines.append(f"[結果] 攻擊結果：{result}")
            self.save_report(name, ip, packet_count, report_lines, result)
        except Exception as e:
            self.log(f"[錯誤] {name} 攻擊失敗：{e}")

    def save_report(self, module_name, ip, count, lines, result):
        if not os.path.exists("reports"):
            os.makedirs("reports")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = f"reports/{module_name}_{timestamp}.log"
        with open(path, "w", encoding="utf-8") as f:
            f.write(f"模組：{module_name}\n目標IP：{ip}\n封包數：{count}\n結果：{result}\n時間：{timestamp}\n\n")
            f.write("\n".join(lines))
        self.log(f"[報告] 儲存至 {path}")

    def log_and_collect(self, msg, report):
        self.log(msg)
        report.append(msg)

    def view_report(self):
        report_dir = "reports"
        if not os.path.exists(report_dir):
            self.log("[錯誤] 報告資料夾不存在")
            return

        report_file = filedialog.askopenfilename(
            initialdir=report_dir,
            title="選擇報告檔案",
            filetypes=(("Log files", "*.log"), ("All files", "*.*"))
        )
        
        if report_file:
            try:
                with open(report_file, "r", encoding="utf-8") as f:
                    content = f.read()
                
                report_window = tk.Toplevel(self.root)
                report_window.title("攻擊報告")
                report_window.geometry("600x400")
                report_window.configure(bg="#2C2C2C")

                report_text = scrolledtext.ScrolledText(report_window, height=20, bg="#3C3C3C", fg="#D3D3D3", insertbackground="#D3D3D3")
                report_text.pack(fill="both", expand=True, padx=5, pady=5)
                report_text.insert(tk.END, content)
                report_text.config(state="disabled")

                tk.Button(report_window, text="關閉", command=report_window.destroy, bg="#4C4C4C", fg="white").pack(pady=5)
                
                self.log(f"[報告] 已開啟報告：{report_file}")
            except Exception as e:
                self.log(f"[錯誤] 無法開啟報告：{e}")

    def process_command(self, event):
        cmd = self.command_entry.get().strip()
        if cmd:
            self.log(f"[命令] {cmd}")
            self.command_entry.delete(0, tk.END)

    def generate_random_ip(self):
        return f"192.168.{random.randint(0, 255)}.{random.randint(1, 254)}"

if __name__ == "__main__":
    root = tk.Tk()
    app = AttackApp(root)
    root.mainloop()