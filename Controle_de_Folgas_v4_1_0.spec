# -*- mode: python ; coding: utf-8 -*-

from PyInstaller.utils.hooks import collect_all

# Impede a distribuição de um executável sem a chave PÚBLICA de suporte.
# A chave PRIVADA permanece fora do projeto e NUNCA deve ser empacotada.
import base64
import re
from pathlib import Path

_public_file = Path(SPECPATH) / "support_public_key.py"
_key_match = re.search(r'SUPPORT_PUBLIC_KEY_B64\s*=\s*"([A-Za-z0-9_-]+)"', _public_file.read_text(encoding="utf-8"))
if _key_match is None or len(base64.urlsafe_b64decode(_key_match.group(1) + "=" * (-len(_key_match.group(1)) % 4))) != 32:
    raise RuntimeError("Chave publica de suporte nao configurada. Execute ferramentas/suporte_cli.py criar-chaves antes do build.")



datas = [("Logo", "Logo")]
binaries = []
hiddenimports = [
    "customtkinter",
    "PIL",
    "PIL.Image",
    "openpyxl",
    "openpyxl.styles",
    "openpyxl.utils",
    "sqlite3",
    "tkinter",
    "tkinter.ttk",
    "tkinter.filedialog",
    "win32com.client",
    "pythoncom",
    "pywintypes",
]

for package_name in ("customtkinter", "openpyxl"):
    package_datas, package_binaries, package_hiddenimports = collect_all(package_name)
    datas += package_datas
    binaries += package_binaries
    hiddenimports += package_hiddenimports


a = Analysis(
    ["controle_folgas_v4_1_0.py"],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

# Primeira etapa do carregamento: splash NATIVO e propositalmente simples.
# Ele aparece enquanto o --onefile está sendo extraído. Não usamos texto/fontes
# aqui para reduzir incompatibilidades do recurso experimental entre versões de
# Tcl/Tk. Assim que o Python inicia, o próprio programa assume com uma segunda
# tela de carregamento e mostra as etapas reais.
splash = Splash(
    "Logo/splash.png",
    binaries=a.binaries,
    datas=a.datas,
    text_pos=None,
    always_on_top=True,
    center="active",
    full_tk=True,
    minify_script=False,
)

exe = EXE(
    pyz,
    a.scripts,
    splash,
    splash.binaries,
    a.binaries,
    a.datas,
    [],
    name="Controle de Folgas",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=["Logo/logo.ico"],
)
