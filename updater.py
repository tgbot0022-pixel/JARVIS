"""JARVIS self-update: checks GitHub Releases and replaces the running EXE safely."""
from __future__ import annotations

import json
import os
import subprocess
import hashlib
import tempfile
import urllib.request
from pathlib import Path

from version import APP_VERSION, GITHUB_API


def _version_tuple(value: str) -> tuple[int, ...]:
    value = str(value).strip().lstrip("vV")
    parts = []
    for part in value.split("."):
        digits = "".join(ch for ch in part if ch.isdigit())
        parts.append(int(digits or 0))
    return tuple(parts or [0])


def _latest_release() -> dict | None:
    req = urllib.request.Request(
        GITHUB_API,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "JARVIS-Updater",
        },
    )
    with urllib.request.urlopen(req, timeout=5) as response:
        return json.loads(response.read().decode("utf-8"))


def _asset_url(release: dict) -> str | None:
    for asset in release.get("assets", []):
        if str(asset.get("name", "")).lower() == "jarvis.exe":
            return asset.get("browser_download_url")
    return None


def _download(url: str, destination: Path) -> None:
    req = urllib.request.Request(url, headers={"User-Agent": "JARVIS-Updater"})
    with urllib.request.urlopen(req, timeout=60) as response, destination.open("wb") as out:
        while True:
            chunk = response.read(1024 * 1024)
            if not chunk:
                break
            out.write(chunk)


def _download_text(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "JARVIS-Updater"})
    with urllib.request.urlopen(req, timeout=30) as response:
        return response.read().decode("utf-8").strip()


def _asset_url_by_name(release: dict, wanted_name: str) -> str | None:
    wanted = wanted_name.lower()
    for asset in release.get("assets", []):
        if str(asset.get("name", "")).lower() == wanted:
            return asset.get("browser_download_url")
    return None


def _verify_sha256(exe_path: Path, expected: str) -> bool:
    expected_hash = expected.strip().split()[0].lower()
    if len(expected_hash) != 64 or any(ch not in "0123456789abcdef" for ch in expected_hash):
        return False
    digest = hashlib.sha256()
    with exe_path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().lower() == expected_hash


def _start_replacer(temp_exe: Path, target_exe: Path) -> None:
    pid = os.getpid()
    script = Path(tempfile.gettempdir()) / f"jarvis_update_{pid}.ps1"
    # PowerShell waits for the current JARVIS process to exit, replaces the EXE,
    # then shows a clear restart message. The user manually starts JARVIS again.
    ps = f'''$ErrorActionPreference = "SilentlyContinue"
$pidToWait = {pid}
$temp = '{str(temp_exe).replace("'", "''")}'
$target = '{str(target_exe).replace("'", "''")}'
for ($i=0; $i -lt 120; $i++) {{
    $p = Get-Process -Id $pidToWait -ErrorAction SilentlyContinue
    if (-not $p) {{ break }}
    Start-Sleep -Milliseconds 250
}}
for ($i=0; $i -lt 30; $i++) {{
    try {{
        Copy-Item -LiteralPath $temp -Destination $target -Force -ErrorAction Stop
        if ((Get-Item $target).Length -gt 100000) {{ break }}
    }} catch {{}}
    Start-Sleep -Milliseconds 500
}}
if (Test-Path -LiteralPath $target) {{
    Add-Type -AssemblyName PresentationFramework
    [System.Windows.MessageBox]::Show(
        "JARVIS güncellendi!`n`nYeni sürüm başarıyla yüklendi.`n`nLütfen JARVIS.exe'yi yeniden başlatın.",
        "JARVIS - Güncelleme Tamamlandı",
        [System.Windows.MessageBoxButton]::OK,
        [System.Windows.MessageBoxImage]::Information
    ) | Out-Null
}}
Remove-Item -LiteralPath $temp -Force -ErrorAction SilentlyContinue
Remove-Item -LiteralPath '{str(script).replace("'", "''")}' -Force -ErrorAction SilentlyContinue
'''
    script.write_text(ps, encoding="utf-8")
    creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    subprocess.Popen(
        ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(script)],
        creationflags=creationflags,
        close_fds=True,
    )


def check_for_update() -> bool:
    """Return True when an update was scheduled and JARVIS should exit."""
    if os.environ.get("JARVIS_SKIP_UPDATE") == "1":
        return False
    if not getattr(__import__("sys"), "frozen", False):
        return False

    try:
        release = _latest_release()
        latest = str(release.get("tag_name", "")).strip()
        if not latest or _version_tuple(latest) <= _version_tuple(APP_VERSION):
            return False

        url = _asset_url(release)
        if not url:
            return False

        target = Path(__import__("sys").executable).resolve()
        temp_exe = Path(tempfile.gettempdir()) / f"JARVIS_update_{os.getpid()}.exe"
        _download(url, temp_exe)
        if not temp_exe.exists() or temp_exe.stat().st_size < 100_000:
            temp_exe.unlink(missing_ok=True)
            return False

        # Releases created by the official workflow include a SHA-256 file.
        # If present, verify it before replacing the running EXE. Older releases
        # without the hash remain compatible.
        hash_url = _asset_url_by_name(release, "JARVIS.exe.sha256")
        if hash_url:
            expected_hash = _download_text(hash_url)
            if not _verify_sha256(temp_exe, expected_hash):
                temp_exe.unlink(missing_ok=True)
                return False

        _start_replacer(temp_exe, target)
        return True
    except Exception as exc:
        print(f"[JARVIS] Güncelleme kontrolü başarısız: {exc}")
        return False
