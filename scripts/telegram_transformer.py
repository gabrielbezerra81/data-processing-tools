from pathlib import Path
from typing import TypedDict, Literal, NotRequired
from datetime import datetime, timezone
import argparse
import json

from scripts.ip_api import get_ips_info, AccessLog, UserAcessLogs
from scripts.create_logs_sheet import create_logs_sheet, Sheet_Config
from scripts.ip_tools import extract_ip_port


class TelegramUser(TypedDict):
    user_id: str
    display_name: str
    username: NotRequired[str]
    phone_number: str
    ip_address: NotRequired[str]
    timestamp: NotRequired[str]


class TelegramData(TypedDict):
    users: list[TelegramUser]


def create_data_from_json(file: Path):
    data: TelegramData = json.loads(file.read_text("utf-8"))

    user_logs: UserAcessLogs = {
        "identifier": "todos",
        "service": "Telegram",
        "logs": [],
    }

    if not data:
        return user_logs

    for user in data["users"]:
        result = extract_ip_port(user.get("ip_address", ""))

        identifiers_list: list[str] = []

        if dn := user.get("display_name"):
            identifiers_list.append(dn)

        if phone := user.get("phone_number"):
            identifiers_list.append(phone)

        if username := user.get("username"):
            identifiers_list.append(username)

        identifier = " ".join(identifiers_list)

        timestamp = user.get("timestamp")

        date = datetime.fromisoformat(timestamp) if timestamp else ""

        log: AccessLog = {
            "log_identifier": identifier,
            "ip": result.get("ip"),
            "port": result.get("port"),
            "date": date,
        }

        user_logs["logs"].append(log)

    return user_logs


def process_telegram(path: str):
    file = Path(path)

    save_folder = file.parent

    user_logs = create_data_from_json(file)

    ips_results = get_ips_info(user_logs)

    sheet_config: Sheet_Config = {"IP": {"new_name": "IP Registro"}}

    create_logs_sheet(
        path=save_folder,
        ips_results=ips_results,
        user_logs=user_logs,
        sheet_config=sheet_config,
        filename="registro-usuários-telegram",
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser("Manipulador de dados json do Telegram")

    parser.add_argument(
        "--arquivo",
        type=str,
        required=True,
        help="Arquivo json",
    )

    args = parser.parse_args()

    process_telegram(args.arquivo)
