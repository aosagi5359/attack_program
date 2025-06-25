import tkinter as tk
from tkinter import ttk, scrolledtext
import threading
import importlib.util
import os
import socket
from datetime import datetime
import random
import ipaddress

class AttackApp:
    def __init__(self, root):
        self.root = root
        self.root.title("多模組封包攻擊介面")
        self.root.geometry("1100x650")
        self.root.configure(bg="#2C2C2C")

        self.attack_modules = self.load_attack_modules()
        self.attack_threads = []

        main_frame = tk.Frame(root, bg="#2C2C2C")
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # 左側：模組設定
        left_frame = tk.Frame(main_frame, bg="#2C2C2C", width=400)
        left_frame.pack(side="left", fill="y", padx=10)

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

        self.module_rows.append((module_cb, ip_entry, pkt_entry, spoof_var))

    def log(self, msg):
        self.output_text.insert(tk.END, msg + "\n")
        self.output_text.see(tk.END)

    def start_all_attacks(self):
        self.attack_threads.clear()
        for module_cb, ip_entry, pkt_entry, spoof_var in self.module_rows:
            name = module_cb.get()
            ip = ip_entry.get()
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
            t.start()
            self.attack_threads.append(t)

    def stop_all_attacks(self):
        self.log("[警告] 模擬停止所有攻擊（尚未實作強制中止）")

    def run_attack(self, name, ip, packet_count, spoof_ip):
        module = self.attack_modules.get(name)
        report_lines = []
        try:
            if hasattr(module, "train_model"):
                self.log(f"[訓練] {name} 模組進行訓練中...")
                module.train_model()

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
        self.log("[報告] 尚未實作報告檢視功能。")

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