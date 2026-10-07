# Checklist de validation - RANSOMWARE_SIM v2.0

| # | Test | Commande | Attendu | PASS/FAIL |
|---|------|----------|---------|-----------|
| 1 | Refus sans marqueur | `--target <dossier_sans_canary>` | exit 2 + message ABORT | ☐ |
| 2 | Refus emplacement système | `--target C:\Windows` (ou `/etc`) | exit 2 | ☐ |
| 3 | Dry-run sans modification | `--dry-run` | liste affichée, 0 fichier modifié | ☐ |
| 4 | Plafond de fichiers | `--max-files 2` | 2 fichiers chiffrés max | ☐ |
| 5 | Chiffrement canary | `--target <canary>` | fichiers `.ransim` + manifest | ☐ |
| 6 | Note de simulation | après run | `README_RESTORE_FILES.txt` présent | ☐ |
| 7 | Audit log | après run | `ransim_audit.log` complet et horodaté | ☐ |
| 8 | Détection Sysmon EID 1 | validate_detection.ps1 | PASS | ☐ |
| 9 | Détection Sysmon EID 11 (note) | idem | PASS | ☐ |
| 10 | Détection Sysmon EID 11 (clef) | idem | PASS | ☐ |
| 11 | Match Sigma ×3 | chainsaw hunt | 3 règles matchent | ☐ |
| 12 | Match YARA | `yara ransim_sample.yar <sample>` | RANSIM_Simulator_Sample | ☐ |
| 13 | Restauration complète | decryptor.py | fichiers d'origine restaurés, `.ransim` supprimés | ☐ |
| 14 | Aucune persistance | après reboot VM | rien ne se relance | ☐ |
| 15 | Aucun trafic réseau | Sysmon EID 3 pendant le run | 0 connexion du simulateur | ☐ |
| 16 | Snapshot restauré | fin de session | VM revenue à l'état propre | ☐ |
