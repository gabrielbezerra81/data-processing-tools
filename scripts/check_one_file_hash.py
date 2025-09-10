from pathlib import Path
from scripts.hash_report_tools import Reporter, Hasher, HashFunc


def check_one_file_hash(file_path: str, original_hash: str, hash_func: HashFunc):
    file = Path(file_path)

    Reporter.configure_pdf()

    Reporter.hashes_count += 1
    print(f"\nIniciando verificação\n")

    result = Hasher.hash_comparator(file, original_hash, hash_func=hash_func)

    file_report = Reporter.create_file_report(
        file,
        hash_not_found=not original_hash,
        has_collision=not result.get("success"),
        original_hash=original_hash,
        generated_hash=result.get("generated_hash"),
    )

    Reporter.add_report_to_pdf(file_report)

    Reporter.print_file_report(file_report)

    Reporter.save_report_pdf(file.parent.resolve())

    return result
