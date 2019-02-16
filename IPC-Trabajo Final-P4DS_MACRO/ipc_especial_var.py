#! /usr/bin/env python

# Import librerias
from datetime import datetime
import pandas as pd
import numpy as np
from scipy.stats.mstats import gmean
from matplotlib import pyplot as plt
import seaborn as sns

# Incializa seaborn con visualización default
sns.set()

'''Funciones para carga de los datos de la ODEPA y cáculo de las series 
   de variaciones de productos
'''

def carga_region(region):
    '''
    Carga y tratamiendo de los datasets de una dada 'region'
    Retorna una tabla con los productos de una region consolidados 
    '''
    pt_Aceite = carga_pi('./'+region+'/Aceite_SeriesDePrecios.xlsx')
    pt_Azucar = carga_pi('./'+region+'/Azucar_SeriesDePrecios.xlsx')
    pt_Carnes = carga_pi('./'+region+'/Carnes_SeriesDePrecios.xlsx')
    pt_Cereales = carga_pi('./'+region+'/Cereales_SeriesDePrecios.xlsx')
    pt_Frutas = carga_pi('./'+region+'/Frutas_SeriesDePrecios.xlsx')
    pt_Harina = carga_pi('./'+region+'/Harina_SeriesDePrecios.xlsx')
    pt_Hortalizas = carga_pi('./'+region+'/Hortalizas_SeriesDePrecios.xlsx')
    pt_Huevos = carga_pi('./'+region+'/Huevos_SeriesDePrecios.xlsx')
    pt_Lacteos = carga_pi('./'+region+'/Lacteos_SeriesDePrecios.xlsx')
    pt_Legumbres = carga_pi('./'+region+'/Legumbres_SeriesDePrecios.xlsx')
    pt_Pan = carga_pi('./'+region+'/Pan_SeriesDePrecios.xlsx')
    
    # Juncion de las series de variaciones de productos en una tabla única                 
    tabla = pd.concat([pt_Aceite.Aceite, pt_Azucar.Azucar,
                 pt_Carnes.Carnes, pt_Cereales.Cereales, pt_Frutas.Frutas,
                 pt_Harina.Harina, pt_Hortalizas.Hortalizas, pt_Huevos.Huevos,
                 pt_Lacteos.Lacteos, pt_Legumbres.Legumbres, pt_Pan.Pan,
                ], axis =1)
    return tabla

def carga_pi(data):
    '''
    Recibe un dataset especifico por categoria de producto de una region; 
    Limpia los datos, determina las diferentes variedades dentro de las categorias 
    de producto; Carga los precios promedio de estes productos y determina su
    variación en relación al mes anterior y calcula la media geométrica entre las
    variacenes de producto. Retorna una tabla con los valores "pit". 
    '''
    x=data.split('_')
    x = x[1].split('/')
    producto = x[-1]  
    df = limpia_data(data)
    variedades, n = encuentra_variedades(df)
    tabla_precios = precios_promedio(df, variedades)
    tabla_var = variaciones_precios_promedio(tabla_precios, n)
    tabla_var[producto] = gmean(tabla_var ,axis=1)
    tabla_var = tabla_var[1:]
    return tabla_var

def limpia_data(data):
    '''
    carga el dataset, limpia y formata los datos
    '''
    # cargar el dataset
    df = pd.read_excel(data)
    
    # encontrar donde está la linea con los nombres de las columnas
    x = df.loc[df['Unnamed: 0'] == 'Mes/Año'].index.values.astype(int)[0]

    # Redefine los nombres de las columnas, utilizandose de los nombres originales de ODEPA
    df.columns = df.loc[x]
    
    # Limpia Head y Footer
    df = df[(x+1):-1]

    # Converter los valores de los precios promedio a float 
    df['Precio promedio'] = df['Precio promedio'].astype(float)
    # Converter la fecha a formato de datatime
    df['Mes/Año'] = pd.to_datetime(df['Mes/Año'])
    
    return df

def encuentra_variedades(df):
    '''
    Encuentra las diferentes variedades de produtos en un dataset y retorna un
    set con estas variedades y el numero de productos distintos ('n'). 
    Caso no exista variedades, retorna:
    n = 1 
    variedades = ['unica']
    '''
    if (any('Producto' in x for x in df.dtypes.index)):
        variedades = set(df['Producto'])
        n = len(variedades)
    else:
        variedades = ['unica']
        n = 1
    return variedades, n 

def consolida_variedades(df):
    '''
    Verifica se el dataset posue subvariedades de productos y 
    retorna un dataset consolidado por producto y 
    formata index del dataset por fecha.
    '''
    
    if 'Calidad' in df.columns:
        df = df.groupby(['Mes/Año', 'Producto']).mean()
        df.reset_index(inplace=True)
    df.set_index('Mes/Año', inplace=True)   
    return df  

