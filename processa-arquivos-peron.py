from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import os
import sys
from selenium.common.exceptions import NoSuchElementException
from concurrent.futures import ThreadPoolExecutor, as_completed
from recursize_unzip import unzip_files


# CONFIGURAÇÕES
email = "gabriel.bezerra@mpce.mp.br"
password = "mg-)ju*@GHDp!"

URL_LOGIN = "https://policia.mperon.org/auth/login"
URL_BASE = "https://policia.mperon.org/"
URL_LOG = f"{URL_BASE}/extractor/access_log"
URL_EXTRACTOR = f"{URL_BASE}/extractor/whatsapp"
max_workers = 3
SESSION_COOKIES = []
FILE_WAIT_TIME = {2000: 7, 3000: 9, 4000: 10, 5000: 12}


email_id = "inputEmail"
password_id = "inputPassword"
login_button_id = "logLink"


def get_file_wait_by_size(file):
    global FILE_WAIT_TIME

    try:
        file_size = os.path.getsize(file)

        wait_time = FILE_WAIT_TIME[2000]

        if not file_size:
            return wait_time

        for size_threshold in FILE_WAIT_TIME:
            if file_size >= size_threshold:
                wait_time = FILE_WAIT_TIME[size_threshold]

        return wait_time
    except:
        return FILE_WAIT_TIME[2000]


def create_webdriver(file_path, cookie):
    global SESSION_COOKIES

    # INICIALIZA O NAVEGADOR
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")

    dir_path = os.path.dirname(file_path)
    prefs = {"download.default_directory": dir_path}
    options.add_experimental_option("prefs", prefs)

    driver = webdriver.Chrome(options=options)
    wait = WebDriverWait(driver, 10)

    if len(SESSION_COOKIES):
        driver.get(URL_BASE)

        for cookie in SESSION_COOKIES:
            driver.add_cookie(cookie)

        time.sleep(1)

    else:
        driver.get(URL_LOGIN)

    # if cookie:
    #     add_cookies_from_string(driver, cookie, "policia.mperon.org")

    # get cookies for the first time
    if not len(SESSION_COOKIES):
        print("NOT LOGGED")
        wait.until(EC.element_to_be_clickable((By.ID, email_id)))
        email_input = driver.find_element(By.ID, email_id)
        password_input = driver.find_element(By.ID, password_id)
        login_button = driver.find_element(By.ID, login_button_id)

        email_input.send_keys(email)
        password_input.send_keys(password)

        login_button.submit()

        wait.until(EC.url_to_be(URL_BASE))
        SESSION_COOKIES = driver.get_cookies()
    else:
        print("ALREADY LOGGED")

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


def process_file(args):

    idx, file_info, cookie = args

    file = file_info.get("path")
    file_type = file_info.get("type")

    obj = create_webdriver(file, cookie)
    driver = obj["driver"]
    wait = obj["wait"]

    try:
        if file_type == "log":
            driver.get(URL_LOG)
        elif file_type == "bilhetagem":
            driver.get(URL_EXTRACTOR)

        print(f"📄 Enviando arquivo {idx}/{len(files)}: {file}📄")

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
        submit_button = wait.until(EC.element_to_be_clickable((By.ID, "submit_form")))
        submit_button.click()

        print("✅ Arquivo enviado.")

        wait_time = get_file_wait_by_size(file)

        # AGUARDA RESPOSTA OU PROCESSAMENTO
        time.sleep(wait_time)

        print("🎉 Todos os arquivos foram processados.")
        driver.quit()
    except NoSuchElementException as e:
        print("ERRO_COOKIE_INVALIDO")
        driver.quit()
        sys.exit(2)

    except Exception as e:
        print(f"Outro ferramenta Peron: {e}")
        driver.quit()


def process_all_files(files, cookie):
    # LOOP PARA ENVIAR CADA ARQUIVO

    args = [(idx, file, cookie) for idx, file in enumerate(files, start=1)]

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        executor.map(process_file, args)


def is_file_empty(file_path):
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            content = file.read()

            count = content.count("No responsive records located")

            empty_message = False
            empty_call = False

            if "Message Log\nNo responsive records located" in content:
                empty_message = True

            if "Call Logs\nNo responsive records located" in content:
                empty_call = True

            if empty_message and empty_call and count == 2:
                return True

            return False
    except:
        return False


def create_files_list(root_path, file_type="log"):
    # type => 'log' ir 'bilhetagem'
    files = []
    try:
        elements = os.listdir(root_path)

        for folder in elements:

            folder_path = os.path.join(root_path, folder)
            is_dir = os.path.isdir(folder_path)

            if is_dir:
                folder_items = os.listdir(folder_path)

                for file in folder_items:
                    if file.endswith(".txt"):
                        file_path = os.path.join(folder_path, file)

                        if (
                            is_file_empty(file_path)
                            or "instructions" in file
                            or "preservation" in file
                        ):
                            continue

                        files.append({"path": file_path, "type": file_type})

                    if "bilhetagem" in file:
                        bilhetagem_folder = os.path.join(folder_path, "bilhetagem")

                        bilhetagem_files = create_files_list(
                            root_path=bilhetagem_folder,
                            file_type="bilhetagem",
                        )
                        files.extend(bilhetagem_files)

        return files
    except:
        return files


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 2:
        print(
            "Use: python script.py <root_folder_path>\nor\nUse: python script.py <root_folder_path>"
        )
        sys.exit(1)

    # cookie = ""

    root_path = sys.argv[1]

    # if len(sys.argv) == 3:
    #     cookie = sys.argv[2]

    files = create_files_list(root_path)

    process_all_files(files, "")

    unzip_files(root_path)
