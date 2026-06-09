"""Integrazione con LibreOffice headless: ricalcolo forzato ed export in PDF.

LibreOffice e' il motore di rendering comune fra l'ambiente di Claude (web) e il
locale. Due operazioni:

* :func:`recalc` ricalcola TUTTE le formule e ri-salva l'``.xlsx`` (openpyxl scrive
  le formule ma non i valori in cache: senza questo passo i valori derivati e il
  PDF resterebbero a zero).
* :func:`to_pdf` esporta un ``.xlsx`` in PDF rispettando area di stampa e scala.

Il ricalcolo forzato si ottiene con un profilo utente dedicato che imposta la
modalita' di ricalcolo a "sempre" (``registrymodifications.xcu``). Il profilo e'
persistente e viene riusato fra le invocazioni: il bootstrap di un profilo nuovo
e' il costo dominante di ogni run headless (secondi per invocazione). In caso di
profilo corrotto od occupato si ritenta automaticamente con un profilo pulito.

Fallback su macOS: se LibreOffice non c'e' ma e' presente Microsoft Excel, si usa
quest'ultimo via AppleScript (solo locale).
"""

from __future__ import annotations

import os
import platform
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

# Modalita' di ricalcolo: 0 = sempre, 1 = mai, 2 = chiedi. Vogliamo "sempre".
_RECALC_XCU = """<?xml version="1.0" encoding="UTF-8"?>
<oor:items xmlns:oor="http://openoffice.org/2001/registry" xmlns:xs="http://www.w3.org/2001/XMLSchema" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
 <item oor:path="/org.openoffice.Office.Calc/Formula/Load"><prop oor:name="OOXMLRecalcMode" oor:op="fuse"><value>0</value></prop></item>
 <item oor:path="/org.openoffice.Office.Calc/Formula/Load"><prop oor:name="ODFRecalcMode" oor:op="fuse"><value>0</value></prop></item>
</oor:items>
"""

_MAC_SOFFICE = "/Applications/LibreOffice.app/Contents/MacOS/soffice"
_MAC_EXCEL = "/Applications/Microsoft Excel.app"


class RenderError(RuntimeError):
    """Errore di rendering con messaggio operativo (incl. come installare il motore)."""


def find_soffice() -> str | None:
    """Trova l'eseguibile LibreOffice (``soffice``) o ``None``."""
    for name in ("soffice", "libreoffice"):
        path = shutil.which(name)
        if path:
            return path
    if Path(_MAC_SOFFICE).exists():
        return _MAC_SOFFICE
    return None


def have_excel() -> bool:
    return platform.system() == "Darwin" and Path(_MAC_EXCEL).exists()


def _run_soffice(soffice: str, args: list[str], profile: str) -> subprocess.CompletedProcess:
    cmd = [
        soffice,
        "--headless",
        "--norestore",
        "--invisible",
        "--nologo",
        f"-env:UserInstallation=file://{profile}",
        *args,
    ]
    return subprocess.run(cmd, capture_output=True, text=True, timeout=180)


def _profile_with_recalc(base: str) -> str:
    """Crea un profilo utente LibreOffice che ricalcola sempre all'apertura."""
    profile = Path(base) / "lo_profile"
    user_dir = profile / "user"
    user_dir.mkdir(parents=True, exist_ok=True)
    (user_dir / "registrymodifications.xcu").write_text(_RECALC_XCU, encoding="utf-8")
    return str(profile)


def _persistent_profile_root() -> Path:
    """Cartella del profilo persistente (override: ``FSA_LO_PROFILE``)."""
    env = os.environ.get("FSA_LO_PROFILE")
    if env:
        return Path(env)
    uid = os.getuid() if hasattr(os, "getuid") else os.environ.get("USERNAME", "user")
    return Path(tempfile.gettempdir()) / f"fsa-lo-profile-{uid}"


def _ensure_persistent_profile() -> str:
    """Prepara (o riusa) il profilo persistente con ricalcolo 'sempre'."""
    root = _persistent_profile_root()
    xcu = root / "user" / "registrymodifications.xcu"
    try:
        existing = xcu.read_text(encoding="utf-8")
    except OSError:
        existing = ""
    # LibreOffice riscrive il file a fine run preservando gli item 'fuse': basta
    # verificare il marcatore senza azzerare il profilo gia' bootstrappato.
    if "OOXMLRecalcMode" not in existing:
        xcu.parent.mkdir(parents=True, exist_ok=True)
        xcu.write_text(_RECALC_XCU, encoding="utf-8")
    return str(root)


