from pathlib import Path
import argparse
import datetime
from scripts.process_html_logs_extractions_to_text import (
    process_html_logs_extractions_to_text,
)
from scripts.ip_api import get_ips_info, AccessLog, UserAcessLogs
from scripts.create_logs_sheet import create_logs_sheet
from scripts.ip_tools import extract_ip_port


BILHETAGEM_KEYWORDS = ["Message Log", "Call Log", "Call Logs"]


def find_index(term: str, array: list):
    index = next(index for index, line in enumerate(array) if term in line)

    return index


def find_exact_index(term: str, array: list[str]):
    index = next(
        index for index, line in enumerate(array) if term == line.replace("\n", "")
    )

    return index


def ip_parse(line: str, next_line: str):
    access_log: AccessLog = {"ip": "", "port": "", "date": ""}

    if "IP Address" in line:
        [_, full_ip] = line.replace("\n", "").split("IP Address ")

        result = extract_ip_port(full_ip)
        access_log["ip"] = result.get("ip")
        access_log["port"] = result.get("port")

        if "Time" in next_line:
            [_, time] = next_line.replace("\n", "").split("Time ")

            string_date = time.replace("UTC", "+0000")
            date = datetime.datetime.strptime(string_date, "%Y-%m-%d %H:%M:%S %z")

            access_log["date"] = date
        # print(access_log)
        return access_log
    else:
        return None


def create_userlogs(file):
    file_path = Path(file)

    user_logs: UserAcessLogs = {"service": "", "identifier": "", "logs": []}

    with open(file_path, "rt", encoding="utf-8") as fp:
        lines = fp.readlines()

        service_index = find_index("Service", lines)
        identifier_index = find_index("Account Identifier", lines)
        ips_index = find_exact_index("Ip Addresses", lines)

        [_, service] = lines[service_index].split(" ")
        [_, identifier] = (
            lines[identifier_index].replace("\n", "").split("Account Identifier ")
        )

        user_logs["service"] = service.replace("\n", "")
        user_logs["identifier"] = identifier

        for index, line in enumerate(lines):
            if index < ips_index + 1:
                continue

            if index + 1 < len(lines):
                access_log = ip_parse(line, next_line=lines[index + 1])
                if access_log:
                    user_logs["logs"].append(access_log)

        return user_logs


def process_logfile(file: str):
    user_logs = create_userlogs(file)

    ips_results = get_ips_info(user_logs)

    # testing only
    # with open("data.json", "r+") as fj:
    #     ips_results: dict[str, InfoIP_API] = json.load(fj)
    path = Path(file).parent

    create_logs_sheet(path=path, user_logs=user_logs, ips_results=ips_results)


def is_file_empty(file_path):
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            content = file.read()

            count = content.count("No responsive records located")

            empty_message = False
            empty_call = False

            if "Message Log\nNo responsive records located" in content:
                empty_message = True

            if "Call Logs\nNo responsive records located" in content:
                empty_call = True

            if empty_message and empty_call and count == 2:
                return True

            return False
    except:
        return False


def is_bilhetagem_file(file_path):
    if "bilhetagem" in file_path:
        return True

    with open(file_path, "r", encoding="utf-8") as file:
        content = file.read()

        return any(word in content for word in BILHETAGEM_KEYWORDS)


def create_files_list(root_path: str):
    current_path = Path(root_path)

    files: list[str] = []

    try:
        for item in current_path.rglob("*"):

            if item.name.endswith(".txt"):
                file_path = str(item.resolve())

                if is_bilhetagem_file(file_path):
                    continue

                if (
                    is_file_empty(file_path)
                    or "instructions" in item.name
                    or "preservation" in item.name
                ):
                    continue

                files.append(file_path)

        return files
    except Exception as e:
        print(f"file list error {e}")
        return files


def process_meta_text_logs(root_path: str):
    process_html_logs_extractions_to_text(root_path)

    files = create_files_list(root_path)

    print(f"Processando {len(files)} arquivos")

    for file in files:
        process_logfile(file)


def get_arguments():
    parser = argparse.ArgumentParser(description="Processador de logs da META")
    parser.add_argument(
        "--pasta_raiz",
        type=str,
        required=True,
        help="Pasta raiz contendo subpastas com arquivos html",
    )

    args = parser.parse_args()

    return args


if __name__ == "__main__":
    # python -m scripts.process_meta_text_logs --pasta_raiz
    args = get_arguments()

    root_path: str = args.pasta_raiz

    process_meta_text_logs(root_path)
