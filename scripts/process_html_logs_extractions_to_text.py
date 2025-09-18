import re
from bs4 import BeautifulSoup
import argparse
import zipfile
import time
import shutil
from typing import TypedDict
from pathlib import Path
from scripts.zip_tools import recursive_delete_zips


class FolderRenameItem(TypedDict):
    path: Path
    account_identifier: str
    is_whats: bool
    file_name: str
    is_bilhetagem: bool


class FullFileName(TypedDict):
    file_name: str
    account_identifier: str
    date_hour: str


folders_to_rename: dict[str, FolderRenameItem] = {}


def process_html_file(file_path: Path):
    # Ler conteúdo do HTML
    html_content = ""
    with open(file_path, "r", encoding="utf-8") as f:
        html_content = f.read()

    isMeta = False
    is_whats = False

    # Extrair data do campo "Generated"
    date_pattern = r">(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) UTC<"
    match = re.search(date_pattern, html_content)

    if not match:
        print("Data após 'Generated' não encontrada.")
        exit()

    date_hour = match.group(1)

    # Extrair texto puro
    soup = BeautifulSoup(html_content, "html.parser")
    pure_text = soup.get_text(separator="\n", strip=True)

    # Separar linhas e limpar
    lines = [
        line.strip()
        for line in pure_text.splitlines()
        if line.strip() and not line.startswith("WhatsApp Business Record Page")
    ]

    # Separar linhas e limpar
    lines = [
        line.strip()
        for line in lines
        if line.strip() and not line.startswith("Meta Platforms Business Record")
    ]

    # Encontrar início em "Service"
    start = next((i for i, line in enumerate(lines) if line == "Service"), None)
    if start is None:
        print("Cabeçalho 'Service' não encontrado.")
        exit()

    lines = lines[start:]

    is_whats = "WhatsApp" in lines[1]
    isMeta = "Facebook" in lines[1] or "Instagram" in lines[1]

    # Cabeçalhos que ficam sempre sozinhos
    solo_headers = {"Message Log", "Message", "Call Log", "Call", "Events"}

    # Campos especiais que SEMPRE devem juntar próxima linha
    upper_letter_fields = {
        "Service",
        "Account Type",
        "First Name",
        "First",
        "Last",
        "Full Name",
        "IP Address",
        "Location",
        "Enabled",
        "Phone Type",
        "Alternate Name",
        "Middle Name",
        "Last Name",
        "Type",
        "Alternate Name Type",
        "Card Type",
        "Payment Credential ID",
        "Country",
        "Zip",
        "State",
        "City",
        "Street2",
        "Last Street",
        "First Middle",
    }

    # Regex para detectar hashes ou IDs hexadecimais longos
    regex_hash = re.compile(r"^[A-F0-9]{6,}$")

    # Função para saber se é hash
    def is_hash(line):
        return bool(regex_hash.match(line))

    # Resultado final
    resultLines = []
    i = 0
    while i < len(lines):
        current = lines[i]
        nextLine = lines[i + 1] if i + 1 < len(lines) else None

        if current in solo_headers:
            resultLines.append(current)
            i += 1
        elif current in upper_letter_fields:
            # Sempre junta próxima linha, mesmo maiúscula
            if nextLine and nextLine not in upper_letter_fields:
                resultLines.append(f"{current} {nextLine}")
                i += 2
            else:
                resultLines.append(current)
                i += 1
        else:
            # Caso geral
            if nextLine:
                # Se a próxima linha é um hash, junta
                if is_hash(nextLine):
                    resultLines.append(f"{current} {nextLine}")
                    i += 2
                # Se próxima começa minúscula ou dígito, junta
                elif (
                    nextLine[0].islower()
                    or nextLine[0].isdigit()
                    or nextLine[0] in "+@"
                ):
                    resultLines.append(f"{current} {nextLine}")
                    i += 2
                else:
                    # Próxima parece outro cabeçalho
                    resultLines.append(current)
                    i += 1
            else:
                resultLines.append(current)
                i += 1

    # Juntar e salvar
    text_content = "\n".join(resultLines)

    file_info = generate_text_file_name(lines, file_path, date_hour)

    save_converted_text_file(
        html_file_path=file_path,
        file_info=file_info,
        text_content=text_content,
        is_whats=is_whats,
    )


def generate_text_file_name(
    lines: list[str], html_file_path: Path, date_hour: str
) -> FullFileName:
    service = lines[1]

    original_name = html_file_path.stem
    account_identifier = ""

    try:
        index = lines.index("Account Identifier")
        account_identifier = lines[index + 1].replace("+55", "+55 ")
        if account_identifier:
            service += f" {account_identifier}"
    except Exception as e:
        print(f"Account identifier error: {e}")

    date_hour_formatted = date_hour.replace(":", "-").replace(" ", "_")

    file_name = f"{date_hour_formatted} {original_name} {service}.txt"

    return {
        "file_name": file_name,
        "account_identifier": account_identifier,
        "date_hour": date_hour_formatted,
    }


