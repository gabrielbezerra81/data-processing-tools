from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions
import time
import sys
from selenium.common.exceptions import NoSuchElementException
import pathlib
from typing import TypedDict, Literal
from scripts.zip_tools import recursive_unzip_files
from concurrent.futures import ThreadPoolExecutor


# CONFIGURAÇÕES
email = "gabriel.bezerra@mpce.mp.br"
password = "mg-)ju*@GHDp!"

URL_LOGIN = "https://policia.mperon.org/auth/login"
URL_BASE = "https://policia.mperon.org/"
URL_LOG = f"{URL_BASE}/extractor/access_log"
URL_EXTRACTOR = f"{URL_BASE}/extractor/whatsapp"
SESSION_COOKIES = []
FILE_WAIT_TIME = {2000: 7, 3000: 9, 4000: 10, 5000: 12}
BILHETAGEM_KEYWORDS = ["Message Log", "Call Log", "Call Logs"]


email_id = "inputEmail"
password_id = "inputPassword"
login_button_id = "logLink"

FileType = Literal["log", "bilhetagem"]


class FileItem(TypedDict):
    path: str
    type: FileType


class DriverResult(TypedDict):
    driver: WebDriver
    wait: WebDriverWait[WebDriver]


def get_file_wait_by_size(file: str):
    global FILE_WAIT_TIME

    try:
        path = pathlib.Path(file)
        file_size = path.stat().st_size / 1024

        wait_time = FILE_WAIT_TIME[2000]

        if not file_size:
            return wait_time

        for size_threshold in FILE_WAIT_TIME:
            if file_size >= size_threshold:
                wait_time = FILE_WAIT_TIME[size_threshold]

        return wait_time
    except Exception as e:
        print(f"get size error: {e}")
        return FILE_WAIT_TIME[2000]


def create_webdriver(file_path: str, cookie: str) -> DriverResult:
    global SESSION_COOKIES

    # INICIALIZA O NAVEGADOR
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")

    path = pathlib.Path(file_path)

    dir_path = str(path.resolve().parent)
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
        wait.until(expected_conditions.element_to_be_clickable((By.ID, email_id)))
        email_input = driver.find_element(By.ID, email_id)
        password_input = driver.find_element(By.ID, password_id)
        login_button = driver.find_element(By.ID, login_button_id)

        email_input.send_keys(email)
        password_input.send_keys(password)

        login_button.submit()

        wait.until(expected_conditions.url_to_be(URL_BASE))
        SESSION_COOKIES = driver.get_cookies()
    else:
        print("ALREADY LOGGED")

    return {"driver": driver, "wait": wait}


# FUNÇÃO PARA INSERIR COOKIES
def add_cookies_from_string(driver: WebDriver, cookie: str, domain: str):
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


def process_file(args: tuple[int, FileItem, str, int]):

    idx, file_info, cookie, total = args

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

        print(f"📄 Enviando arquivo {idx}/{total}: {file}📄")

        print(file)

        # CLICA NA ABA "Carregar arquivo"
        tabFile = driver.find_element(By.CSS_SELECTOR, 'a[href="#tabFile"]')

        tabFile.click()
        time.sleep(1)

        # AGUARDA O INPUT ESTAR VISÍVEL
        file_input = driver.find_element(By.ID, "import_file")

        # ENVIA O ARQUIVO
        file_input.send_keys(file)
        time.sleep(1)

        # CLICA EM "ENVIAR"
        submit_button = wait.until(
            expected_conditions.element_to_be_clickable((By.ID, "submit_form"))
        )
        submit_button.click()

        print("✅ Arquivo enviado.")

        wait_time = get_file_wait_by_size(file)

        # AGUARDA RESPOSTA OU PROCESSAMENTO
        time.sleep(wait_time)

        print("🎉 Todos os arquivos foram processados.")
    except NoSuchElementException as e:
        print("ERRO_COOKIE_INVALIDO")
        sys.exit(2)

    except Exception as e:
        print(f"Outro ferramenta Peron: {e}")
    finally:
        if driver:
            driver.quit()


def process_all_files(files: list[FileItem], cookie: str):
    # LOOP PARA ENVIAR CADA ARQUIVO
    max_workers = 3

    args = [(idx, file, cookie, len(files)) for idx, file in enumerate(files, start=1)]

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


def is_bilhetagem_file(file_path):
    if "bilhetagem" in file_path:
        return True

    with open(file_path, "r", encoding="utf-8") as file:
        content = file.read()

        return any(word in content for word in BILHETAGEM_KEYWORDS)


def create_files_list(root_path: str):
    current_path = pathlib.Path(root_path)

    files: list[FileItem] = []

    try:
        for item in current_path.rglob("*"):

            if item.name.endswith(".txt"):
                file_path = str(item.resolve())

                # type => 'log' ir 'bilhetagem'
                file_type: FileType = "log"

                if is_bilhetagem_file(file_path):
                    file_type = "bilhetagem"

                if (
                    is_file_empty(file_path)
                    or "instructions" in item.name
                    or "preservation" in item.name
                ):
                    continue

                files.append({"path": file_path, "type": file_type})

        return files
    except Exception as e:
        print(f"file list error {e}")
        return files


def process_files_peron(cur_path: str):
    files = create_files_list(cur_path)

    print(f"Processando {len(files)} arquivos")

    process_all_files(files, "")

    recursive_unzip_files(cur_path)


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 2:
        print(
            "Use: python script.py <root_folder_path>\nor\nUse: python script.py <root_folder_path>"
        )
        sys.exit(1)

    cur_path = sys.argv[1]

    process_files_peron(cur_path)

    # if len(sys.argv) == 3:
    #     cookie = sys.argv[2]