def _convert(soffice: str, source: Path, convert_to: str, out_ext: str, dest: Path, what: str) -> Path:
    """Conversione headless con profilo riusato; un retry con profilo pulito."""
    with tempfile.TemporaryDirectory() as tmp:
        outdir = Path(tmp) / "out"
        outdir.mkdir()
        produced = outdir / (source.stem + out_ext)
        args = ["--convert-to", convert_to, "--outdir", str(outdir), str(source)]

        try:
            profile = _ensure_persistent_profile()
        except OSError:  # profilo persistente non creabile: usa un profilo usa-e-getta
            profile = _profile_with_recalc(tmp)
        proc = _run_soffice(soffice, args, profile)
        if proc.returncode != 0 or not produced.exists():
            shutil.rmtree(_persistent_profile_root(), ignore_errors=True)
            proc = _run_soffice(soffice, args, _profile_with_recalc(tmp))
            if proc.returncode != 0 or not produced.exists():
                raise RenderError(
                    f"{what} LibreOffice fallito (rc={proc.returncode}).\n{proc.stderr or proc.stdout}"
                )
        shutil.copyfile(produced, dest)
    return dest


def recalc(xlsx_path: str | Path) -> Path:
    """Ricalcola le formule e ri-salva l'``.xlsx`` in place. Ritorna il path."""
    xlsx_path = Path(xlsx_path).resolve()
    soffice = find_soffice()
    if soffice is None:
        if have_excel():
            return _excel_recalc(xlsx_path)
        raise RenderError(_no_engine_msg())
    return _convert(soffice, xlsx_path, "xlsx:Calc MS Excel 2007 XML", ".xlsx", xlsx_path, "Ricalcolo")


def to_pdf(xlsx_path: str | Path, pdf_path: str | Path) -> Path:
    """Esporta l'``.xlsx`` in PDF. Ritorna il path del PDF."""
    xlsx_path = Path(xlsx_path).resolve()
    pdf_path = Path(pdf_path).resolve()
    pdf_path.parent.mkdir(parents=True, exist_ok=True)
    soffice = find_soffice()
    if soffice is None:
        if have_excel():
            return _excel_pdf(xlsx_path, pdf_path)
        raise RenderError(_no_engine_msg())
    return _convert(soffice, xlsx_path, "pdf:calc_pdf_Export", ".pdf", pdf_path, "Export PDF")


def ensure_fonts(fonts_dir: str | Path) -> list[str]:
    """Rende disponibili i font bundlati (Syne) al renderer copiandoli nella
    cartella font utente della piattaforma. Best effort: ritorna i font copiati."""
    fonts_dir = Path(fonts_dir)
    if not fonts_dir.is_dir():
        return []
    system = platform.system()
    if system == "Darwin":
        dest = Path.home() / "Library" / "Fonts"
    elif system == "Windows":  # pragma: no cover
        dest = Path(os.environ.get("LOCALAPPDATA", Path.home())) / "Microsoft" / "Windows" / "Fonts"
    else:
        dest = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share")) / "fonts"
    dest.mkdir(parents=True, exist_ok=True)
    copied = []
    for ttf in sorted(fonts_dir.glob("*.ttf")):
        target = dest / ttf.name
        if not target.exists():
            try:
                shutil.copyfile(ttf, target)
                copied.append(ttf.name)
            except OSError:  # pragma: no cover - best effort
                pass
    if copied and system not in ("Darwin", "Windows"):
        fc = shutil.which("fc-cache")
        if fc:
            subprocess.run([fc, "-f", str(dest)], capture_output=True)
    return copied


def _no_engine_msg() -> str:
    return (
        "Nessun motore di rendering trovato.\n"
        "Installa LibreOffice:\n"
        "  - macOS:  brew install --cask libreoffice\n"
        "  - Debian/Ubuntu:  sudo apt-get install -y libreoffice-calc\n"
        "In alternativa, su macOS con Microsoft Excel installato il fallback e' automatico."
    )


# --- Fallback macOS via Microsoft Excel (AppleScript) -------------------------------


def _osascript(script: str) -> subprocess.CompletedProcess:
    return subprocess.run(["osascript", "-e", script], capture_output=True, text=True, timeout=180)


def _excel_recalc(xlsx_path: Path) -> Path:
    script = f'''
    tell application "Microsoft Excel"
        set wb to open workbook workbook file name (POSIX file "{xlsx_path}")
        calculate
        close wb saving yes
    end tell
    '''
    proc = _osascript(script)
    if proc.returncode != 0:
        raise RenderError(f"Ricalcolo via Excel fallito:\n{proc.stderr}")
    return xlsx_path


def _excel_pdf(xlsx_path: Path, pdf_path: Path) -> Path:
    script = f'''
    tell application "Microsoft Excel"
        set wb to open workbook workbook file name (POSIX file "{xlsx_path}")
        calculate
        set sh to worksheet "Report" of wb
        save as sh filename (POSIX file "{pdf_path}") file format PDF file format
        close wb saving no
    end tell
    '''
    proc = _osascript(script)
    if proc.returncode != 0 or not pdf_path.exists():
        raise RenderError(f"Export PDF via Excel fallito:\n{proc.stderr}")
    return pdf_path


if __name__ == "__main__":  # pragma: no cover - diagnostica rapida
    print("soffice:", find_soffice() or "NON trovato")
    print("excel  :", "presente" if have_excel() else "assente")
    sys.exit(0)
