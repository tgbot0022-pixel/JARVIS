# -*- mode: python ; coding: utf-8 -*-
from pathlib import Path
from PyInstaller.utils.hooks import collect_dynamic_libs, collect_submodules

ROOT = Path(SPEC).parent

# Do not rely only on automatic discovery. PyAudio contains a native PortAudio
# extension and must be explicitly included in the frozen application.
hiddenimports = [
    "pyaudio",
    "pyaudio._portaudio",
]

for pkg in ["google.genai", "cv2", "PIL", "mss", "pyautogui", "psutil", "pycaw", "comtypes"]:
    try:
        hiddenimports += collect_submodules(pkg)
    except Exception:
        pass

# Remove duplicates while preserving order.
hiddenimports = list(dict.fromkeys(hiddenimports))

binaries = []
try:
    binaries += collect_dynamic_libs("pyaudio")
except Exception:
    pass

datas = [
    (str(ROOT / "core"), "core"),
    (str(ROOT / "Fonts"), "Fonts"),
    (str(ROOT / "SFX"), "SFX"),
    (str(ROOT / "Icon"), "Icon"),
    (str(ROOT / "memory"), "memory"),
    (str(ROOT / "biyometrik_photoshop.jsx"), "."),
    (str(ROOT / "config" / "api_keys.example.json"), "config"),
]

# Exclude local secrets / runtime data from the build.
datas = [(src, dst) for src, dst in datas if Path(src).exists()]

excludes = ["tkinter.test", "pytest", "IPython"]

a = Analysis(
    [str(ROOT / "main.py")],
    pathex=[str(ROOT)],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="JARVIS",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    icon=str(ROOT / "Icon" / "JARVIS.ico") if (ROOT / "Icon" / "JARVIS.ico").exists() else None,
)
