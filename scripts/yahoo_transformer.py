from pathlib import Path
from typing import TypedDict
from datetime import datetime
import argparse

from scripts.ip_api import get_ips_info, UserAcessLogs
from scripts.create_logs_sheet import create_logs_sheet
import locale


ProcessResult = TypedDict(
    "ProcessResult",
    {
        "success": bool,
        "message": str,
    },
)


def extract_userlog(file: Path, users_accesslogs: dict[str, UserAcessLogs]):
    with open(file, "rt") as fp:

        lines = fp.readlines()

        # yahoo logs has month in english locale
        locale.setlocale(locale.LC_ALL, "en_US")

        for line in lines:
            [user, ip, port, month, day, year, hour_min_sec] = line.split(" ")
            [hour, minute, second] = hour_min_sec.replace("\n", "").split(":")

            if not users_accesslogs.get(user):
                users_accesslogs[user] = {
                    "identifier": user,
                    "service": "Yahoo",
                    "logs": [],
                }

            utc_date = datetime.strptime(
                f"{year}-{month}-{day} {hour}:{minute}:{second} +0000",
                "%Y-%B-%d %H:%M:%S %z",
            )

            users_accesslogs[user]["logs"].append(
                {"ip": ip, "port": port, "date": utc_date}
            )

        # reverse locale
        locale.setlocale(locale.LC_ALL, "pt_BR")


def process_yahoo(path: str):
    try:
        search_path = Path(path)

        users_accesslogs: dict[str, UserAcessLogs] = {}

        for file in search_path.glob("log*.txt", case_sensitive=False):
            extract_userlog(file, users_accesslogs)

        for user in users_accesslogs:
            user_logs = users_accesslogs.get(user)

            ips_results = get_ips_info(user_logs)

            create_logs_sheet(
                path=search_path,
                user_logs=user_logs,
                ips_results=ips_results,
            )

        result: ProcessResult = {
            "success": True,
            "message": "Os logs foram processados na mesma pasta de origem",
        }
        return result
    except Exception as e:
        print("yahoo error ", e)
        result: ProcessResult = {
            "success": False,
            "message": "Erro no processamento dos dados",
        }
        return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser("Manipulador de dados json da Microsoft")

    parser.add_argument(
        "--pasta",
        type=str,
        required=True,
        help="Pasta raiz da telemática da Microsoft",
    )

    args = parser.parse_args()

    process_yahoo(args.pasta)
