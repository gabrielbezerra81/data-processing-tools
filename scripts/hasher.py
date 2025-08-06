from pathlib import Path
import re
from abc import ABC
import hashlib
from typing import TypedDict, Literal

chunk_size = 1024 * 32


class CompareResult(TypedDict):
    success: bool
    message: str


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
            return {"success": True, "message": f"Hashs são iguais.{info}"}
        else:
            return {"success": False, "message": f"As hashes são diferentes.{info}"}
