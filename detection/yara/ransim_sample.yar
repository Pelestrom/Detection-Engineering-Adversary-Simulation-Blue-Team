/*
  Détecte les scripts/binaires RANSOMWARE_SIM (échantillon du lab).
  Test: yara detection/yara/ransim_sample.yar simulator/ransomware_sim.py
*/
rule RANSIM_Simulator_Sample
{
    meta:
        author = "Lab operator"
        description = "Detects RANSOMWARE_SIM simulator sample"
        date = "2026-10-07"
    strings:
        $app = "RANSOMWARE_SIM" ascii
        $note = "README_RESTORE_FILES.txt" ascii
        $marker = ".ransim_canary" ascii
        $ext = ".ransim" ascii
    condition:
        2 of ($app, $note, $marker, $ext)
}
