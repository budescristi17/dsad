from pathlib import Path
import numpy as np
import pandas as pd

baza = Path(__file__).resolve().parent
intrare = baza / 'data_in'
t = pd.read_csv(intrare / 'I2014.csv', index_col='Siruta', dtype={'Siruta': str})
t_pop = pd.read_csv(intrare / 'PopulatieLocalitati.csv', index_col='Siruta', dtype={'Siruta': str})
coloane_noi = [c for c in t_pop if c not in t]
if not t.index.isin(t_pop.index).all():
    raise ValueError('Cod Siruta fără corespondent în tabelul auxiliar.')
t = t.merge(t_pop[coloane_noi], left_index=True, right_index=True, validate='one_to_one')


def medie_ponderata(df, variabile, pondere):
    ponderi = df[pondere]
    if (ponderi < 0).any():
        raise ValueError("Ponderile trebuie să fie nenegative.")
    if ponderi.sum() == 0:
        return pd.Series(np.nan, index=variabile)
    return pd.Series(np.average(df[variabile], axis=0, weights=ponderi), index=variabile)

# Cerința 1. Să se salveze în fișierul Output1.csv raportul dintre cifra de afaceri și numărul de salariați pentru fiecare localitate unde există salariați. Datele vor fi salvate în ordine descrescătoare a acestui raport. Pentru fiecare localitate se va afișa codul Siruta, denumirea localității și raportul dintre cifra de afaceri și numărul de salariați.
selectie = t.loc[t['NrSal'] > 0]
t1 = selectie.loc[selectie['NrSal'] != 0].copy()
t1['Raport CA/NrSal'] = t1['TotalCifraAfaceri'] / t1['NrSal']
t1 = t1[['DenLocalitate', 'Raport CA/NrSal']]
t1 = t1.sort_values('Raport CA/NrSal', ascending=False, kind='stable')
t1.to_csv(baza / 'Output1.csv')

# Cerința 2. Să se calculeze rata ocupării populației ca număr de salariați la 1000 locuitori pentru fiecare județ. Datele vor fi salvate în ordine descrescătoare a ratei, în fișierul Output2.csv. Pentru fiecare județ se va afișa indicativul de județ și rata ocupării.
t2 = t.groupby('Judet')[['NrSal', 'Populatie']].sum()
t2['Rata Ocuparii'] = t2['NrSal'] * 1000 / t2['Populatie'].replace(0, np.nan)
t2 = t2[['Rata Ocuparii']]
t2 = t2.sort_values('Rata Ocuparii', ascending=False, kind='stable')
t2.to_csv(baza / 'Output2.csv')

# Cerința 3. Să se determine pentru fiecare județ localitatea cu cel mai mare profit pe locuitor și să se salveze în fișierul Output3.csv. Pentru fiecare județ se va salva indicativul de județ și denumirea localității cerute.
t3 = t.loc[t['Populatie'] != 0].copy()
scor = t3['TotalProfit'] / t3['Populatie']
coduri = scor.groupby(t3['Judet']).idxmax()
t3 = t3.loc[coduri, ['Judet', 'DenLocalitate']].rename(columns={'DenLocalitate': 'Localitate'})
t3.to_csv(baza / 'Output3.csv', index=False)

# Cerința 4. Să se calculeze valorile medii ale indicatorilor la nivel de județ (media localităților din județ) și să se salveze în fișierul Output4.csv. Se va calcula media ponderată, folosind ca pondere populația localităților. Pentru fiecare județ se va afișa indicativul de județ și cele 5 medii.
variabile = ['NrFirme', 'NrSal', 'TotalCifraAfaceri', 'TotalProfit', 'TotalPierdere']
pondere = 'Populatie'
t4 = t.groupby('Judet')[['NrFirme', 'NrSal', 'TotalCifraAfaceri', 'TotalProfit', 'TotalPierdere', 'Populatie']].apply(
    medie_ponderata, variabile=variabile, pondere=pondere)
t4.to_csv(baza / 'Output4.csv')

print('Gata: Output1.csv, Output2.csv, Output3.csv, Output4.csv')
