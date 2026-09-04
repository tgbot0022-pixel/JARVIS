"""
JARVIS kısayol yardımcıları — Windows sürümü.

macOS sürümü .app/.command ve LaunchAgent plist üretiyordu; Windows'ta
bunların karşılığı .lnk kısayollarıdır:
  - Masaüstü kısayolu  → Desktop\\JARVIS.lnk
  - Açılışta başlat     → Başlangıç klasörü\\JARVIS.lnk

PowerShell WScript.Shell kullanılır, ek bağımlılık gerekmez.
Kısayollar kurulu JARVIS.exe dosyasını doğrudan başlatır.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
_CREATE_NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)


def _desktop_dir() -> Path:
    """OneDrive masaüstü veya klasik masaüstünü bulur."""
    candidates = []
    one = os.environ.get("OneDrive") or os.environ.get("OneDriveConsumer")
    if one:
        candidates.append(Path(one) / "Desktop")
    candidates.append(Path(os.environ.get("USERPROFILE", str(Path.home()))) / "Desktop")
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return candidates[-1]


def _startup_dir() -> Path:
    """Windows Başlangıç klasörü (açılışta otomatik çalışanlar)."""
    return (
        Path(os.environ.get("APPDATA", str(Path.home())))
        / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup"
    )


def _target_exe() -> tuple[str, str]:
    """EXE derlemesinde JARVIS.exe'yi; kaynak çalıştırmada pythonw + main.py'yi döndürür."""
    exe = Path(sys.executable)
    if getattr(sys, "frozen", False):
        return str(exe), ""
    pyw = exe.with_name("pythonw.exe")
    target = pyw if pyw.exists() else exe
    return str(target), f'"{BASE_DIR / "main.py"}"'


def _write_shortcut(link_path: Path) -> Path:
    """Verilen yola JARVIS .lnk kısayolu yazar."""
    link_path.parent.mkdir(parents=True, exist_ok=True)
    target, arguments = _target_exe()

    # Frozen EXE'de BASE_DIR PyInstaller'ın geçici klasörü olabilir.
    # Bu nedenle ikon kaynağı olarak doğrudan hedef JARVIS.exe kullanılır.
    icon_source = target if getattr(sys, "frozen", False) else str(BASE_DIR / "Icon" / "JARVIS.ico")
    icon_line = f"$s.IconLocation = '{icon_source},0'; "

    ps_script = (
        "$ws = New-Object -ComObject WScript.Shell; "
        f"$s = $ws.CreateShortcut('{link_path}'); "
        f"$s.TargetPath = '{target}'; "
        f"$s.Arguments = '{arguments}'; "
        f"$s.WorkingDirectory = '{Path(target).parent}'; "
        "$s.Description = 'J.A.R.V.I.S'; "
        f"{icon_line}"
        "$s.Save()"
    )

    result = subprocess.run(
        ["powershell", "-NoProfile", "-WindowStyle", "Hidden", "-Command", ps_script],
        capture_output=True,
        text=True,
        timeout=20,
        creationflags=_CREATE_NO_WINDOW,
    )
    if result.returncode != 0:
        detail = (result.stderr or result.stdout or "").strip()
        raise RuntimeError(detail or "Kısayol oluşturulamadı.")
    return link_path


# ── Masaüstü kısayolu ────────────────────────────────────────────────────────
def desktop_shortcut_path() -> Path:
    return _desktop_dir() / "JARVIS.lnk"


def create_desktop_shortcut() -> Path:
    return _write_shortcut(desktop_shortcut_path())


# ── Açılışta başlat (Başlangıç klasörü) ──────────────────────────────────────
def startup_shortcut_path() -> Path:
    return _startup_dir() / "JARVIS.lnk"


def create_startup_shortcut() -> Path:
    return _write_shortcut(startup_shortcut_path())


def remove_startup_shortcut() -> None:
    path = startup_shortcut_path()
    if path.exists():
        path.unlink()


if __name__ == "__main__":
    created = create_desktop_shortcut()
    print(f"Masaüstü kısayolu oluşturuldu: {created}")
