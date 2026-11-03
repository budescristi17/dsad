import os
import pandas as pd
import numpy as np

os.makedirs('data_out', exist_ok=True)
firme = pd.read_csv('data_in/I2014.csv')

# Cerința 1: Raport pe localitate
conditie = firme['NrSal'] > 0
rezultat = firme.loc[conditie].copy()
rezultat['Raport CA/NrSal'] = rezultat['TotalCifraAfaceri'] / rezultat['NrSal']
rezultat = rezultat[['Siruta', 'DenLocalitate', 'Raport CA/NrSal']]
rezultat = rezultat.sort_values('Raport CA/NrSal', ascending=False, kind='stable')
rezultat.to_csv('data_out/Output1.csv', index=False)

# Cerința 2: Raport pe grup
populatie = pd.read_csv('data_in/PopulatieLocalitati.csv')
date = firme.merge(populatie, on='Siruta')
total = date.groupby('Judet')[['NrSal', 'Populatie']].sum()
total['Rata Ocuparii'] = total['NrSal'] / total['Populatie'] * 1000
rez2 = total[['Rata Ocuparii']]
rez2 = rez2.sort_values('Rata Ocuparii', ascending=False, kind='stable')
rez2.to_csv('data_out/Output2.csv')

# Cerința 3: Localitatea cu valoarea maximă
date['ProfitPeLocuitor'] = date['TotalProfit'] / date['Populatie']
maxim = date.groupby('Judet')['ProfitPeLocuitor'].idxmax()
rez3 = date.loc[maxim, ['Judet', 'DenLocalitate']]
rez3 = rez3.rename(columns={'DenLocalitate': 'Localitate'})
rez3.to_csv('data_out/Output3.csv', index=False)

# Cerința 4: Medii ponderate
variabile = ['NrFirme', 'NrSal', 'TotalCifraAfaceri', 'TotalProfit', 'TotalPierdere']

def medie_ponderata(df):
    medii = np.average(df[variabile], axis=0, weights=df['Populatie'])
    return pd.Series(medii, index=variabile)

rez4 = date.groupby('Judet')[variabile + ['Populatie']].apply(medie_ponderata)
rez4.to_csv('data_out/Output4.csv')
