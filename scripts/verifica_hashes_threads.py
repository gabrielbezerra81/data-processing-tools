import csv
from natsort import natsorted
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
import argparse
from pathlib import Path
from scripts.google_pdf_reader import read_google_hashes_pdf
from scripts.hash_report_tools import Hasher, Reporter
import py7zr

successIcon = "✅"
errorIcon = "❌"

google_pdf_filename = str("Valores de Hash")


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

        print(py7zr.is_7zfile(item.resolve()))

        if is_dir and level == 0:
            subfolder_files = create_files_list(item, level=1).get("folder_files", [])
        elif item.name.endswith(".zip"):
            folder_files.append(item)
        elif item.name.endswith(".7z"):
            folder_files.append(item)
        elif py7zr.is_7zfile(item.resolve()):
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
            report = future.result()

            Reporter.add_report_to_pdf(report)

            Reporter.print_file_report(report)

    Reporter.save_report_pdf(path)

    return {}


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
