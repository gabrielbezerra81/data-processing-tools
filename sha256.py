import hashlib


def calculate_sha256(file_path):
    sha256 = hashlib.sha256()
    print(f"calculando hash para o arquivo: {file_path}...\n")
    try:
        with open(file_path, "rb+") as file:
            while chunk := file.read(8192):
                sha256.update(chunk)
        return sha256.hexdigest()
    except Exception as e:
        return None


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 2:
        print("Use: script.py <file_path>")
        sys.exit(1)

    path = sys.argv[1]

    print(f"SHA256: {calculate_sha256(path)}")
