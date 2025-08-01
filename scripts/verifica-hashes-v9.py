import hashlib
import os
import re
from fpdf import FPDF
import csv
from abc import ABC
from natsort import natsorted
import importlib.util
import subprocess
import sys

successIcon = "✅"
errorIcon = "❌"


def check_install_packages(packages):
    """
    Verifica se os pacotes (chave: pip, valor: módulo) estão instalados.
    Se não estiverem, instala com pip.
    """
    for pi_name, module_name in packages.items():
        if importlib.util.find_spec(module_name) is None:
            print(
                f"[!] Módulo '{module_name}' (pip: '{pi_name}') não encontrado. Instalando..."
            )
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", pi_name])
                print(f"[✓] '{pi_name}' instalado com sucesso.")
            except subprocess.CalledProcessError:
                print(f"[X] Falha ao instalar '{pi_name}'.")
        else:
            print(f"[✓] '{module_name}' já está instalado.")


check_install_packages({"fpdf": "fpdf", "natsort": "natsort"})


class Hasher(ABC):
    @classmethod
    def generate_file_hash(self, file_path, is_google_hashes):
        generated_hash = (
            Hasher.calculate_sha512(file_path)
            if is_google_hashes
            else Hasher.calculate_sha256(file_path)
        )

        return generated_hash

    @classmethod
    def calculate_sha256(self, file_path):
        sha256 = hashlib.sha256()
        try:
            with open(file_path, "rb+") as file:
                while chunk := file.read(8192):
                    sha256.update(chunk)
            return sha256.hexdigest()
        except Exception as e:
            return None

    @classmethod
    def calculate_sha512(self, file_path):
        sha512_hash = hashlib.sha512()
        try:
            with open(file_path, "rb") as file:
                while chunk := file.read(8192):
                    sha512_hash.update(chunk)
            return sha512_hash.hexdigest()
        except Exception as e:
            print(f"An error occurred: {e}")
            return None

    @classmethod
    def extract_sha256(self, text):
        pattern = r"\b[a-f0-9]{64}\b"
        result = re.search(pattern, text)
        if result:
            return result.group(0)
        return None

    @classmethod
    def extract_sha512(self, text):
        pattern = r"[0-9a-fA-F]{128}"
        result = re.search(pattern, text)
        if result:
            return result.group(0)
        return None


class Reporter(ABC):
    collisions = 0
    verified_files = 0
    hashes_count = 0
    pdf = FPDF()  # type: ignore
    pdf_sections = []

    @classmethod
    def configure_pdf(self):
        Reporter.pdf.add_page()
        Reporter.pdf.set_font("Arial", size=12)

    @classmethod
    def add_text_to_pdf(self, text):
        formatted_text = text.replace(successIcon, "[OK] -").replace(
            errorIcon, "[ERRO] -"
        )
        Reporter.pdf.multi_cell(0, 10, formatted_text, align="Left text")

    @classmethod
    def set_pdf_text_color(self, color):
        if color == "green":
            Reporter.pdf.set_text_color(0, 150, 0)
        elif color == "red":
            Reporter.pdf.set_text_color(255, 0, 0)
        elif color == "black":
            Reporter.pdf.set_text_color(0, 0, 0)

    @classmethod
    def add_file_report(
        self, file_name, hash_not_found, has_collision, original_hash, generated_hash
    ):
        text = ""
        Reporter.verified_files += 1

        indent = 6 * " "

        hashes_text = f"{indent}original: {original_hash}\n{indent}hash gerada: {generated_hash}\n"

        color = ""

        if hash_not_found:
            Reporter.collisions += 1
            text = f"{errorIcon} {file_name} não possui hash no arquivo de hashes.txt\n"
            color = "red"

        elif has_collision:
            Reporter.collisions += 1
            text = f"{errorIcon} {file_name} houve colisão de hash\n"
            color = "red"
        else:
            text = f"{successIcon} {file_name} foi verificado com sucesso\n"
            color = "green"

        text += hashes_text + "\n"

        Reporter.pdf_sections.append(
            {
                "text": text,
                "color": color,
            }
        )

        return text

    @classmethod
    def save_report_pdf(self, folder_path):
        Reporter.set_pdf_text_color(color="black")
        file_name = "relatorio_hashes.pdf"

        alert_missing_files = ""

        if Reporter.hashes_count > Reporter.verified_files:
            alert_missing_files = "\n** Há arquivos em falta, a quantidade de arquivos verificados foi menor do que a quantidade de hashes encontradas **\n\n"

        head_text = (
            f"Quantidade de hashes encontradas: {Reporter.hashes_count}\n"
            + f"Arquivos verificados: {Reporter.verified_files}\n"
            + f"Verificados com sucesso: {Reporter.verified_files-Reporter.collisions}\n"
            + f"Quantidade de colisões: {Reporter.collisions}\n"
            + alert_missing_files
        )

        Reporter.add_text_to_pdf(head_text)

        for section in Reporter.pdf_sections:
            Reporter.set_pdf_text_color(section.get("color", "black"))
            Reporter.add_text_to_pdf(section.get("text"))

        Reporter.pdf.output(os.path.join(folder_path, file_name))


