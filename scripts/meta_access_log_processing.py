from pathlib import Path
import argparse
import shutil
from typing import TypedDict, Literal
import re
import requests
import json
import numpy
import math


class AccessLog(TypedDict):
    ip: str
    port: str
    date: str


class UserAcessLogs(TypedDict):
    service: str
    target: str
    logs: list[AccessLog]


InfoIP_API = TypedDict(
    "InfoIP_API",
    {
        "asname": str,
        "as": str,
        "region": str,
        "city": str,
        "mobile": bool,
        "proxy": bool,
        "hosting": bool,
        "lat": float,
        "lon": float,
        "timezone": str,
        "countryCode": str,
        "status": str,
    },
)

# Diurno => entre 5h às 22h
# Noturno => entre 22h às 5h
Periodo = Literal["Diurno", "Noturno"]

InfoIP_Sheet = TypedDict(
    "InfoIP_Sheet",
    {
        "Alvo": str,
        "IP": str,
        "ISO_Date": str,
        "Data": str,
        "Dia da semana": str,
        "Data fuso": str,
        "IP_dono": str,
        "IP_AS": str,
        "IP_Regiao": str,
        "IP_Cidade": str,
        "IP_movel": str,
        "IP_Proxy": str,
        "IP_Hospedagem": str,
        "Periodo": Periodo,
        "Latitude": float,
        "Longitude": float,
    },
)


IP_URL = "http://ip-api.com/batch"

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


def find_index(term: str, array: list):
    index = next(index for index, line in enumerate(array) if term in line)

    return index


def find_exact_index(term: str, array: list[str]):
    index = next(
        index for index, line in enumerate(array) if term == line.replace("\n", "")
    )

    return index


def log_parse(line: str, next_line: str):
    access_log: AccessLog = {"ip": "", "port": "", "date": ""}

    if "IP Address" in line:
        [_, full_ip] = line.replace("\n", "").split("IP Address ")

        ipv6_match = re.search(regex_ipv6, full_ip)
        ipv4_match = re.search(regex_ipv4, full_ip.split(":")[0])

        # ipv6 with port
        if "]:" in full_ip:
            [ip, port] = full_ip.replace("[", "").split("]:")
            access_log["ip"] = ip
            access_log["port"] = port
        # ipv6 without port
        elif ipv6_match:
            access_log["ip"] = full_ip
            access_log["port"] = ""
        # all ipv4 matches
        elif ipv4_match:
            # ipv4 with port
            if ":" in full_ip:
                [ip, port] = full_ip.split(":")
                access_log["ip"] = ip
                access_log["port"] = port
            # ipv4 without port
            else:
                access_log["ip"] = full_ip
                access_log["port"] = ""

        if "Time" in next_line:
            [_, time] = next_line.replace("\n", "").split("Time ")
            access_log["date"] = time
        # print(access_log)
        return access_log
    else:
        return None


def log_parser(file):
    file_path = Path(file)

    user_logs: UserAcessLogs = {"service": "", "target": "", "logs": []}

    with open(file_path, "rt", encoding="utf-8") as fp:
        lines = fp.readlines()

        service_index = find_index("Service", lines)
        target_index = find_index("Target", lines)
        ips_index = find_exact_index("Ip Addresses", lines)

        [_, service] = lines[service_index].split(" ")
        [_, target] = lines[target_index].split(" ")

        user_logs["service"] = service
        user_logs["target"] = target

        for index, line in enumerate(lines):
            if index < ips_index + 1:
                continue

            if index + 1 < len(lines):
                access_log = log_parse(line, next_line=lines[index + 1])
                if access_log:
                    user_logs["logs"].append(access_log)

        return user_logs


def get_ips_info(user_logs: UserAcessLogs):
    ips_list = [log["ip"] for log in user_logs["logs"]]

    ips_list_by_100 = numpy.array_split(ips_list, math.ceil(len(ips_list) / 100))

    ips_results: list[InfoIP_API] = []

    try:
        for ips in ips_list_by_100:
            body = json.dumps(ips.tolist())
            response = requests.post(IP_URL, data=body)

            data: list[InfoIP_API] = response.json()
            ips_results.extend(data)

        # with open("data.json", "w+") as fj:
        #     json.dump(ips_results, fj)
        return ips_results

    except Exception as e:
        print("error", e)

        return ips_results


def create_logs_sheet(user_logs: UserAcessLogs, ips_results: list[InfoIP_API]):
    pass


def process_logs(file: str):
    user_logs = log_parser(file)

    # ips_results = get_ips_info(user_logs)
    with open("data.json", "r+") as fj:
        ips_results:list[InfoIP_API] = json.load(fj)

    print(len(ips_results))

    create_logs_sheet(user_logs, ips_results)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--file", required=True, type=str)

    args = parser.parse_args()

    process_logs(args.file)
