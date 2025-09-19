import subprocess
from tkinter import filedialog, messagebox
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
import importlib.util
import sys
from pathlib import Path
from typing import TypedDict, Literal

from scripts.verifica_hashes_threads import verify_hashes

from scripts.create_hashes_model_file import create_hashes_file
from scripts.digital_guru_transformer import process_guru
from scripts.cartpanda_transformer import process_cartpanda
from scripts.process_files_peron import process_files_peron
from scripts.process_meta_text_logs import process_meta_text_logs
from scripts.check_one_file_hash import check_one_file_hash
from scripts.microsoft_transformer import process_microsoft
from scripts.telegram_transformer import process_telegram


path_input_width = 80


packages = {
    "selenium": "selenium",
    "beautifulsoup4": "bs4",
    "fpdf": "fpdf",
    "natsort": "natsort",
    "pypdf": "pypdf",
    "openpyxl": "openpyxl",
}

PADYS = {"input_to_label": (3, 10), "label_to_top": (10, 0), "execute_button": 20}

ProviderType = Literal["Digital Manager Guru", "Cartpanda", "Microsoft", "Telegram"]


class ProviderTabConfig(TypedDict):
    input_type: Literal["file", "folder"]
    informative_text: str
    input_text: str
    select_button_text: str
    title: ProviderType


PROVIDERS_TAB_CONFIG: dict[ProviderType, ProviderTabConfig] = {
    "Microsoft": {
        "title": "Microsoft",
        "input_type": "folder",
        "informative_text": "Serão gerados arquivos contendo os logs de acesso",
        "input_text": "Caminho da pasta da telemática da Microsoft",
        "select_button_text": "Selecionar pasta",
    },
    "Digital Manager Guru": {
        "title": "Digital Manager Guru",
        "input_type": "file",
        "informative_text": "Serão gerados arquivos contendo as geocoordenadas e os logs de acesso",
        "input_text": "Caminho do arquivo auditoria-usuarios.json:",
        "select_button_text": "Selecionar arquivo",
    },
    "Cartpanda": {
        "title": "Cartpanda",
        "input_type": "file",
        "informative_text": "Serão gerados arquivos contendo os logs de acesso",
        "input_text": "Caminho do arquivo Authentications-ips.xlsx:",
        "select_button_text": "Selecionar arquivo",
    },
    "Telegram": {
        "title": "Telegram",
        "input_type": "file",
        "informative_text": "Será gerado um arquivo contendo os registros de usuário",
        "input_text": "Caminho do arquivo com extensão .json:",
        "select_button_text": "Selecionar arquivo",
    },
}


def check_install_packages(packages):
    """
    Verifica se os pacotes (chave: pip, valor: módulo) estão instalados.
    Se não estiverem, instala com pip.
    """
    for pi_name, module_name in packages.items():
        if importlib.util.find_spec(module_name) is None:
            print(
                f"[!] Módulo '{module_name}' (pip: '{pi_name}') não encontrado. Instalando..."
            )
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", pi_name])
                print(f"[✓] '{pi_name}' instalado com sucesso.")
            except subprocess.CalledProcessError:
                print(f"[X] Falha ao instalar '{pi_name}'.")
        else:
            print(f"[✓] '{module_name}' já está instalado.")


def selecionar_pasta(entry_widget):
    pasta = filedialog.askdirectory()
    if pasta:
        entry_widget.delete(0, ttk.END)
        entry_widget.insert(0, pasta)


def selecionar_arquivo(entry_widget):
    arquivo = filedialog.askopenfilename()
    if arquivo:
        entry_widget.delete(0, ttk.END)
        entry_widget.insert(0, arquivo)


def get_resource_path(filename):
    if hasattr(sys, "_MEIPASS"):
        # rodando no executável
        return Path(sys._MEIPASS).joinpath(filename).resolve()
    else:
        # Rodando como script.py
        return Path(__file__).parent.joinpath(filename).resolve()


