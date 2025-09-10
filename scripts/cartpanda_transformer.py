from pathlib import Path
import argparse
import openpyxl
from openpyxl.cell import Cell, MergedCell

from scripts.ip_api import get_ips_info, AccessLog, UserAcessLogs
from scripts.create_logs_sheet import create_logs_sheet
from scripts.ip_tools import extract_ip_port
import datetime


def process_cartpanda(path: str):
    file_path = Path(path)

    save_folder = file_path.parent.joinpath("processamentos cartpanda")

    save_folder.mkdir(exist_ok=True)

    users_accesslogs: dict[str, UserAcessLogs] = {}

    workbook = openpyxl.load_workbook(file_path.resolve())

    sheet = workbook.active

    if not sheet:
        print("Erro ao processar planilha")
        return

    for row in sheet.iter_rows(min_row=2):
        create_acesslog_entry(row, users_accesslogs)

    for user in users_accesslogs:
        user_logs = users_accesslogs[user]
        ips_results = get_ips_info(user_logs)

        create_logs_sheet(
            path=save_folder, user_logs=user_logs, ips_results=ips_results
        )


def create_acesslog_entry(
    row: tuple[Cell | MergedCell, ...],
    users_accesslogs: dict[str, UserAcessLogs],
):
    [id, email, ip, user_agent, login_at] = row

    if not users_accesslogs.get(email.value):
        users_accesslogs[email.value] = {
            "identifier": email.value,
            "service": "Cartpanda",
            "logs": [],
        }

    result = extract_ip_port(ip.value)

    log: AccessLog = {"ip": result.get("ip"), "port": result.get("port"), "date": ""}

    if login_at.value and isinstance(login_at.value, datetime.datetime):
        string_date = str(login_at.value) + " +0000"

        utc_date = datetime.datetime.strptime(string_date, "%Y-%m-%d %H:%M:%S %z")

        current_timezone = datetime.datetime.now().astimezone().tzinfo

        date: datetime.datetime = utc_date.astimezone(current_timezone)
        log["date"] = date

    users_accesslogs[email.value]["logs"].append(log)


if __name__ == "__main__":
    parser = argparse.ArgumentParser("Manipulador de logs de acesso xlsx da Carpanda")

    parser.add_argument(
        "--arquivo",
        type=str,
        required=True,
        help="Arquivo Authentications-ips.xlsx da Cartpanda",
    )

    args = parser.parse_args()

    process_cartpanda(args.arquivo)
