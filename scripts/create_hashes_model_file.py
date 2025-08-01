import pathlib
import argparse


def create_hashes_file(folder_path: str):
    current_path = pathlib.Path(folder_path)

    zip_files = [file.name for file in current_path.glob("*.zip")]

    for index in range(len(zip_files)):

        if (index + 1) != len(zip_files):
            zip_files[index] += "-hash\n"
        else:
            zip_files[index] += "-hash"

    textfile_path = current_path.joinpath("hashes.txt")

    with open(textfile_path, "wt") as file:
        file.seek(0)
        file.truncate()
        file.writelines(zip_files)
        print(f"{len(zip_files)} arquivos foram encontrados e salvos em hashes.txt")


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
