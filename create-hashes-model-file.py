import os
import argparse


if __name__ == "__main__":
    import sys

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

    folder_path = args.pasta

    files = os.listdir(folder_path)

    zip_files = [file for file in files if file.endswith(".zip")]

    for index in range(len(zip_files)):

        if (index + 1) != len(zip_files):
            zip_files[index] += "-hash\n"
        else:
            zip_files[index] += "-hash"

    with open(os.path.join(folder_path, "hashes.txt"), "wt") as file:
        file.seek(0)
        file.truncate()
        file.writelines(zip_files)
        print(f"{len(zip_files)} arquivos foram encontrados e salvos em hashes.txt")