class Janela(ttk.Window):
    def __init__(
        self,
        title="ttkbootstrap",
        themename="litera",
        iconphoto="",
        size=None,
        position=None,
        minsize=None,
        maxsize=None,
        resizable=None,
        hdpi=True,
        scaling=None,
        transient=None,
        overrideredirect=False,
        alpha=1,
        **kwargs,
    ):
        super().__init__(
            title,
            themename,
            iconphoto,
            size,
            position,
            minsize,
            maxsize,
            resizable,
            hdpi,
            scaling,
            transient,
            overrideredirect,
            alpha,
            **kwargs,
        )
        self.title("Processamento de telemática")
        self.centralize_window(900, 460)
        self.configure_tabs()
        self.configure_tab1()
        self.configure_tab2()
        self.configure_tab3()
        self.configure_tab4()
        self.configure_tab5()

    def configure_tabs(self):
        self.tabs = ttk.Notebook(self)
        self.tab1 = ttk.Frame(self.tabs)
        self.tab2 = ttk.Frame(self.tabs)
        self.tab3 = ttk.Frame(self.tabs)
        self.tab4 = ttk.Frame(self.tabs)
        self.tab5 = ttk.Frame(self.tabs)
        self.tabs.add(self.tab1, text="1. Verificar múltiplas hashes")
        self.tabs.add(self.tab2, text="2. Processar logs e bilhetagem")
        self.tabs.add(self.tab3, text="3. Gerar modelo hashes.txt (Listar Arquivos)")
        self.tabs.add(self.tab4, text="4. Verificar hash de um arquivo")
        self.tabs.add(self.tab5, text="5. Outros provedores")
        self.tabs.pack(expand=1, fill="both")

    def configure_tab1(self):
        # === Aba 1: Verificação de Hashes ===
        ttk.Label(
            self.tab1,
            text="Pasta com arquivos (.zip, .gpg ou pdf) e arquivo de hashes (.txt, .csv ou .pdf):",
        ).pack(pady=(10, 0))
        self.entry_pasta_hashes = ttk.Entry(self.tab1, width=path_input_width)
        self.entry_pasta_hashes.pack(pady=(3, 10))
        ttk.Button(
            self.tab1,
            text="Selecionar Pasta",
            command=lambda: selecionar_pasta(self.entry_pasta_hashes),
        ).pack()

        ttk.Button(
            self.tab1, text="Verificar Hashes", command=self.executar_script_hashes
        ).pack(pady=40)

    def configure_tab2(self):
        # === Aba 2: Processamento de Logs ===
        ttk.Label(self.tab2, text="Pasta com arquivos zips (WhatsApp, Meta):").pack(
            pady=(10, 0)
        )
        self.entry_pasta_logs = ttk.Entry(self.tab2, width=path_input_width)
        self.entry_pasta_logs.pack(pady=(3, 10))
        ttk.Button(
            self.tab2,
            text="Selecionar Pasta",
            command=lambda: selecionar_pasta(self.entry_pasta_logs),
        ).pack()
        # ttk.Label(self.tab2, text="Cookie de autorização:").pack(pady=(10, 0))
        # self.entry_cookie = ttk.Entry(self.tab2, width=path_input_width)
        # self.entry_cookie.insert(0, carregar_cookie())
        # self.entry_cookie.pack(pady=(3, 0))
        ttk.Button(
            self.tab2,
            text="Processar Logs e Bilhetagem",
            command=self.executar_script_logs,
        ).pack(pady=20)

    def configure_tab3(self):
        # === Aba 3: Listagem de Arquivos ===
        ttk.Label(self.tab3, text="Pasta com arquivos ZIP ou PDF:").pack(pady=(10, 0))
        self.entry_pasta_listagem = ttk.Entry(self.tab3, width=path_input_width)
        self.entry_pasta_listagem.pack(pady=(3, 10))
        ttk.Button(
            self.tab3,
            text="Selecionar Pasta",
            command=lambda: selecionar_pasta(self.entry_pasta_listagem),
        ).pack()
        ttk.Button(
            self.tab3,
            text="Gerar modelo hashes.txt",
            command=self.executar_script_criacao_modelo,
        ).pack(pady=20)

    def configure_tab4(self):
        ttk.Label(self.tab4, text="Caminho do arquivo:").pack(pady=(10, 0))
        self.entry_pasta_gerar_hash = ttk.Entry(self.tab4, width=path_input_width)
        self.entry_pasta_gerar_hash.pack(pady=(3, 10))
        ttk.Button(
            self.tab4,
            text="Selecionar arquivo",
            command=lambda: selecionar_arquivo(self.entry_pasta_gerar_hash),
        ).pack()

        self.hash_type = ttk.StringVar()
        ttk.Label(self.tab4, text="Tipo da hash:").pack(pady=(10, 0))
        self.hash_box = ttk.Combobox(self.tab4, textvariable=self.hash_type)
        self.hash_box["values"] = ("SHA256", "SHA512")
        self.hash_box.state(["readonly"])
        self.hash_box.set("SHA256")
        self.hash_box.pack(pady=(3, 10))

        ttk.Label(self.tab4, text="Hash original:").pack(pady=(10, 0))
        self.entry_original_hash = ttk.Entry(self.tab4, width=path_input_width)
        self.entry_original_hash.pack(pady=(3, 10))

        ttk.Button(
            self.tab4, text="Comparar hash", command=self.comparate_single_file_hash
        ).pack(pady=20)

    def configure_tab5(self):
        self.provider_type = ttk.StringVar()
        ttk.Label(
            self.tab5, text="Selecione a empresa cujos dados serão processados:"
        ).pack(pady=PADYS["label_to_top"])

        values = tuple(PROVIDERS_TAB_CONFIG)
        self.provider_box = ttk.Combobox(
            self.tab5,
            textvariable=self.provider_type,
            state=("readonly"),
            values=values,
        )
        self.provider_box.set(values[0])
        self.provider_box.pack(pady=PADYS["input_to_label"])

        self.frames_tab5: dict[str, ttk.Frame] = {}

        self.tab5_display_components()

        self.provider_box.bind(
            "<<ComboboxSelected>>", lambda _: self.tab5_display_components()
        )

    def tab5_display_components(self):
        current_provider = self.provider_box.get()

        frame = self.frames_tab5.get(current_provider)

        config = PROVIDERS_TAB_CONFIG[current_provider]

        if not frame:
            frame = ttk.Frame(self.tab5)

            select_function = (
                selecionar_arquivo
                if config["input_type"] == "file"
                else selecionar_pasta
            )

            ttk.Label(
                frame,
                text=config["informative_text"],
            ).pack(pady=PADYS["label_to_top"])

            ttk.Label(frame, text=config["input_text"]).pack(pady=PADYS["label_to_top"])
            self.entry_file_tab5 = ttk.Entry(frame, width=path_input_width)
            self.entry_file_tab5.pack(pady=PADYS["input_to_label"])

            ttk.Button(
                frame,
                text=config["select_button_text"],
                command=lambda: select_function(self.entry_file_tab5),
            ).pack()

            # common widgets
            ttk.Button(frame, text="Processar", command=self.execute_tab5).pack(
                pady=PADYS["execute_button"]
            )

        for provider in self.frames_tab5:
            fram = self.frames_tab5[provider]

            if provider != current_provider and fram:
                fram.pack_forget()
                fram.destroy()
                self.frames_tab5[provider] = None

        self.frames_tab5[current_provider] = frame
        self.frames_tab5[current_provider].pack()

    def centralize_window(self, width, height):
        self.update_idletasks()
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width // 2) - (width // 2)
        y = (screen_height // 2) - (height // 2) - 50
        self.geometry(f"{width}x{height}+{x}+{y}")

    def executar_script_hashes(self):
        pasta = self.entry_pasta_hashes.get()
        path = Path(pasta)
        # arquivo = entry_arquivo_hashes.get()
        # modo = tipo_verificacao.get()

        if not path.is_dir():
            messagebox.showerror("Erro", "Verifique a pasta e o arquivo de hashes.")
            return

        try:
            result = verify_hashes(str(path.resolve()))
            if e := result.get("error"):
                messagebox.showerror("Erro", f"Erro ao executar script:\n{e}")
                return

            messagebox.showinfo(
                "Sucesso",
                "Verificação de hashes concluída.\n\nFoi criado um relatório em pdf na mesma pasta.",
            )
        except subprocess.CalledProcessError as e:
            messagebox.showerror("Erro", f"Erro ao executar script:\n{e}")

    def executar_script_logs(self):
        pasta_raiz = self.entry_pasta_logs.get()
        path = Path(pasta_raiz)
        # cookie = self.entry_cookie.get().strip()

        if not path.is_dir():
            messagebox.showerror("Erro", "Selecione uma pasta raiz válida.")
            return

        try:
            process_meta_text_logs(pasta_raiz)
            process_files_peron(pasta_raiz)

            messagebox.showinfo("Sucesso", "Processamento de logs concluído.")
        except subprocess.CalledProcessError as e:
            if e.returncode == 2:
                messagebox.showerror(
                    "Cookie inválido", "O cookie fornecido não é válido ou expirou."
                )
            else:
                messagebox.showerror("Erro", f"Erro ao executar script:\n{e}")

    def executar_script_criacao_modelo(self):
        pasta = self.entry_pasta_listagem.get()
        path = Path(pasta)

        if not path.is_dir():
            messagebox.showerror("Erro", "Selecione uma pasta válida.")
            return

        try:
            create_hashes_file(pasta)
            messagebox.showinfo("Sucesso", "O arquivo hashes.txt foi criado.")
        except subprocess.CalledProcessError as e:
            messagebox.showerror("Erro", f"Erro ao executar script:\n{e}")

    def comparate_single_file_hash(self):
        file = self.entry_pasta_gerar_hash.get()
        is_file_valid = self.validate_file(file)
        hash_type = self.hash_box.get()

        original_hash = self.entry_original_hash.get()

        if not is_file_valid:
            return

        if not original_hash:
            messagebox.showerror("Erro", "Preencha a hash original para comparar")
            return

        try:
            result = check_one_file_hash(file, original_hash, hash_type)

            if result.get("success"):
                messagebox.showinfo(
                    "Sucesso",
                    result.get("message"),
                )
            else:
                messagebox.showerror("Erro", result.get("message"))
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao executar script:\n{e}")

    def execute_tab5(self):
        file = self.entry_file_tab5.get()
        path = Path(file)

        provider_type = self.provider_box.get()

        match provider_type:
            case value if (
                value == PROVIDERS_TAB_CONFIG["Digital Manager Guru"]["title"]
            ):
                self.execute_guru(file, path)

            case value if value == PROVIDERS_TAB_CONFIG["Cartpanda"]["title"]:
                self.execute_cartpanda(file, path)

            case value if value == PROVIDERS_TAB_CONFIG["Microsoft"]["title"]:
                self.execute_microsoft(path)
            case value if value == PROVIDERS_TAB_CONFIG["Telegram"]["title"]:
                self.execute_telegram(file, path)

    def validate_file(self, file):
        file_path = Path(file)

        if not file_path.exists():
            messagebox.showerror("Erro", "O arquivo não existe ou é inválido")
            return False

        if file_path.is_dir():
            messagebox.showerror("Erro", "Selecione um arquivo, não um diretório")
            return False

        return True

    def validate_file_extension(self, file: str, extension: str):
        file_path = Path(file)

        if file_path.suffix != extension:
            messagebox.showerror("Erro", f"O arquivo selecionado não é um {extension}")
            return False

        return True

    def validate_folder(self, path: Path):
        if not path.exists():
            messagebox.showerror("Erro", "A pasta não existe ou é inválida")
            return False

        if not path.is_dir():
            messagebox.showerror("Erro", "Selecione uma pasta, não um arquivo")
            return False

        return True

    def execute_microsoft(self, path: Path):
        is_dir_valid = self.validate_folder(path)

        if not is_dir_valid:
            return

        result = process_microsoft(path.resolve())

        title = "Sucesso" if result.get("success") else "Erro"
        messagebox.showinfo(title, result.get("message"))

    def execute_guru(self, file, path: Path):
        is_file_valid = self.validate_file(file)

        if not is_file_valid:
            return

        is_json = self.validate_file_extension(path.resolve(), ".json")

        if not is_json:
            return

        process_guru(path.resolve())
        messagebox.showinfo(
            "Sucesso",
            "Os arquivo processados foram salvo na pasta 'processamentos guru'",
        )

    def execute_cartpanda(self, file, path: Path):
        is_file_valid = self.validate_file(file)

        if not is_file_valid:
            return

        is_xlsx = self.validate_file_extension(path.resolve(), ".xlsx")
        if not is_xlsx:
            return

        process_cartpanda(path.resolve())

        messagebox.showinfo(
            "Sucesso",
            "Os arquivo processados foram salvo na pasta 'processamentos cartpanda'",
        )

    def execute_telegram(self, file, path: Path):
        is_file_valid = self.validate_file(file)

        if not is_file_valid:
            return

        is_json = self.validate_file_extension(path.resolve(), ".json")
        if not is_json:
            return

        process_telegram(path.resolve())

        messagebox.showinfo(
            "Sucesso",
            "O arquivo processado foi salvo na mesma pasta do arquivo de origem",
        )


def is_frozen():
    """Retorna True se o script estiver rodando como executável (PyInstaller)"""
    return getattr(sys, "frozen", False)


def main():
    if not is_frozen():
        check_install_packages(packages)

    janela = Janela()
    janela.mainloop()


if __name__ == "__main__":
    main()


# empacotar
# pip install pyinstaller
# pyinstaller data-processing-tools.spec
