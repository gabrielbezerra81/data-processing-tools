# -*- mode: python ; coding: utf-8 -*-
import os
from glob import glob

project_path = os.path.abspath('.')

a = Analysis(
    ['data-processing-tools.py'],
    pathex=[project_path],
    binaries=[],
    datas=[(src, "scripts") for src in glob("scripts/*.py")],
    hiddenimports=[
        'pypdf',
        'fpdf',
        'selenium',
        'selenium.webdriver.common.by',
        'selenium.webdriver.chrome.webdriver',
        'selenium.webdriver.support.ui',
        'selenium.webdriver.support.expected_conditions',
        'bs4',
        'natsort'
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='Processamento de telemática',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
