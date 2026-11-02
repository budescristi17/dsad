"""Adaptor pentru sistemul de fișiere în memorie din browser."""
import json
import csv
from itertools import islice
import runpy
import shutil
import sys
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED

from rezolva import alege_fisiere, copiaza_date, scrie_proiect
from date_intrare import pregateste_date
from enunturi import citeste_enunt, enunt_din_proiect
from interpretare import planifica

lucru = Path("/lucru")
intrari = lucru / "intrari"
proiect = lucru / "proiect"


def incepe():
    if lucru.exists():
        shutil.rmtree(lucru)
    intrari.mkdir(parents=True)
    proiect.mkdir()


def interpreteaza_web(config):
    cfg = json.loads(config)
    arhive = list(intrari.glob("*.zip"))
    sursa = arhive[0] if arhive else intrari
    text = cfg["text"].strip()
    if not text:
        fise = [f for f in intrari.iterdir() if f.suffix.lower() in (".txt", ".pdf")]
        if len(fise) > 1:
            raise ValueError("Alege o singură fișă PDF sau TXT.")
        text = citeste_enunt(fise[0]) if fise else enunt_din_proiect(sursa)
    if not text.strip():
        raise ValueError("Introdu cerințele sau alege o fișă PDF sau TXT cu text selectabil.")
    date = proiect / "data_in"
    copiaza_date(sursa, date)
    principal, auxiliare = alege_fisiere(date, cfg["principal"] or None)
    _, indicatori, _ = pregateste_date(date, principal, [], [])
    pasi = planifica(text, indicatori, cfg["categorie"] or None)
    scrie_proiect(proiect, principal, auxiliare, pasi)
    cod = (proiect / "solutie.py").read_text(encoding="utf-8")
    return json.dumps({"principal": principal, "pasi": pasi, "text": text, "cod": cod}, ensure_ascii=False)


def calculeaza_web():
    # Executăm exact scriptul afișat. Grupăm fișierele rezultate în data_out pentru arhivă.
    runpy.run_path(str(proiect / "solutie.py"), run_name="__main__")
    iesiri = proiect / "data_out"
    iesiri.mkdir(exist_ok=True)
    rezultate = []
    for f in sorted(proiect.glob("*.csv")):
        with f.open(encoding="utf-8", newline="") as sursa:
            cititor = csv.reader(sursa)
            antet = next(cititor)
            mostra = list(islice(cititor, 5))
            total = len(mostra) + sum(1 for _ in cititor)
        rezultate.append(dict(nume=f.name, antet=antet, mostra=mostra, total=total))
        f.replace(iesiri / f.name)
    with ZipFile(lucru / "rezolvare.zip", "w", ZIP_DEFLATED) as z:
        for f in sorted(proiect.rglob("*")):
            if f.is_file() and "__pycache__" not in f.parts:
                z.write(f, f.relative_to(proiect))
    return json.dumps(rezultate, ensure_ascii=False)
