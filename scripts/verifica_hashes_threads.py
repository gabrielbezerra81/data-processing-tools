import hashlib
import re
from fpdf import FPDF
import csv
from abc import ABC
from natsort import natsorted
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
import argparse
from pathlib import Path
from typing import TypedDict, Literal
from scripts.google_pdf_reader import read_google_hashes_pdf

successIcon = "✅"
errorIcon = "❌"

google_pdf_filename = str("Valores de Hash")
chunk_size = 1024 * 32

Color = Literal["green", "black", "red"]


class PDFSection(TypedDict):
    text: str
    color: Color
    collision: bool


class Hasher(ABC):
    @classmethod
    def generate_file_hash(self, file_path: Path, is_google_hashes: bool):
        generated_hash = (
            Hasher.calculate_sha512(file_path)
            if is_google_hashes
            else Hasher.calculate_sha256(file_path)
        )

        return generated_hash

    @classmethod
    def calculate_sha256(self, file_path: Path):
        sha256 = hashlib.sha256()
        try:
            with open(file_path, "rb+") as file:
                while chunk := file.read(chunk_size):
                    sha256.update(chunk)
            return sha256.hexdigest()
        except Exception as e:
            return None

    @classmethod
    def calculate_sha512(self, file_path: Path):
        sha512_hash = hashlib.sha512()
        try:
            with open(file_path, "rb") as file:
                while chunk := file.read(chunk_size):
                    sha512_hash.update(chunk)
            return sha512_hash.hexdigest()
        except Exception as e:
            print(f"An error occurred: {e}")
            return None

    @classmethod
    def extract_sha256(self, text: str):
        pattern = r"\b[a-f0-9]{64}\b"
        result = re.search(pattern, text)
        if result:
            return result.group(0)
        return None

    @classmethod
    def extract_sha512(self, text: str):
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
    pdf_sections: list[PDFSection] = []

    @classmethod
    def clear_reporter(self):
        Reporter.collisions = 0
        Reporter.verified_files = 0
        Reporter.hashes_count = 0
        Reporter.pdf_sections = []
        Reporter.pdf = FPDF()

    @classmethod
    def configure_pdf(self):
        Reporter.pdf.add_page()
        Reporter.pdf.set_font("Arial", size=12)

    @classmethod
    def add_text_to_pdf(self, text: str):
        formatted_text = text.replace(successIcon, "[OK] -").replace(
            errorIcon, "[ERRO] -"
        )
        Reporter.pdf.multi_cell(0, 10, formatted_text, align="L")

    @classmethod
    def set_pdf_text_color(self, color: Color):
        if color == "green":
            Reporter.pdf.set_text_color(0, 150, 0)
        elif color == "red":
            Reporter.pdf.set_text_color(255, 0, 0)
        elif color == "black":
            Reporter.pdf.set_text_color(0, 0, 0)

    @classmethod
    def create_file_report(
        self,
        file_name: str,
        hash_not_found: bool,
        has_collision: bool,
        original_hash: str,
        generated_hash: str | None,
    ):
        text = ""

        indent = 6 * " "

        hashes_text = f"{indent}original: {original_hash}\n{indent}hash gerada: {generated_hash}\n"

        color = ""

        if hash_not_found:
            text = f"{errorIcon} {file_name} não possui hash no arquivo de hashes.txt\n"
            color = "red"

        elif has_collision:
            text = f"{errorIcon} {file_name} houve colisão de hash\n"
            color = "red"
        else:
            text = f"{successIcon} {file_name} foi verificado com sucesso\n"
            color = "green"

        text += hashes_text + "\n"

        return {
            "text": text,
            "color": color,
            "collision": has_collision or hash_not_found,
        }

    @classmethod
    def save_report_pdf(self, folder_path: Path):
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

        path = folder_path.joinpath(file_name)

        Reporter.pdf.output(path.resolve())
        Reporter.clear_reporter()


def check_if_google_file(text_file: Path):
    if google_pdf_filename in text_file.name and text_file.name.endswith(".pdf"):
        return True

    return False


def create_google_hashes_file(text_file: Path):
    with open(text_file, "tr+") as file:
        filtered_lines: list[str] = []

        text = file.read()
        if "SHA512" not in text:
            return

        text = text.replace("\n", "")
        # text = text.replace(":", "-")
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


def create_hashes_dict_from_csv(csv_file: Path):
    with open(csv_file, mode="r", newline="") as file:
        csv_reader = csv.reader(file)
        next(csv_reader)

        hashes_dict: dict[str, str] = {}

        for row in csv_reader:
            file_name = row[1]
            hash = row[5]
            hashes_dict[file_name] = hash

        return hashes_dict