def resolve_textfile_path(file_info: FullFileName, old_path: Path, is_whats: bool):
    file_name = file_info.get("file_name")

    if is_whats:
        sub_folder = old_path
    else:
        # create sub_folder inside identifier folder to prevent overwrite of meta files with
        # identical identifier and dates
        date_hour = file_info.get("date_hour")

        sub_folder = old_path.joinpath(f"{date_hour}-{old_path.name}")
        sub_folder.mkdir(exist_ok=True)

        # copy files from original extracted folder to new sub_folder
        for file in old_path.glob("*"):
            if file.name != sub_folder.name:

                if file.is_dir():
                    shutil.copytree(file, sub_folder.joinpath(file.name))
                    shutil.rmtree(file)
                else:
                    shutil.copy(file, sub_folder)
                    file.unlink()

    text_file_path = sub_folder.joinpath(file_name)

    return text_file_path


def save_converted_text_file(
    *,
    html_file_path: Path,
    file_info: FullFileName,
    text_content: str,
    is_whats: bool,
):
    global folders_to_rename

    file_name = file_info.get("file_name")
    account_identifier = file_info.get("account_identifier")

    old_path = html_file_path.parent
    old_path_str = str(old_path.resolve())

    identifier_folder_name = (
        old_path.joinpath("..").joinpath(account_identifier).resolve()
    )

    is_bilhetagem = "Message Log" in text_content or "bilhetagem" in old_path_str

    folders_to_rename[old_path_str] = {
        "path": identifier_folder_name,
        "account_identifier": account_identifier,
        "is_whats": is_whats,
        "file_name": file_name,
        "is_bilhetagem": is_bilhetagem,
    }

    text_file_path = resolve_textfile_path(file_info, old_path, is_whats)

    with open(text_file_path, "w", encoding="utf-8") as file:
        file.write(text_content)
        print(f"Salvo: {text_file_path}")


def process_zip_files(*, root_path: Path):

    directories: list[Path] = []

    try:
        for file in root_path.iterdir():
            is_zip = file.name.endswith(".zip")

            if is_zip:
                file_path = str(file.resolve())
                destination_directory = file.parent.joinpath(file.stem)
                destination_directory.mkdir(exist_ok=True)

                directories.append(destination_directory)
                with zipfile.ZipFile(file_path, "r") as zip_ref:

                    zip_ref.extractall(destination_directory)

        for dir in directories:
            while not dir.exists():
                print("Esperando descompactar...")
                time.sleep(2)
    except Exception as e:
        print(f"Unzip error: {e}")


def rename_folders():
    # renomeia os diretorios extraídos para o nome do identificador (email, telefone)
    global folders_to_rename
    for old_path in folders_to_rename:
        try:

            new_path = folders_to_rename[old_path].get("path")
            is_whats = folders_to_rename[old_path].get("is_whats")
            is_bilhetagem = folders_to_rename[old_path].get("is_bilhetagem")

            if is_bilhetagem:
                file_name = (
                    folders_to_rename[old_path].get("file_name").replace(".txt", "")
                )
                new_path = new_path.parent.joinpath(file_name)

            both_path_exists = Path(old_path).exists() and new_path.exists()

            if both_path_exists and old_path != new_path:
                shutil.copytree(old_path, new_path, dirs_exist_ok=True)
                shutil.rmtree(old_path)
            else:
                Path.rename(Path(old_path), new_path)

            if is_whats and not is_bilhetagem:
                bilhetagem_folder = new_path.joinpath("bilhetagem")
                bilhetagem_folder.mkdir(exist_ok=True)
        except Exception as e:
            print(f"Erro ao renomear diretórios: {e}")


def process_html_folders_in_path(root_path: str, level=0):
    root = Path(root_path)

    # try to process zip files
    if level == 0:
        process_zip_files(root_path=root)

    """
    Procura arquivos .html em subpastas 1 nível abaixo de raiz
    e executa salvar_html_como_txt para cada um.
    """
    for item in root.iterdir():
        if item.is_dir():
            # Para cada subpasta, listar arquivos .html
            for sub_item in item.iterdir():
                if "preservation" not in sub_item.name and sub_item.name.endswith(
                    ".html"
                ):
                    process_html_file(sub_item.resolve())
                if "bilhetagem" in str(sub_item.resolve()) and level == 0:
                    bilhetagem_path = item.joinpath("bilhetagem")
                    process_zip_files(root_path=bilhetagem_path)
                    process_html_folders_in_path(bilhetagem_path, level=1)

    if level == 0:
        rename_folders()


def get_arguments():
    parser = argparse.ArgumentParser(description="Processador de logs e bilhetagem")
    parser.add_argument(
        "--pasta_raiz",
        type=str,
        required=True,
        help="Pasta raiz contendo subpastas com arquivos html",
    )

    args = parser.parse_args()

    return args


def process_html_logs_extractions_to_text(root_path: str):
    process_html_folders_in_path(root_path)

    recursive_delete_zips(root_path)


if __name__ == "__main__":
    args = get_arguments()

    root_path: str = args.pasta_raiz

    process_html_logs_extractions_to_text(root_path)
