import hashlib


def calculate_sha256(file_path: str):
    sha256 = hashlib.sha256()
    print(f"calculando hash para o arquivo: {file_path}...\n")
    try:
        with open(file_path, "rb+") as file:
            while chunk := file.read(8192):
                sha256.update(chunk)
        return sha256.hexdigest()
    except Exception as e:
        return None


original_hash = "52b7b5e3873a679991e979e8fc9766376aedc42a373fdae21b75bd4e0b598a78"


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 2:
        print("Use: script.py <file_path>")
        sys.exit(1)

    path = sys.argv[1]

    calculated = calculate_sha256(path)

    is_equal = "Sim" if calculated == original_hash else "Não"

    print(f"hashes iguais? {is_equal}")
