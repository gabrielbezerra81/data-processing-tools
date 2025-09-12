from pathlib import Path
import json
from typing import TypedDict
from datetime import datetime
import argparse

from scripts.ip_api import get_ips_info, AccessLog, UserAcessLogs
from scripts.create_logs_sheet import create_logs_sheet
from scripts.ip_tools import extract_ip_port


IPData_Item = TypedDict("IPData_Item", {"ipAddress": str, "dateTimeChangedUtc": str})

ProcessResult = TypedDict(
    "ProcessResult",
    {
        "success": bool,
        "message": str,
    },
)


class MSA_IP_Data(TypedDict):
    startDateTimeUtc: str
    endDateTimeUtc: str
    ipData: list[IPData_Item]
    identifier: str
    identifierType: str
    requestId: str
    recordLocatorId: str


def extract_user_log(file: Path, users_accesslogs: dict[str, UserAcessLogs]):
    json_content = file.read_text("utf-8")
    data: MSA_IP_Data = json.loads(json_content)

    identifier = data["identifier"]

    if not users_accesslogs.get(identifier):
        users_accesslogs[identifier] = {
            "identifier": identifier,
            "service": "Microsoft",
            "logs": [],
        }

    for ip_data in data["ipData"]:
        result = extract_ip_port(ip_data["ipAddress"])

        utc_date = datetime.fromisoformat(ip_data["dateTimeChangedUtc"])
        current_timezone = datetime.now().tzinfo
        local_date = utc_date.astimezone(current_timezone)

        log: AccessLog = {
            "ip": result.get("ip"),
            "port": result.get("port"),
            "date": local_date,
        }

        users_accesslogs[data["identifier"]]["logs"].append(log)


def process_microsoft(path: str) -> ProcessResult:
    try:
        search_path = Path(path)
        save_path = search_path.parent.joinpath("processamentos microsoft")

        save_path.mkdir(exist_ok=True)

        users_accesslogs: dict[str, UserAcessLogs] = {}

        for file in search_path.rglob("ConsIpDataOnly*.json"):
            extract_user_log(file, users_accesslogs)

        for user in users_accesslogs:
            user_logs = users_accesslogs[user]

            ips_results = get_ips_info(user_logs)
            create_logs_sheet(
                path=save_path, ips_results=ips_results, user_logs=user_logs
            )

        result: ProcessResult = {
            "success": True,
            "message": "Os dados foram processados na pasta 'processamentos microsoft'",
        }
        return result

    except Exception as e:
        print("ms error ", e)
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

    process_microsoft(args.pasta)
