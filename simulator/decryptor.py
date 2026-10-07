#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RANSIM_DECRYPTOR - Restaure les fichiers du canary chiffres par
RANSOMWARE_SIM (exercice de detection - aucune donnee reelle touchee).
"""

import argparse
import json
import sys
from pathlib import Path

MARKER = ".ransim_canary"
ENC_EXT = ".ransim"
MANIFEST_NAME = "ransim_manifest.json"


def main() -> None:
    ap = argparse.ArgumentParser(prog="ransim_decryptor")
    ap.add_argument("--target", required=True, help="dossier canary")
    ap.add_argument("--keyfile", required=True, help="clef generee par le simulateur")
    ap.add_argument("--manifest", default=None,
                    help=f"manifest (defaut: {MANIFEST_NAME} dans le canary)")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--keep-encrypted", action="store_true")
    args = ap.parse_args()

    target = Path(args.target).resolve()
    if not (target / MARKER).exists():
        print("[!] Marqueur canary absent - ce dossier n'est pas un canary RANSIM.",
              file=sys.stderr)
        sys.exit(2)

    try:
        from cryptography.fernet import Fernet, InvalidToken
    except ImportError:
        print("[!] module 'cryptography' manquant -> "
              "python3 -m pip install cryptography", file=sys.stderr)
        sys.exit(2)

    manifest_path = Path(args.manifest) if args.manifest else target / MANIFEST_NAME
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    f = Fernet(Path(args.keyfile).read_bytes())

    ok = fail = 0
    for entry in manifest["files"]:
        enc = target / entry["enc"]
        orig = target / entry["orig"]
        if not enc.exists():
            print(f"[!] introuvable: {entry['enc']}")
            fail += 1
            continue
        try:
            data = f.decrypt(enc.read_bytes())
        except InvalidToken:
            print(f"[!] clef invalide pour {entry['enc']}")
            fail += 1
            continue
        if len(data) != entry["size"]:
            print(f"[!] taille inattendue pour {entry['orig']}")
            fail += 1
            continue
        if args.dry_run:
            print(f"[DRY] {entry['enc']} -> {entry['orig']} ({len(data)} octets)")
            ok += 1
            continue
        orig.write_bytes(data)
        if not args.keep_encrypted:
            enc.unlink()
        print(f"[+] restaure: {entry['orig']}")
        ok += 1

    print(f"[=] termine: {ok} restaure(s), {fail} echec(s)")


if __name__ == "__main__":
    main()
