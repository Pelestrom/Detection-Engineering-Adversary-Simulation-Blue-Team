# Guide de lab - RANSOMWARE_SIM v2.0

Objectif : construire, exécuter et **valider des détections** contre un
comportement de rançongiciel simulé — sur Kali VM et Windows VM isolées.

> Règle d'or : snapshot AVANT chaque phase, restauration APRÈS chaque phase.

---

## Phase 0 — Environnement isolé (obligatoire)

- VM Windows 10/11 (VirtualBox/VMware) + VM Kali, réseau host-only ou NAT isolé
- Snapshot "état propre" pris avant toute manipulation
- Aucune donnée personnelle dans les VMs

## Phase 1 — Installer le simulateur

**Windows VM :**
```powershell
python -m pip install cryptography
# Copier simulator/ dans C:\Lab\simulator\
```

**Kali VM :**
```bash
python3 -m pip install cryptography
git clone <ton-repo> ~/ransim && cd ~/ransim
```

## Phase 2 — Installer Sysmon (Windows VM)

```powershell
# Télécharger Sysmon (Sysinternals), puis :
.\Sysmon64.exe -accepteula -i detection\sysmon-config.xml
Get-Service Sysmon64            # doit être Running
# Log : Journal "Microsoft-Windows-Sysmon/Operational"
```

## Phase 3 — Ligne de base (avant simulation)

```powershell
# Noter l'état initial du journal Sysmon
Get-WinEvent -LogName "Microsoft-Windows-Sysmon/Operational" -MaxEvents 5
```
Kali : rien à installer de plus (optionnel : `sudo apt install chainsaw yara`).

## Phase 4 — Exécuter la simulation

**Windows VM :**
```powershell
python C:\Lab\simulator\ransomware_sim.py --target C:\Lab\canary --init-canary
python C:\Lab\simulator\ransomware_sim.py --target C:\Lab\canary --dry-run
python C:\Lab\simulator\ransomware_sim.py --target C:\Lab\canary
```
Attendu : fichiers `.ransim`, `README_RESTORE_FILES.txt`, `ransim_manifest.json`,
clef `ransim_key_DO_NOT_SHARE.key` dans le dossier d'exécution.

**Kali VM :**
```bash
python3 simulator/ransomware_sim.py --target ~/lab/canary --init-canary
python3 simulator/ransomware_sim.py --target ~/lab/canary
```

## Phase 5 — Valider les détections

**Windows (script automatique) :**
```powershell
cd lab\
.\validate_detection.ps1 -Target C:\Lab\canary -SimPath C:\Lab\simulator\ransomware_sim.py
```
Sortie attendue : 5 lignes PASS (Sysmon actif, note EID 11, clef EID 11,
exécution EID 1, restauration).

**Corrélation Sigma avec Chainsaw (Windows ou Kali) :**
```bash
# Sur Kali, exporter les journaux Windows puis :
chainsaw hunt /chemin/vers/evtx -s detection/sigma/ --mapping mappings/sigma-event-logs-all.yml
# 3 règles doivent matcher: ransim_exec, ransim_ransom_note, ransim_keyfile_drop
```
(Le fichier de mapping est fourni avec le repo chainsaw.)

**YARA sur l'échantillon :**
```bash
yara detection/yara/ransim_sample.yar simulator/ransomware_sim.py
# Attendu: RANSIM_Simulator_Sample
```

## Phase 6 — Restauration & teardown

```bash
python3 simulator/decryptor.py --target ~/lab/canary --keyfile ransim_key_DO_NOT_SHARE.key
# Vérifier le contenu d'un fichier restauré, puis:
sha256sum document_demo_1.txt   # comparer avec l'original si archivé avant
```
- Windows : restaurer le snapshot, ou conserver la VM comme environnement de détection permanent
- Supprimer/protéger la clef locale après l'exercice

## Phase 7 — Ce que tu peux publier (GitHub/LinkedIn)

- README orienté **detection engineering** (celui du repo)
- Les 3 règles Sigma + règle YARA + config Sysmon (100 % publiable)
- Un writeup : "J'ai simulé un rançongiciel en lab et écrit les détections qui l'attrapent"
- Capture d'écran Chainsaw montrant les 3 matches
