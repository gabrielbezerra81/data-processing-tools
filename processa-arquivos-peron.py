from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import os
import sys
from selenium.common.exceptions import NoSuchElementException


# CONFIGURAÇÕES
cookie_str = "_ga=GA1.1.2104152263.1746708028; _ga_NQ799D13XJ=GS2.1.s1746717031$o2$g1$t1746717175$j0$l0$h0; _ga_NF011H78CX=GS2.1.s1746803384$o3$g1$t1746804077$j0$l0$h0; session=.eJwdzd1ugyAYANBXWXgCMNWkvXQVUi10wsc36x0bLm74QzKXWJu--5Jen4tzJ8scuokc7uTlgxxI2wyVFHit34c3Z-MZf7h2dj2asf_WiYqQDJVBzAzwi7Nzeh4xNVMMSIenucAyt6FCoX8B5eooy6DpJfIyAvXKF3tbQ97aLd8BlKrjQ-ZEr9z4eYMpquc15a6mIYEmlrJgJ_mabl6sf368pi1XX92Rawg6sZsO1jAJN3aRYlE1-MXSeWfYPqJYKyxKRR6Pf0oeSuI.aGUowg.Pimi4rY3oBzSh31sU_md1hJZZew"

URL_BASE = "https://policia.mperon.org"
URL_FORM = f"{URL_BASE}/extractor/access_log"


def create_webdriver(file_path):

    # INICIALIZA O NAVEGADOR
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")

    dir_path = os.path.dirname(file_path)
    prefs = {"download.default_directory": dir_path}
    options.add_experimental_option("prefs", prefs)

    driver = webdriver.Chrome(options=options)
    wait = WebDriverWait(driver, 10)

    # ENTRA NO DOMÍNIO PARA DEFINIR OS COOKIES
    driver.get(URL_BASE)
    add_cookies_from_string(driver, cookie, "policia.mperon.org")

    # ACESSA A PÁGINA DO FORMULÁRIO
    driver.get(URL_FORM)

    return {"driver": driver, "wait": wait}


# FUNÇÃO PARA INSERIR COOKIES
def add_cookies_from_string(driver, cookie, domain):
    parts = cookie.split(";")
    for part in parts:
        if "=" in part:
            name, value = part.strip().split("=", 1)
            driver.add_cookie(
                {
                    "name": name,
                    "value": value,
                    "domain": domain,
                    "path": "/",
                }
            )


def process_files(files, cookie):
    # LOOP PARA ENVIAR CADA ARQUIVO

    try:

        for idx, file in enumerate(files, start=1):

            obj = create_webdriver(file)
            driver = obj["driver"]
            wait = obj["wait"]

            print(f"📄 Enviando arquivo {idx}/{len(files)}: {file}")

            print(file)

            # CLICA NA ABA "Carregar arquivo"
            tabFile = driver.find_element(By.CSS_SELECTOR, 'a[href="#tabFile"]')

            tabFile.click()
            time.sleep(1)

            # AGUARDA O INPUT ESTAR VISÍVEL
            file_input = driver.find_element(By.ID, "import_file")

            # ENVIA O ARQUIVO
            file_input.send_keys(os.path.abspath(file))
            time.sleep(1)

            # CLICA EM "ENVIAR"
            submit_button = wait.until(
                EC.element_to_be_clickable((By.ID, "submit_form"))
            )
            submit_button.click()

            print("✅ Arquivo enviado.")

            # AGUARDA RESPOSTA OU PROCESSAMENTO
            time.sleep(5)

            print("🎉 Todos os arquivos foram processados.")
            driver.quit()
    except NoSuchElementException as e:
        print("ERRO_COOKIE_INVALIDO")
        sys.exit(2)


def create_files_list(root_path):
    files = []
    try:
        elements = os.listdir(root_path)

        for folder in elements:

            folder_path = os.path.join(root_path, folder)
            is_dir = os.path.isdir(folder_path)

            if is_dir:
                folder_items = os.listdir(folder_path)

                for file in folder_items:
                    if file.endswith(".txt") and "instructions" not in file:
                        file_path = os.path.join(folder_path, file)
                        files.append(file_path)

        return files
    except:
        return files


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print(
            "Use: python script.py <root_folder_path>\nor\nUse: python script.py <root_folder_path> <cookie_string>"
        )
        sys.exit(1)

    cookie = cookie_str

    root_path = sys.argv[1]

    if len(sys.argv) == 3:
        cookie = sys.argv[2]

    files = create_files_list(root_path)
    process_files(files, cookie)
