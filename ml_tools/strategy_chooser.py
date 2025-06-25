import re

def choose_attack_module(target, available_modules, log_fn):
    """
    根據目標特徵與可用模組自動選擇攻擊方式。
    """
    log_fn(f"[策略模組] 分析目標：{target}")

    ip_pattern = r"^\d{1,3}(\.\d{1,3}){3}$"
    is_ip = re.match(ip_pattern, target)

    # 模擬策略：不同情況使用不同攻擊
    if "login" in target or "session" in target:
        if "session_hijacking" in available_modules:
            return "session_hijacking"
    elif is_ip:
        last_octet = int(target.strip().split(".")[-1])
        if last_octet < 50 and "smurf" in available_modules:
            return "smurf"
        elif last_octet % 2 == 0 and "icmp_flood" in available_modules:
            return "icmp_flood"
        elif "tcp_rst" in available_modules:
            return "tcp_rst"
    elif "test" in target or "dev" in target:
        if "fragmentation" in available_modules:
            return "fragmentation"
    elif "slow" in target or "keepalive" in target:
        if "slowloris" in available_modules:
            return "slowloris"

    # 預設回傳第一個可用模組
    log_fn("[策略模組] 找不到明確特徵，預設選擇。")
    return next(iter(available_modules), None)
