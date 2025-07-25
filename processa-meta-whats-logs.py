import re
from bs4 import BeautifulSoup
import os
import subprocess
import argparse
import sys


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

    file_name = generate_text_file_name(lines, file_path, date_hour)

    save_converted_text_file(file_path, file_name, text_content)


def generate_text_file_name(lines, html_file_path, date_hour):
    service = lines[1]

    original_name = os.path.basename(html_file_path).replace(".html", "")
    account_identifier = ""

    try:
        index = lines.index("Account Identifier")
        account_identifier = lines[index + 1]
        if account_identifier:
            service += f" {account_identifier}"
    except:
        pass

    file_name = (
        date_hour.replace(":", "-").replace(" ", "_")
        + f" {original_name} {service}"
        + ".txt"
    )

    return file_name


def save_converted_text_file(html_file_path, file_name, text_content):
    folder_name = file_name.replace(".txt", "")

    text_file_path = html_file_path.replace("records.html", "")

    if "preservation-1" in html_file_path:
        text_file_path = html_file_path.replace("preservation-1.html", "")

    folder_path = os.path.join(text_file_path, "..", folder_name)

    if not os.path.exists(folder_path):
        os.makedirs(folder_path, exist_ok=True)

    text_file_path = os.path.join(folder_path, file_name)

    with open(text_file_path, "w", encoding="utf-8") as file:
        file.write(text_content)
        print(f"Salvo: {text_file_path}")


def process_folders_in_path(root_path):
    """
    Procura arquivos .html em subpastas 1 nível abaixo de raiz
    e executa salvar_html_como_txt para cada um.
    """
    # Listar todos os diretórios 1 nível abaixo
    for folder in os.listdir(root_path):
        folder_path = os.path.join(root_path, folder)
        if os.path.isdir(folder_path):
            # Para cada subpasta, listar arquivos .html
            for file in os.listdir(folder_path):
                if file.lower().endswith(".html"):
                    html_path = os.path.join(folder_path, file)
                    print(html_path)
                    process_html_file(html_path)


if __name__ == "__main__":

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
