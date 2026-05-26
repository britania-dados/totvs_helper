# -*- mode: python ; coding: utf-8 -*-

import os
import re

from PyInstaller.building.splash import Splash
from PyInstaller.utils.hooks import collect_data_files

project_dir = os.path.dirname(os.path.abspath(SPEC))
icon_file = os.path.join(project_dir, "assets", "totvs_helper.ico")
splash_file = os.path.join(project_dir, "assets", "splash.png")

exe_name = os.environ.get("TOTVS_HELPER_EXE_NAME", "TotvsHelper_64b")

_version_py = os.path.join(project_dir, "src", "totvs_helper", "version.py")
_version_text = open(_version_py, encoding="utf-8").read()
_match = re.search(r'__version__\s*=\s*["\']([^"\']+)["\']', _version_text)
if not _match:
    raise RuntimeError("Nao foi possivel ler __version__ em version.py")
__version__ = _match.group(1)
_parts = [int(p) for p in __version__.split(".")]
while len(_parts) < 4:
    _parts.append(0)
_filevers = tuple(_parts[:4])

version_file = os.path.join(project_dir, "packaging", "windows_version_info.build.txt")
with open(version_file, "w", encoding="utf-8") as _vf:
    _vf.write(
        f"""# UTF-8
# Generated during build from src/totvs_helper/version.py
VSVersionInfo(
  ffi=FixedFileInfo(
    filevers={_filevers},
    prodvers={_filevers},
    mask=0x3F,
    flags=0x0,
    OS=0x40004,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
    ),
  kids=[
    StringFileInfo(
      [
      StringTable(
        u'040904B0',
        [StringStruct(u'CompanyName', u'TOTVS Helper Team'),
        StringStruct(u'FileDescription', u'Totvs Helper'),
        StringStruct(u'FileVersion', u'{__version__}'),
        StringStruct(u'InternalName', u'{exe_name}'),
        StringStruct(u'OriginalFilename', u'{exe_name}.exe'),
        StringStruct(u'ProductName', u'Totvs Helper'),
        StringStruct(u'ProductVersion', u'{__version__}')])
      ]),
    VarFileInfo([VarStruct(u'Translation', [1033, 1200])])
  ]
)
"""
    )

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
        ("packaging/pentaho/templates", "packaging/pentaho/templates"),
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
    name=exe_name,
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