def check_if_google_file(text_file):
    with open(text_file, "tr+") as file:
        text = file.read()
        text = text.replace("\n", "")
        hasHash = Hasher.extract_sha512(text)

        if hasHash:
            return True
        else:
            return False


def create_google_hashes_file(text_file):
    with open(text_file, "tr+") as file:
        filtered_lines = []

        text = file.read()
        if "SHA512" not in text:
            return

        text = text.replace("\n", "")
        text = text.replace(":", "-")
        text = text.replace(" ", "")

        lines = text.split("SHA512-")

        for line in lines:
            line = line.replace(
                "GoogleLLC1600AmphitheatreParkwMountainView,California94043www.google.com",
                "",
            )

            hash = Hasher.extract_sha512(line)

            if hash:
                line = line.replace(hash, f"{hash}\n")

            if line:
                filtered_lines.append(line)

        file.seek(0)
        file.truncate()
        file.writelines(filtered_lines)


def create_hashes_dict_from_csv(csv_file):
    with open(csv_file, mode="r", newline="") as file:
        csv_reader = csv.reader(file)

        hashes_dict = {}

        for row in csv_reader:
            file_name = row[1]
            hash = row[5]
            hashes_dict[file_name] = hash

        return hashes_dict


def create_hashes_dict_from_txt(txt_file, isSha512):
    hashes_dict = {}

    with open(txt_file, "tr") as file:
        lines = file.readlines()

        for line in lines:
            splitted = line.replace(" ", "").split("-")
            file_name = splitted[0]
            original_hash = (
                Hasher.extract_sha512(line) if isSha512 else Hasher.extract_sha256(line)
            )
            hashes_dict[file_name] = original_hash

        return hashes_dict


def create_hashes_dict(hashes_path, is_google_hashes):
    hashes_dict = {}

    if hashes_path.endswith(".csv"):
        hashes_dict = create_hashes_dict_from_csv(hashes_path)
    elif hashes_path.endswith(".txt"):

        if is_google_hashes:
            create_google_hashes_file(hashes_path)
        hashes_dict = create_hashes_dict_from_txt(hashes_path, is_google_hashes)
    return hashes_dict


def create_files_list(files_folder_path, level):
    hashes_path = ""

    folder_files = []

    for x in os.listdir(files_folder_path):
        subfolder_files = []

        is_dir = os.path.isdir(os.path.join(files_folder_path, x))

        if level == 1:
            x = os.path.join(os.path.basename(files_folder_path), x)

        if is_dir and level == 0:
            subfolder_path = os.path.join(files_folder_path, x)
            subfolder_files = create_files_list(subfolder_path, level=1).get(
                "folder_files", []
            )
        elif x.endswith(".zip"):
            folder_files.append(x)
            # adiciona os arquivos contidos nas subpastas em até 1 nível abaixo
        elif x.endswith(".gpg"):
            folder_files.append(x)
        elif x == "HASHES.txt":
            hashes_path = x
        elif x == "hashes.txt":
            hashes_path = x
        elif x.endswith(".csv"):
            hashes_path = x

        folder_files.extend(subfolder_files)

    folder_files = natsorted(folder_files)

    return {"folder_files": folder_files, "hashes_path": hashes_path}


def verify_hashes(files_folder_path):
    if not os.path.exists(files_folder_path):
        print("o caminho da pasta de arquivos não existe")
        sys.exit(1)

    Reporter.configure_pdf()

    object = create_files_list(files_folder_path, level=0)

    folder_files = object["folder_files"]
    hashes_path = object["hashes_path"]

    if not hashes_path:
        print("o caminho do arquivo de hashes.txt ou .csv não existe")
        sys.exit(1)

    hashes_path = os.path.join(files_folder_path, hashes_path)

    is_google_hashes = check_if_google_file(hashes_path)
    hashes_dict = create_hashes_dict(hashes_path, is_google_hashes)

    Reporter.hashes_count = len(hashes_dict)
    print(f"Arquivos verificados: {Reporter.verified_files}/{Reporter.hashes_count}")

    for file in folder_files:
        file_report = ""

        try:
            # files inside a subfolder should have their folder name removed
            file_name = os.path.basename(file)

            original_hash = hashes_dict.get(file_name, None)

            file_path = os.path.join(files_folder_path, file)

            generated_hash = Hasher.generate_file_hash(file_path, is_google_hashes)

            has_collision = original_hash != generated_hash

            if not original_hash:
                raise ValueError("não encontrou a hash original")

            file_report = Reporter.add_file_report(
                file,
                hash_not_found=False,
                has_collision=has_collision,
                original_hash=original_hash,
                generated_hash=generated_hash,
            )

        except Exception as e:
            file_report = Reporter.add_file_report(
                file,
                hash_not_found=not original_hash,
                has_collision=has_collision,
                original_hash=original_hash or "- - - -",
                generated_hash=generated_hash,
            )

        print(file_report)
        print(
            f"Arquivos verificados: {Reporter.verified_files}/{Reporter.hashes_count}"
        )

    Reporter.save_report_pdf(files_folder_path)


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 2:
        print("Use: python script.py <folder_path>")
        sys.exit(1)
    folder_path = sys.argv[1]

    verify_hashes(folder_path)
