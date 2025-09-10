from pathlib import Path
import re
from abc import ABC
import hashlib
from typing import TypedDict, Literal
from fpdf import FPDF

chunk_size = 1024 * 32

successIcon = "✅"
errorIcon = "❌"

Color = Literal["green", "black", "red"]


class PDFSection(TypedDict):
    text: str
    color: Color
    collision: bool


class CompareResult(TypedDict):
    success: bool
    message: str
    generated_hash: str


HashFunc = Literal["SHA256", "SHA512"]


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

    @classmethod
    def hash_comparator(
        self, file: str, original_hash: str, hash_func: HashFunc
    ) -> CompareResult:
        generated_hash = ""
        path = Path(file)

        if hash_func == "SHA256":
            generated_hash = Hasher.calculate_sha256(path)
        elif hash_func == "SHA512":
            generated_hash = Hasher.calculate_sha512(path)
        else:
            generated_hash = Hasher.calculate_sha256(path)

        is_equal = generated_hash == original_hash

        info = f"\n\nHash original:\n{original_hash}\n\nHash gerada:\n{generated_hash}"

        if is_equal:
            return {
                "success": True,
                "message": f"Hashs são iguais.{info}",
                "generated_hash": generated_hash,
            }
        else:
            return {
                "success": False,
                "message": f"As hashes são diferentes.{info}",
                "generated_hash": generated_hash,
            }


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

        report: PDFSection = {
            "text": text,
            "color": color,
            "collision": has_collision or hash_not_found,
        }

        return report

    @classmethod
    def add_report_to_pdf(self, file_report: PDFSection):
        Reporter.verified_files += 1

        if file_report["collision"]:
            Reporter.collisions += 1

        Reporter.pdf_sections.append(file_report)

    @classmethod
    def print_file_report(self, file_report: PDFSection):
        print(file_report.get("text"))

        print(
            f"Arquivos verificados: {Reporter.verified_files}/{Reporter.hashes_count}"
        )

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
