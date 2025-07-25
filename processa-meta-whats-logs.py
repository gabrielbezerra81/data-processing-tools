import re
from bs4 import BeautifulSoup
import os
import subprocess
import argparse
import sys
import zipfile
import os
import time
import shutil

folders_to_rename = {}


def process_html_file(file_path):
    # Ler conteúdo do HTML
    html_content = ""
    with open(file_path, "r", encoding="utf-8") as f:
        html_content = f.read()

    isMeta = False
    isWhats = False

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
        for line in pure_text.splitlines()
        if line.strip() and not line.startswith("Meta Platforms Business Record")
    ]

    # Encontrar início em "Service"
    start = next((i for i, line in enumerate(lines) if line == "Service"), None)
    if start is None:
        print("Cabeçalho 'Service' não encontrado.")
        exit()

    lines = lines[start:]

    isWhats = "WhatsApp" in lines[1]
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

    file_name = file_info.get("file_name")
    account_identifier = file_info.get("account_identifier")

    save_converted_text_file(
        file_path, file_name, text_content, account_identifier, isWhats
    )


def generate_text_file_name(lines, html_file_path, date_hour):
    service = lines[1]

    original_name = os.path.basename(html_file_path).replace(".html", "")
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

    return {"file_name": file_name, "account_identifier": account_identifier}


def save_converted_text_file(*args):
    global folders_to_rename
    html_file_path, file_name, text_content, account_identifier, isWhats = args

    old_path = os.path.dirname(html_file_path)

    identifier_folder_name = old_path.replace(
        os.path.basename(old_path), account_identifier
    )

    folders_to_rename[old_path] = {
        "path": identifier_folder_name,
        "account_identifier": account_identifier,
        "is_whats": isWhats,
    }

    text_file_path = os.path.join(old_path, file_name)

    with open(text_file_path, "w", encoding="utf-8") as file:
        file.write(text_content)
        print(f"Salvo: {text_file_path}")


def process_zip_files(*, root_path):
    root_dir_list = os.listdir(root_path)

    directories = []

    try:
        for file in root_dir_list:
            is_zip = file.endswith(".zip")

            if is_zip:
                file_path = os.path.join(root_path, file)
                destination_directory = file_path.replace(".zip", "")
                directories.append(destination_directory)
                with zipfile.ZipFile(file_path, "r") as zip_ref:
                    os.makedirs(destination_directory, exist_ok=True)
                    zip_ref.extractall(destination_directory)

        for dir in directories:
            while not os.path.exists(dir):
                print("Esperando descompactar...")
                time.sleep(2)
    except Exception as e:
        print(f"Unzip error: {e}")


def process_folders_in_path(root_path):
    global folders_to_rename

    # try to process zip files
    process_zip_files(root_path=root_path)

    root_dir_list = os.listdir(root_path)

    """
    Procura arquivos .html em subpastas 1 nível abaixo de raiz
    e executa salvar_html_como_txt para cada um.
    """
    for folder in root_dir_list:
        folder_path = os.path.join(root_path, folder)
        if os.path.isdir(folder_path):
            # Para cada subpasta, listar arquivos .html
            for file in os.listdir(folder_path):
                if file.lower().endswith(".html"):
                    html_path = os.path.join(folder_path, file)
                    process_html_file(html_path)

    # renomeia os diretorios extraídos para o nome do identificador (email, telefone)
    try:
        for old_path in folders_to_rename:
            new_path = folders_to_rename[old_path].get("path")
            is_whats = folders_to_rename[old_path].get("is_whats")

            if os.path.exists(new_path) and old_path != new_path:
                shutil.rmtree(new_path)

            os.renames(old_path, new_path)

            if is_whats:
                os.makedirs(os.path.join(new_path, "bilhetagem"), exist_ok=True)
    except Exception as e:
        print(f"Erro ao renomear diretórios: {e}")


def get_arguments():
    parser = argparse.ArgumentParser(description="Processador de logs e bilhetagem")
    parser.add_argument(
        "--pasta_raiz",
        type=str,
        required=True,
        help="Pasta raiz contendo subpastas com arquivos html",
    )
    parser.add_argument(
        "--cookie",
        type=str,
        required=False,
        help="Cookie de autorização do site do Peron",
    )

    args = parser.parse_args()

    return args


if __name__ == "__main__":
    args = get_arguments()

    root_path = args.pasta_raiz
    cookie = args.cookie

    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
    peron_script_path = os.path.join(SCRIPT_DIR, "processa-arquivos-peron.py")

    params = [
        "python",
        peron_script_path,
        root_path,
    ]

    if cookie:
        params.append(cookie)

    process_folders_in_path(root_path)

    result = subprocess.run(params)
    if result.returncode == 2:
        sys.exit(result.returncode)
