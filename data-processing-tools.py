import subprocess
from tkinter import filedialog, messagebox
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
import importlib.util
import sys
from pathlib import Path

from scripts.verifica_hashes_threads import verify_hashes
from scripts.processa_meta_whats_logs import process_logs_extractions
from scripts.create_hashes_model_file import create_hashes_file
from scripts.hasher import Hasher


# COOKIE_FILE = "cookie.txt"

path_input_width = 80


packages = {
    "selenium": "selenium",
    "beautifulsoup4": "bs4",
    "fpdf": "fpdf",
    "natsort": "natsort",
    "pypdf": "pypdf",
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
        self.title("Ferramentas de Processamento")
        self.centralizar_janela(740, 460)
        self.configura_abas()
        self.configura_aba1()
        self.configura_aba2()
        self.configura_aba3()
        self.configura_aba4()

    def configura_abas(self):
        self.abas = ttk.Notebook(self)
        self.aba1 = ttk.Frame(self.abas)
        self.aba2 = ttk.Frame(self.abas)
        self.aba3 = ttk.Frame(self.abas)
        self.aba4 = ttk.Frame(self.abas)
        self.abas.add(self.aba1, text="1. Verificação de Hashes")
        self.abas.add(self.aba2, text="2. Processamento de Logs")
        self.abas.add(self.aba3, text="3. Gerar modelo hashes.txt (Listar Arquivos)")
        self.abas.add(self.aba4, text="4. Comparar hash de um arquivo")
        self.abas.pack(expand=1, fill="both")

    def configura_aba1(self):
        # === Aba 1: Verificação de Hashes ===
        ttk.Label(
            self.aba1,
            text="Pasta com arquivos (.zip, .gpg ou pdf) e arquivo de hashes (.txt, .csv ou .pdf):",
        ).pack(pady=(10, 0))
        self.entry_pasta_hashes = ttk.Entry(self.aba1, width=path_input_width)
        self.entry_pasta_hashes.pack(pady=(3, 10))
        ttk.Button(
            self.aba1,
            text="Selecionar Pasta",
            command=lambda: selecionar_pasta(self.entry_pasta_hashes),
        ).pack()

        ttk.Button(
            self.aba1, text="Verificar Hashes", command=self.executar_script_hashes
        ).pack(pady=40)

    def configura_aba2(self):
        # === Aba 2: Processamento de Logs ===
        ttk.Label(self.aba2, text="Pasta com arquivos zips (WhatsApp, Meta):").pack(
            pady=(10, 0)
        )
        self.entry_pasta_logs = ttk.Entry(self.aba2, width=path_input_width)
        self.entry_pasta_logs.pack(pady=(3, 10))
        ttk.Button(
            self.aba2,
            text="Selecionar Pasta",
            command=lambda: selecionar_pasta(self.entry_pasta_logs),
        ).pack()
        # ttk.Label(self.aba2, text="Cookie de autorização:").pack(pady=(10, 0))
        # self.entry_cookie = ttk.Entry(self.aba2, width=path_input_width)
        # self.entry_cookie.insert(0, carregar_cookie())
        # self.entry_cookie.pack(pady=(3, 0))
        ttk.Button(
            self.aba2,
            text="Processar Logs e Bilhetagem",
            command=self.executar_script_logs,
        ).pack(pady=20)

    def configura_aba3(self):
        # === Aba 3: Listagem de Arquivos ===
        ttk.Label(self.aba3, text="Pasta com arquivos ZIP ou PDF:").pack(pady=(10, 0))
        self.entry_pasta_listagem = ttk.Entry(self.aba3, width=path_input_width)
        self.entry_pasta_listagem.pack(pady=(3, 10))
        ttk.Button(
            self.aba3,
            text="Selecionar Pasta",
            command=lambda: selecionar_pasta(self.entry_pasta_listagem),
        ).pack()
        ttk.Button(
            self.aba3,
            text="Gerar modelo hashes.txt",
            command=self.executar_script_criacao_modelo,
        ).pack(pady=20)

    def configura_aba4(self):
        ttk.Label(self.aba4, text="Caminho do arquivo:").pack(pady=(10, 0))
        self.entry_pasta_gerar_hash = ttk.Entry(self.aba4, width=path_input_width)
        self.entry_pasta_gerar_hash.pack(pady=(3, 10))
        ttk.Button(
            self.aba4,
            text="Selecionar arquivo",
            command=lambda: selecionar_arquivo(self.entry_pasta_gerar_hash),
        ).pack()

        self.hash_type = ttk.StringVar()
        ttk.Label(self.aba4, text="Tipo da hash:").pack(pady=(10, 0))
        self.hash_box = ttk.Combobox(self.aba4, textvariable=self.hash_type)
        self.hash_box["values"] = ("SHA256", "SHA512")
        self.hash_box.state(["readonly"])
        self.hash_box.set("SHA256")
        self.hash_box.pack(pady=(3, 10))

        ttk.Label(self.aba4, text="Hash original:").pack(pady=(10, 0))
        self.entry_original_hash = ttk.Entry(self.aba4, width=path_input_width)
        self.entry_original_hash.pack(pady=(3, 10))

        ttk.Button(
            self.aba4, text="Comparar hash", command=self.comparate_single_file_hash
        ).pack(pady=20)

    def centralizar_janela(self, largura, altura):
        self.update_idletasks()
        largura_tela = self.winfo_screenwidth()
        altura_tela = self.winfo_screenheight()
        x = (largura_tela // 2) - (largura // 2)
        y = (altura_tela // 2) - (altura // 2) - 50
        self.geometry(f"{largura}x{altura}+{x}+{y}")

    def executar_script_hashes(self):
        pasta = self.entry_pasta_hashes.get()
        path = Path(pasta)
        # arquivo = entry_arquivo_hashes.get()
        # modo = tipo_verificacao.get()

        if not path.is_dir():
            messagebox.showerror("Erro", "Verifique a pasta e o arquivo de hashes.")
            return

        try:
            verify_hashes(str(path.resolve()))
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

        # if not cookie:
        #     messagebox.showerror("Erro", "O campo de cookie está vazio.")
        #     return

        # salvar_cookie(cookie)

        try:
            process_logs_extractions(pasta_raiz)

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
            result = Hasher.hash_comparator(file, original_hash, hash_func=hash_type)

            if result.get("success"):
                messagebox.showinfo(
                    "Sucesso",
                    result.get("message"),
                )
            else:
                messagebox.showerror("Erro", result.get("message"))
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao executar script:\n{e}")

    def validate_file(self, file):
        file_path = Path(file)

        if not file_path.exists():
            messagebox.showerror("Erro", "O arquivo não existe ou é inválido")
            return False

        if file_path.is_dir():
            messagebox.showerror("Erro", "Selecione um arquivo, não um diretório")
            return False

        return True


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
