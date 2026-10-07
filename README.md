# RANSOMWARE_SIM — Laboratoire de détection de rançongiciels

> Simulateur de comportement rançongiciel **safe-by-design** + decryptor +
> pack de détection complet (Sysmon, Sigma, YARA). Conçu pour les labs
> isolés et l'ingénierie de détection (blue team).

---

## Quoi de neuf dans la v2.0

Cette version remplace l'ancien PoC "shutdown" par un outil **exploitable
en contexte professionnel** :

| Élément v1 (shutdown PoC) | v2.0 (detection lab) |
|---|---|
| Shutdown forcé de la machine | ❌ supprimé |
| Persistance (clé Run) | ❌ supprimé |
| Anti-sandbox / évasion | ❌ supprimé |
| Livraison par lien + bypass navigateur | ❌ supprimé |
| — | ✅ Chiffrement réel Fernet **limité au canary** |
| — | ✅ Decryptor avec vérification d'intégrité |
| — | ✅ Config Sysmon + 3 règles Sigma + règle YARA |
| — | ✅ Script de validation automatique des détections |
| — | ✅ Garde-fous : marqueur, refus système, dry-run, plafonds |

**Pourquoi ce choix :** sur un CV, « j'ai écrit un simulateur **et** les
détections qui l'attrapent » est plus crédible et plus recherché (SOC,
DFIR, détection) que « j'ai écrit un malware ». Et ça passe les
modérations GitHub/LinkedIn sans risque.

## Architecture

```
RansomwareDetectionLab/
├── README.md                    <- ce fichier
├── LICENSE (MIT + clause lab)
├── simulator/
│   ├── ransomware_sim.py        <- simulateur (Fernet, canary uniquement)
│   └── decryptor.py             <- restauration + vérification d'intégrité
├── detection/
│   ├── sysmon-config.xml        <- visibilité lab (proc, fichiers, registre)
│   ├── sigma/
│   │   ├── ransim_exec.yml      <- exécution du simulateur (EID 1)
│   │   ├── ransim_ransom_note.yml  <- dépose note de rançon (EID 11)
│   │   └── ransim_keyfile_drop.yml <- création clef locale (EID 11)
│   └── yara/ransim_sample.yar   <- signature de l'échantillon
└── lab/
    ├── lab-guide.md             <- guide pas-à-pas Kali + Windows (7 phases)
    ├── validate_detection.ps1   <- validation automatique PASS/FAIL
    └── test-checklist.md        <- 16 checks de validation
```

## Garde-fous intégrés (safe-by-design)

1. **Marqueur obligatoire** : le dossier cible doit contenir `.ransim_canary`
   (créé volontairement par l'opérateur via `--init-canary`)
2. **Refus des emplacements système** : racines de disque, `C:\Windows`,
   `/etc`, `/usr`, `/var`, etc. → exit immédiat
3. **`--dry-run`** : liste ce qui serait chiffré sans rien modifier
4. **Plafonds** : 200 fichiers max, 10 Mo max par fichier
5. **Aucun effet hors périmètre** : pas de persistance, pas de réseau,
   pas de shutdown, pas d'injection
6. **Journal d'audit** horodaté de chaque action
7. **Restauration garantie** : manifest + clef locale → `decryptor.py`

## Démarrage rapide

```bash
# Kali / Linux
python3 -m pip install cryptography
python3 simulator/ransomware_sim.py --target ~/lab/canary --init-canary
python3 simulator/ransomware_sim.py --target ~/lab/canary --dry-run
python3 simulator/ransomware_sim.py --target ~/lab/canary
python3 simulator/decryptor.py --target ~/lab/canary --keyfile ransim_key_DO_NOT_SHARE.key
```

```powershell
# Windows (lab VM)
python -m pip install cryptography
python simulator\ransomware_sim.py --target C:\Lab\canary --init-canary
python simulator\ransomware_sim.py --target C:\Lab\canary
# Détection :
.\lab\validate_detection.ps1 -Target C:\Lab\canary
```

## Plan de test (résumé)

Voir `lab/lab-guide.md` pour le détail des 7 phases :

1. VM isolée + snapshot
2. Installation simulateur + Sysmon
3. Ligne de base
4. Simulation (dry-run puis réel, sur canary)
5. Validation des détections (Sysmon EID 1/11, Sigma ×3, YARA)
6. Restauration + teardown
7. Publication (README, writeup, captures Chainsaw)

## Positionnement LinkedIn / CV

- **Titre suggéré** : *Detection Engineering | Adversary Simulation | Blue Team*
- **Bullet CV** : « Conçu un simulateur de rançongiciel safe-by-design avec
  decryptor (Fernet, périmètre canary) ; développé et **validé** un pack de
  détection complet — Sysmon, 3 règles Sigma, règle YARA — en lab isolé
  Windows/Kali ; restaurations vérifiées par checksum. »
- **Preuves à publier** : captures Chainsaw (3 matches), sortie
  `validate_detection.ps1` (5 PASS), YARA hit, checklist 16/16.

## Avertissement

Outil destiné aux labs isolés dont vous avez le contrôle. L'utiliser sur des
machines ou des données sans autorisation explicite est illégal
(Art. 323-1 et suivants du Code pénal français ; équivalents dans la plupart
des juridictions). La licence MIT inclut une clause rappelant cet usage.

## Contributions / suite

Idées de v2.1 : ingestion Elastic/ELK, règle Sigma pour EID 3 (preuve
d'absence de C2), benchmark canari, version conteneurisée.
