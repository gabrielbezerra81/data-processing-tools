from pypdf import PdfReader
import argparse
import pathlib


pdf_parts: list[str] = []

page_y = {"page_zero_y": 550, "all_pages_y": 660}

current_page_y = page_y["page_zero_y"]


def pdf_visitor_body(text: str, cm, tm, font_dict, font_size):
    global current_page_y
    y: float = cm[5]

    if 50 < y < current_page_y:
        if text == "":
            text = text.replace("", "\n")

        pdf_parts.append(text)


def read_google_hashes_pdf(pdf_path: str):

    global current_page_y

    reader = PdfReader(pdf_path)

    for index, page in enumerate(reader.pages):
        if index > 0:
            current_page_y = page_y.get("all_pages_y")

        page.extract_text(0, visitor_text=pdf_visitor_body)

    path = pathlib.Path(pdf_path)
    dir_path = path.parent
    new_textfile_path = dir_path.joinpath("hashes.txt")

    with open(new_textfile_path, "w") as file:
        file.seek(0)
        file.truncate()
        file.writelines(pdf_parts)


if __name__ == "__main__":
    parser = argparse.ArgumentParser("Leitor de arquivo hash do google")

    parser.add_argument(
        "--arquivo-pdf", type=str, required=True, help="Arquivo pdf de hashes do Google"
    )

    args = parser.parse_args()

    pdf_path: str = args.arquivo_pdf
    read_google_hashes_pdf(pdf_path)