def create_hashes_dict_from_txt(txt_file: Path, isSha512: bool):
    hashes_dict: dict[str, str | None] = {}

    with open(txt_file, "tr", encoding="utf-8") as file:
        lines = file.readlines()

        for line in lines:
            splitted = line.replace(" ", "").split(":")
            file_name = splitted[0]
            original_hash = (
                Hasher.extract_sha512(line) if isSha512 else Hasher.extract_sha256(line)
            )
            hashes_dict[file_name] = original_hash

        return hashes_dict


def create_hashes_dict(hashes_path: Path, is_google_hashes: bool):
    hashes_dict: dict[str, str] = {}

    if hashes_path.name.endswith(".csv"):
        hashes_dict = create_hashes_dict_from_csv(hashes_path)
    else:
        if is_google_hashes:
            read_google_hashes_pdf(hashes_path)

            hashes_path = hashes_path.parent.joinpath("hashes.txt")

            create_google_hashes_file(hashes_path)

        hashes_dict = create_hashes_dict_from_txt(
            hashes_path, isSha512=is_google_hashes
        )

    return hashes_dict


def create_files_list(files_folder_path: Path, level: int):
    hashes_path: Path | None = None

    folder_files: list[Path] = []

    for item in files_folder_path.iterdir():
        subfolder_files = []

        is_dir = item.is_dir()

        item = item.resolve()

        if is_dir and level == 0:
            subfolder_files = create_files_list(item, level=1).get("folder_files", [])
        elif item.name.endswith(".zip"):
            folder_files.append(item)
            # adiciona os arquivos contidos nas subpastas em até 1 nível abaixo
        elif item.name.endswith(".gpg"):
            folder_files.append(item)
        elif item.name == "HASHES.txt":
            hashes_path = item
        elif item.name == "hashes.txt":
            hashes_path = item
        elif item.name.endswith(".csv"):
            hashes_path = item
        elif google_pdf_filename in item.name and item.name.endswith(".pdf"):
            hashes_path = item
        elif item.name.endswith(".pdf") and "relatorio_hashes" not in item.name:
            folder_files.append(item)

        folder_files.extend(subfolder_files)

    folder_files = natsorted(folder_files)

    return {"folder_files": folder_files, "hashes_path": hashes_path}


def process_file(args: tuple[Path, Path, dict[str, str], bool]):
    file, files_folder_path, hashes_dict, is_google_hashes = args
    file_name = file.name
    file_path = file.resolve()

    try:
        file_name_in_dict = file_name.replace(" ", "")
        original_hash = hashes_dict.get(file_name_in_dict, None)
        generated_hash = Hasher.generate_file_hash(file_path, is_google_hashes)
        has_collision = original_hash != generated_hash

        if not original_hash:
            raise ValueError("não encontrou a hash original")

        file_report = Reporter.create_file_report(
            file,
            hash_not_found=False,
            has_collision=has_collision,
            original_hash=original_hash,
            generated_hash=generated_hash,
        )

    except Exception as e:
        file_report = Reporter.create_file_report(
            file,
            hash_not_found=not original_hash,
            has_collision=True,
            original_hash=original_hash or "- - - -",
            generated_hash=generated_hash,
        )

    return file_report


def verify_hashes(files_folder_path: str):
    path = Path(files_folder_path)
    if not path.exists():
        print("o caminho da pasta de arquivos não existe")
        sys.exit(1)

    Reporter.configure_pdf()

    object = create_files_list(path, level=0)

    folder_files: list[Path] = object["folder_files"]
    hashes_path: Path | None = object["hashes_path"]

    if not hashes_path:
        msg = "o caminho do arquivo de hashes.txt ou .csv não existe"
        print(msg)
        return {"error": msg}

    hashes_path = hashes_path.resolve()

    is_google_hashes = check_if_google_file(hashes_path)
    hashes_dict = create_hashes_dict(hashes_path, is_google_hashes)

    hashes_count = len(hashes_dict)

    Reporter.hashes_count = hashes_count
    print(f"\nIniciando verificação\n")

    args_list = [
        (file, files_folder_path, hashes_dict, is_google_hashes)
        for file in folder_files
    ]

    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = [executor.submit(process_file, args) for args in args_list]
        for future in as_completed(futures):
            report: PDFSection = future.result()

            Reporter.verified_files += 1

            if report["collision"]:
                Reporter.collisions += 1

            print(report.get("text"))

            print(f"Arquivos verificados: {Reporter.verified_files}/{hashes_count}")

            Reporter.pdf_sections.append(
                {
                    "text": report.get("text"),
                    "color": report.get("color"),
                    "collision": report.get("collision"),
                }
            )

    Reporter.save_report_pdf(path)


if __name__ == "__main__":
    parser = argparse.ArgumentParser("Verificador de hashes de arquivos")
    parser.add_argument(
        "--pasta",
        type=str,
        required=True,
        help="Pasta onde estão os arquivos a serem verificados e o arquivo de hashes",
    )

    args = parser.parse_args()

    folder_path: str = args.pasta
    verify_hashes(folder_path)
