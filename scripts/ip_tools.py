import re
from typing import Literal

regex_ipv4 = r"\b(?:(?:25[0-5]|2[0-4][0-9]|1?[0-9]{1,2})\.){3}(?:25[0-5]|2[0-4][0-9]|1?[0-9]{1,2})\b"
regex_ipv6 = (
    r"(?:^|(?<=\s))(?:(?:[A-Fa-f0-9]{1,4}:){7}[A-Fa-f0-9]{1,4}|"
    r"(?:[A-Fa-f0-9]{1,4}:){1,7}:|"
    r"(?:[A-Fa-f0-9]{1,4}:){1,6}:[A-Fa-f0-9]{1,4}|"
    r"(?:[A-Fa-f0-9]{1,4}:){1,5}(?::[A-Fa-f0-9]{1,4}){1,2}|"
    r"(?:[A-Fa-f0-9]{1,4}:){1,4}(?::[A-Fa-f0-9]{1,4}){1,3}|"
    r"(?:[A-Fa-f0-9]{1,4}:){1,3}(?::[A-Fa-f0-9]{1,4}){1,4}|"
    r"(?:[A-Fa-f0-9]{1,4}:){1,2}(?::[A-Fa-f0-9]{1,4}){1,5}|"
    r"[A-Fa-f0-9]{1,4}:(?:(?::[A-Fa-f0-9]{1,4}){1,6})|"
    r":(?:(?::[A-Fa-f0-9]{1,4}){1,7}|:))"
    r"(?:$|(?=\s))"
)


def extract_ip_port(full_ip: str) -> dict[Literal["ip", "port"], str]:

    ipv6_match = re.search(regex_ipv6, full_ip)
    ipv4_match = re.search(regex_ipv4, full_ip.split(":")[0])

    ip = ""
    port = ""

    # ipv6 with port
    if "]:" in full_ip:
        [ip, port] = full_ip.replace("[", "").split("]:")
        ip = ip
        port = port
    # ipv6 without port
    elif ipv6_match:
        ip = full_ip
        port = ""
    # all ipv4 matches
    elif ipv4_match:
        # ipv4 with port
        if ":" in full_ip:
            [ip, port] = full_ip.split(":")
            ip = ip
            port = port
        # ipv4 without port
        else:
            ip = full_ip
            port = ""

    return {"ip": ip, "port": port}
