#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RANSOMWARE_SIM v2.0 - Simulateur de comportement rançongiciel pour
l'ingénierie de détection (blue team / lab isolé).

SAFETY BY DESIGN
- Chiffre UNIQUEMENT les fichiers du dossier canary passé via --target
- Refuse de s'exécuter sans le marqueur ".ransim_canary" dans le dossier
- Refuse les emplacements système (racines, /etc, /usr, C:\Windows, ...)
- Aucune persistance, aucun accès réseau, aucune injection, aucun shutdown
- Journal d'audit complet, mode --dry-run, plafonds stricts (nombre/taille)

Usage légitime : VM de lab isolée, pour construire et valider des
détections (Sysmon, Sigma, YARA). Toute autre utilisation est illégale.
"""

import argparse
import json
import logging
import os
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

APP = "RANSOMWARE_SIM"
VERSION = "2.0"
MARKER = ".ransim_canary"
ENC_EXT = ".ransim"
NOTE_NAME = "README_RESTORE_FILES.txt"
MANIFEST_NAME = "ransim_manifest.json"
KEY_NAME = "ransim_key_DO_NOT_SHARE.key"
LOG_NAME = "ransim_audit.log"

MAX_FILE_BYTES = 10 * 1024 * 1024      # 10 Mo max par fichier
DEFAULT_MAX_FILES = 200                # plafond global

# Emplacements où un canary n'a aucun sens légitime
FORBIDDEN = [
    "c:/windows", "c:/program files", "c:/program files (x86)",
    "c:/programdata/microsoft", "c:/system volume information",
    "c:/", "c:", "/", "/etc", "/usr", "/bin", "/sbin", "/lib",
    "/var", "/boot", "/sys", "/proc", "/dev", "/run",
]

RESERVED = {MARKER, NOTE_NAME, MANIFEST_NAME, KEY_NAME, LOG_NAME}


def is_forbidden(target: Path) -> bool:
    s = str(target).lower().replace("\\", "/").rstrip("/")
    return s in FORBIDDEN


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def setup_logging(logfile: Path) -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[logging.StreamHandler(sys.stdout),
                  logging.FileHandler(logfile, encoding="utf-8")],
    )


def abort(msg: str) -> None:
    print(f"[!] ABORT: {msg}", file=sys.stderr)
    sys.exit(2)


def load_fernet():
    try:
        from cryptography.fernet import Fernet
        return Fernet
    except ImportError:
        abort("module 'cryptography' manquant -> python3 -m pip install cryptography")


def init_canary(args) -> None:
    target = Path(args.target).resolve()
    if is_forbidden(target):
        abort(f"emplacement interdit pour un canary: {target}")
    target.mkdir(parents=True, exist_ok=True)
    (target / MARKER).write_text(
        f"Canary autorise pour {APP} v{VERSION} - declare par l'operateur "
        f"le {now_iso()}\n", encoding="utf-8")
    for i in range(1, 4):
        (target / f"document_demo_{i}.txt").write_text(
            f"Fichier de demonstration {i} - contenu simule.\n" * 20,
            encoding="utf-8")
    logging.info("Canary initialise: %s (3 fichiers demo crees)", target)


def collect_files(target: Path, max_files: int):
    files = []
    for p in sorted(target.rglob("*")):
        if not p.is_file():
            continue
        if p.name in RESERVED or p.name.endswith(ENC_EXT):
            continue
        try:
            if p.stat().st_size > MAX_FILE_BYTES:
                logging.info("SKIP (>10 Mo): %s", p)
                continue
        except OSError:
            continue
        files.append(p)
        if len(files) >= max_files:
            logging.info("Plafond atteint (%d fichiers) - stop collecte", max_files)
            break
    return files


def run_simulation(args) -> None:
    target = Path(args.target).resolve()
    if is_forbidden(target):
        abort(f"emplacement interdit: {target}")
    if not target.is_dir():
        abort("dossier cible inexistant")
    if not (target / MARKER).exists():
        abort("marqueur canary absent -> lancez d'abord: "
              "ransomware_sim.py --target <dossier> --init-canary")

    files = collect_files(target, args.max_files)
    if not files:
        logging.info("Aucun fichier a chiffrer - rien a faire.")
        return

    if args.dry_run:
        logging.info("[DRY-RUN] %d fichier(s) seraient chiffres:", len(files))
        for p in files:
            logging.info("  -> %s", p.name)
        return

    Fernet = load_fernet()
    key = Fernet.generate_key()
    f = Fernet(key)

    keyfile = Path(args.keyfile)
    keyfile.write_bytes(key)
    try:
        os.chmod(keyfile, 0o600)
    except OSError:
        pass
    logging.info("Clef sauvegardee: %s (ne la partagez PAS)", keyfile)

    victim_id = str(uuid.uuid4())
    manifest = {"app": APP, "version": VERSION, "victim_id": victim_id,
                "started": now_iso(), "target": str(target), "files": []}
    manifest_path = target / MANIFEST_NAME

    for p in files:
        enc = p.with_name(p.name + ENC_EXT)
        data = p.read_bytes()
        enc.write_bytes(f.encrypt(data))
        p.unlink()
        manifest["files"].append({"orig": p.name, "enc": enc.name,
                                  "size": len(data)})
        manifest_path.write_text(json.dumps(manifest, indent=2),
                                 encoding="utf-8")
        logging.info("CHIFFRE: %s -> %s", p.name, enc.name)

    if args.note:
        (target / NOTE_NAME).write_text(
            "==============================================\n"
            "  SIMULATION - RANSOMWARE_SIM v{v}\n"
            "==============================================\n"
            "Victim ID : {vid}\n"
            "Fichiers chiffrés (simulation) : {n}\n"
            "Algorithme : Fernet (AES128-CBC + HMAC)\n"
            "Aucun paiement : ceci est un exercice de detection.\n"
            "Restauration : decryptor.py --target <dossier> --keyfile <clef>\n"
            "Cet outil ne touche QUE ce dossier canary.\n"
            "==============================================\n".format(
                v=VERSION, vid=victim_id, n=len(manifest["files"])),
            encoding="utf-8")
        logging.info("Note de simulation deposee: %s", NOTE_NAME)

    manifest["finished"] = now_iso()
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    logging.info("SIMULATION COMPLETE - %d fichier(s), victime %s",
                 len(manifest["files"]), victim_id)


def main() -> None:
    ap = argparse.ArgumentParser(prog="ransomware_sim",
                                 description=f"{APP} v{VERSION} - simulateur "
                                              "safe-by-design pour lab de detection")
    ap.add_argument("--target", required=True,
                    help="dossier canary (doit contenir le marqueur)")
    ap.add_argument("--init-canary", action="store_true",
                    help="declare le dossier comme canary et cree des fichiers demo")
    ap.add_argument("--dry-run", action="store_true",
                    help="liste ce qui serait chiffre, sans rien modifier")
    ap.add_argument("--no-note", dest="note", action="store_false",
                    help="ne pas deposer la note de simulation")
    ap.add_argument("--max-files", type=int, default=DEFAULT_MAX_FILES)
    ap.add_argument("--keyfile", default=KEY_NAME)
    ap.add_argument("--log", default=LOG_NAME)
    args = ap.parse_args()

    setup_logging(Path(args.log))
    logging.info("%s v%s - demarrage", APP, VERSION)

    if args.init_canary:
        init_canary(args)
    else:
        run_simulation(args)


if __name__ == "__main__":
    main()
