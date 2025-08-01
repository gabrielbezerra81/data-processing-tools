import pathlib
import zipfile


def recursive_create_zip_list(root_path: str):
    files: list[str] = []

    try:

        path = pathlib.Path(root_path)

        for item in path.rglob("*"):
            item_full_path = str(item.resolve())
            if zipfile.is_zipfile(item_full_path):
                files.append(item_full_path)

        return files

    except Exception as e:
        print(f"create zip list error {e}")
        return files


def recursive_delete_zips(root_path: str):
    files = recursive_create_zip_list(root_path)
    print(f"deletando {len(files)} arquivos zip")

    for file in files:
        path = pathlib.Path(file)
        try:
            if path.exists():
                path.unlink()
        except Exception as e:
            print(f"delete file error {e}")


def recursive_unzip_files(root_path: str):
    files = recursive_create_zip_list(root_path)
    print(f"descompactando {len(files)} arquivos zips")

    for file in files:
        try:
            file_path = pathlib.Path(file)
            dir = str(file_path.parent.resolve())
            zipfile.ZipFile(file).extractall(dir)
            file_path.unlink()
        except Exception as e:
            print(f"unzip error {e}")
