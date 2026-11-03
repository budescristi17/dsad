import os
import pandas as pd
import numpy as np

os.makedirs('data_out', exist_ok=True)
t_firme = pd.read_csv('data_in/I2014.csv', index_col=0)

# Cerința 1: Raport pe localitate
t1 = t_firme[t_firme['NrSal'] > 0].copy()
t1['Raport CA/NrSal'] = t1['TotalCifraAfaceri'] / t1['NrSal']
t1 = t1[['DenLocalitate', 'Raport CA/NrSal']]
t1 = t1.sort_values('Raport CA/NrSal', ascending=False, kind='stable')
t1.to_csv('data_out/Output1.csv')

# Legăm tabelele după Siruta.
t_pop = pd.read_csv('data_in/PopulatieLocalitati.csv', index_col=0)
t = t_firme.merge(t_pop, left_index=True, right_index=True)

# Cerința 2: Raport pe grup
t2 = t.groupby('Judet')[['NrSal', 'Populatie']].sum()
t2['Rata Ocuparii'] = t2['NrSal'] * 1000 / t2['Populatie']
t2 = t2[['Rata Ocuparii']]
t2 = t2.sort_values('Rata Ocuparii', ascending=False, kind='stable')
t2.to_csv('data_out/Output2.csv')

# Cerința 3: Localitatea cu valoarea maximă
t['ProfitPeLocuitor'] = t['TotalProfit'] / t['Populatie']
siruta_max = t.groupby('Judet')['ProfitPeLocuitor'].idxmax()
t3 = t.loc[siruta_max, ['Judet', 'DenLocalitate']].rename(columns={'DenLocalitate': 'Localitate'})
t3.to_csv('data_out/Output3.csv', index=False)

# Cerința 4: Medii ponderate
variabile = list(t_firme.columns)[1:]

def medie_ponderata(df):
    medii = np.average(df[variabile], axis=0, weights=df['Populatie'])
    return pd.Series(medii, index=variabile)

t4 = t.groupby('Judet')[variabile + ['Populatie']].apply(medie_ponderata)
t4.to_csv('data_out/Output4.csv')
