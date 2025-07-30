import os
import zipfile


def recursive_create_zip_list(root_path):
    try:
        files = []

        elements = os.listdir(root_path)

        for item in elements:
            item_full_path = os.path.join(root_path, item)
            if zipfile.is_zipfile(item_full_path):
                files.append(item_full_path)
            elif os.path.isdir(item_full_path):
                append_files = recursive_create_zip_list(item_full_path)
                files.extend(append_files)

        return files

    except Exception as e:
        print(e)
        return []


def recursive_delete_zips(root_path):
    files = recursive_create_zip_list(root_path)
    print(f"deletando {len(files)} arquivos zip")

    for file in files:
        try:
            os.remove(file)
        except Exception as e:
            print(e)


def recursive_unzip_files(root_path):
    files = recursive_create_zip_list(root_path)
    print(f"descompactando {len(files)} arquivos zips")

    for file in files:
        try:
            dir = os.path.dirname(file)
            zipfile.ZipFile(file).extractall(dir)
            os.remove(file)
        except Exception as e:
            print(e)