def precios_promedio(df, variedades):
    '''
    Recibe un dataset y sus variedades de productos, 
    retornando una tabla con todos los precios promedio de todas 
    las variedades de producto. En caso no existan datos, 
    carga los datos faltantes con el valor mas proximo en el tiempo.
    '''
    
    df = consolida_variedades(df)
    tabla = pd.DataFrame(index=set(df.index))
    if (any('Producto' in x for x in df.dtypes.index)):
        for i in variedades:
            var = df[df['Producto'] == i]['Precio promedio']
            tabla = pd.concat([tabla, var], axis = 1)  
    else:
        var = df['Precio promedio']
        tabla = pd.concat([tabla, var], axis = 1)  
    
    tabla.fillna(method='ffill',inplace=True )
    tabla.fillna(method='bfill',inplace=True )
    tabla.columns = variedades
    return tabla

def variaciones_precios_promedio(df, n, moneda=False):
    '''
    - En caso 'moneda == False': Cria una tabla con todos las 
      variaciones de los precios promedio de un dataset en relacion 
      al mes anterior (para todas las 'n' variedades).
    - En caso 'moneda == True', la funcion retorna precios 
      nominales y no variaciones.
    '''
    
    tabla = pd.DataFrame(index=set(df.index))
    for i in range(n):
        if moneda:
            var = df.iloc[:, [i]]
        else:
            var = 1 + df.iloc[:, [i]].pct_change(periods=1,axis = 0)

        tabla = pd.concat([tabla, var], axis = 1) 
    
    return tabla


''' 
Funciones para cálculo del IPC
'''

def carga_w():
    '''
    A partir de los ponderadores del INE, retorna la serie
    'w especial de ODEPA' y el numero de productos ('N') de la canastra
    '''
    w_ine = {
        'Aceite' : 0.59, 
        'Azucar' : 0.94,
        'Carnes' : 4.38,
        'Cereales' : 3.91,
        'Frutas' : 0.94,
        'Harina' : 0.68,
        'Hortalizas' : 2.64,
        'Huevos' : 0.33,
        'Lacteos' : 2.32,
        'Legumbres' : 2.64,
        'Pan' : 3.91,
    }
    # conversión a series de Pandas
    w_ine = pd.Series(w_ine)

    # criar ponderadores especiales para uso en el cáculo del IPC
    s = w_ine.sum()
    w = w_ine*100/s

    # Define el numero de produtos que són parte de la canastra
    N = len(w)
    if w.sum().round() == 100: 
        print("OK para {} categorias de productos".format(N))
    return w, N

def calc_ipc(pit, w):
    '''
    A partir de los datos 'pit' (precios ponderados por producto en el tiempo),
    calcula un tabla de ipc, llevandose en consideración los ponderadores especiales
    'w'. Retorna una tabla del ipc, donde incluí el 'IPC-Indice' para la región. 
    '''
    
    pio = pit[0:1]
    ipc = pd.DataFrame(index=set(pit.index))
    for i in range(len(w)):
        var = pit.iloc[:, [i]]*w[i]/pio.iat[0,i]
        ipc = pd.concat([ipc, var], axis = 1)
    ipc['IPC-Indice'] = ipc.apply(sum, axis = 1)    
    return ipc

def monta_ipc(region, graph=True):
    '''
    A partir del directorio de una region retorna tabla completa 
    del indice del IPC para la data region por producto y una 
    grafica de la variación del IPC-Indice para la dada región
    '''
    
    tabla = carga_region(region)
    w, N = carga_w()
    ipc = calc_ipc(tabla, w)
    if graph:
        ipc['IPC-Indice'].plot()
    return ipc

'''
Concatena y plota los IPCs de 2 regiones para teste
'''

def main():
    try:
        ipc_arica = monta_ipc('data/data_ar', False)
        ipc_metro = monta_ipc('data/data_rm', False)
    
        ipc = pd.DataFrame(ipc_arica['IPC-Indice'])
        ipc = pd.concat([ipc, ipc_metro['IPC-Indice']], axis =1)
        ipc.columns = ['Arica', 'Metropolitana'] 
        print () 
        print(ipc.head())
        print ()
        ipc.plot(figsize=(10,5), 
                 ylim = (98,120), 
                 title='IPC Alimentos Especial ODEPA')
        plt.show()
    except:
        print("[AVISO] Certifique que la data está corretamente cargada en sus carpetas")

# -------------------------------------------------------------
if __name__ == "__main__":
    main()