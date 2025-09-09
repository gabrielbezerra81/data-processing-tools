from pathlib import Path
import argparse
import openpyxl
from openpyxl.cell import Cell, MergedCell
from scripts.process_files_peron import process_files_peron


def process_cartpanda(path: str):
    file_path = Path(path)

    save_folder = file_path.parent.joinpath("processamentos cartpanda")

    save_folder.mkdir(exist_ok=True)

    users_accesslogs: dict[str, str] = {}

    workbook = openpyxl.load_workbook(file_path.resolve())

    sheet = workbook.active

    if not sheet:
        print("Erro ao processar planilha")
        return

    for row in sheet.iter_rows(min_row=2):

        create_acesslog_entry(row, users_accesslogs)

    logs_content = ""

    for user in users_accesslogs:
        log = users_accesslogs[user]

        logs_content += log + "\n\n"

    log_new_path = save_folder.joinpath(f"access-log-todos.txt")

    with open(log_new_path, "wt+") as log_file:
        log_file.write(logs_content)

    process_files_peron(str(save_folder.resolve()))


def create_acesslog_entry(
    row: tuple[Cell | MergedCell, ...],
    users_accesslogs: dict[str, str],
):
    [id, email, ip, user_agent, login_at] = row

    # if ":" not in ip.value:
    #     return

    if not users_accesslogs.get(email.value):
        users_accesslogs[email.value] = (
            f"Service Instagram\nAccount Identifier {email.value}\nLogins"
        )

    users_accesslogs[email.value] += f"\nIP Address {ip.value}"

    if login_at.value:
        users_accesslogs[email.value] += f"\nTime {login_at.value}"


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
