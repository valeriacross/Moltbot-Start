# architect.py — ingresso fisso per Koyeb (Run command: python architect.py).
# Avvia il file versionato di Architect indicato in BOT_FILE.
# A OGNI nuova versione di Architect si aggiorna solo BOT_FILE qui sotto:
# il Run command su Koyeb non cambia più. Questo file non ha una VERSION propria.
import glob
import os
import re
import runpy

BOT_FILE = "Architect_400.py"


def _num(path):
    m = re.search(r"Architect_(\d+)\.py$", path)
    return int(m.group(1)) if m else 0


if __name__ == "__main__":
    base = os.path.dirname(os.path.abspath(__file__))
    newest = max(glob.glob(os.path.join(base, "Architect_*.py")), key=_num, default=None)
    if newest and _num(newest) > _num(BOT_FILE):
        print(f"ATTENZIONE: {os.path.basename(newest)} è più recente di {BOT_FILE}; "
              f"aggiornare BOT_FILE in architect.py", flush=True)
    runpy.run_path(os.path.join(base, BOT_FILE), run_name="__main__")
