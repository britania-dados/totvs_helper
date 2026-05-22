# -*- mode: python ; coding: utf-8 -*-

import os

from PyInstaller.building.splash import Splash
from PyInstaller.utils.hooks import collect_data_files

project_dir = os.path.dirname(os.path.abspath(SPEC))
icon_file = os.path.join(project_dir, "assets", "totvs_helper.ico")
splash_file = os.path.join(project_dir, "assets", "splash.png")
version_file = os.path.join(project_dir, "packaging", "windows_version_info.txt")

a = Analysis(
    ["main.py"],
    pathex=["src"],
    binaries=[],
    datas=[
        (".env", "."),
        ("assets/totvs_helper_logo.png", "assets"),
        ("assets/totvs_helper.ico", "assets"),
        ("assets/splash.png", "assets"),
        ("assets/splash_logo_ui.png", "assets"),
    ]
    + collect_data_files("customtkinter"),
    hiddenimports=[
        "customtkinter",
        "pygments",
        "pygments.lexers",
        "pygments.lexers.sql",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)

splash = Splash(
    splash_file,
    binaries=a.binaries,
    datas=a.datas,
    text_pos=(24, 300),
    text_size=11,
    text_color="white",
    text_default="Iniciando Totvs Helper...",
)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    splash,
    name="TotvsHelper",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    icon=icon_file,
    version=version_file,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

