import pathlib
import argparse


def create_hashes_file(folder_path: str):
    current_path = pathlib.Path(folder_path)

    files = []

    zip_files = [file.name for file in current_path.glob("*.zip")]
    files.extend(zip_files)

    zip_files = [file.name for file in current_path.glob("*.7z")]
    files.extend(zip_files)

    exclude = {"relatorio_hashes.pdf"}
    pdf_files = [
        file.name for file in current_path.glob("*.pdf") if file.name not in exclude
    ]
    files.extend(pdf_files)

    for index in range(len(files)):

        if (index + 1) != len(files):
            files[index] += ":hash\n"
        else:
            files[index] += ":hash"

    textfile_path = current_path.joinpath("hashes.txt")

    with open(textfile_path, "wt", encoding="utf-8") as file:
        file.seek(0)
        file.truncate()
        file.writelines(files)
        print(f"{len(files)} arquivos foram encontrados e salvos em hashes.txt")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Cria um modelo de a arquivo hashes.txt"
    )
    parser.add_argument(
        "--pasta",
        type=str,
        required=True,
        help="O caminho da pasta onde estão os arquivos .zip",
    )

    args = parser.parse_args()

    folder_path: str = args.pasta
    create_hashes_file(folder_path)
