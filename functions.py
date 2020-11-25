"""
# -- --------------------------------------------------------------------------------------------------- -- #
# -- project: A SHORT DESCRIPTION OF THE PROJECT                                                         -- #
# -- script: data.py : python script for data collection                                                 -- #
# -- author: YOUR GITHUB USER NAME                                                                       -- #
# -- license: GPL-3.0 License                                                                            -- #
# -- repository: YOUR REPOSITORY URL                                                                     -- #
# -- --------------------------------------------------------------------------------------------------- -- #
"""

from data import *
from datetime import datetime
import pandas as pd
pd.set_option("display.max_rows", None, "display.max_columns", None)

"""
Cargamos los datos históricos de futuros a memoria con un pkl.
Tanto daily como intraday.
Así como los datos de los escenarios de operaciones tomadas por el sistema.
"""
futuros_hist_intraday = pd.read_pickle("./EUR-USD-OPTIONS/future-historical-intraday.pkl")
futuros_hist_daily = pd.read_pickle("./EUR-USD-OPTIONS/future-historical-daily.pkl")
futuros_hist_daily_modelo = pd.read_csv("./escenarios/ResultadosModelo.csv")


"""
Vamos a colocar en cada operación pronosticada el precio correspondiente histórico.
"""
def precios_escenarios(futuros_hist_daily_modelo, datos_futuros):
    datos_escenarios = futuros_hist_daily_modelo.set_index('DATE2').drop(columns=["Date","YEAR", "MONTH", "DAY"])
    datos_escenarios.index = pd.to_datetime(datos_escenarios.index)
    datos_futuros.index = pd.to_datetime(datos_futuros.index)
    result = pd.concat([datos_escenarios, datos_futuros], axis=1).dropna()
    return result

"""
Cargamos los históricos de opciones a memoria con un pkl.
Vamos a hacer un query para ver cuales son las opciones que más nos convienen
dependiendo de la fecha de nuestras posiciones y nuestro precio spot.

Esta función arroja un solo DataFrame con la info de la posición, el precio de entrada y además
la información del hedge que se tiene que tomar.
"""
opciones_historicos = pd.read_pickle("./EUR-USD-OPTIONS/options.pkl")
def query_opciones(escenario_historicos):
    opciones = opciones_historicos.drop(columns=['Vol', 'Gamma', 'Vega', 'Theta', 'Call Open Interest',
    'Put Open Interest', 'Call Volume', 'Put volume'])
    coberturas = {}
    coberturas_df = pd.DataFrame()
    for fecha in escenario_historicos.index:
        precio_cierre = escenario_historicos.loc[fecha.strftime('%Y-%m-%d')]['close']
        precio_upper = precio_cierre + 0.001
        precio_bottom = precio_cierre - 0.001

        filters = opciones[opciones['Date'] == fecha] #Filtra por Fecha de la Operación

        filters = filters[filters['Price'] < precio_upper] #Filtra por Precio de la Operación
        filters = filters[filters['Price'] > precio_bottom] #Filtra por Precio de la Operación

        tipo = escenario_historicos.loc[fecha.strftime('%Y-%m-%d')]['Predictions']
        if tipo == 'sell':
            filters = filters[filters['Call Delta'] < 0.55]
            filters = filters[filters['Call Delta'] > 0.45]
        else:
            filters = filters[filters['Put Delta'] > -0.55]
            filters = filters[filters['Put Delta'] < -0.45]

        coberturas[fecha] = filters.head(1).set_index("Date")
        coberturas_df = coberturas_df.append(coberturas[fecha])
        #print(escenario_historicos.loc[fecha.strftime('%Y-%m-%d')])

    result = pd.concat([escenario_historicos, coberturas_df], axis=1).dropna()
    return result


def SLTP(posiciones, precios_intradia):
    '''
    La funcion recibe dos dataframes, el primero contiene las posiciones que se efectuaran en el sistema,
    con el cual hizo la prediccion. Este DataFrame tendra que contener columnas con el nombre de Predictions,
    close, high, low, open.
    El otro DataFrame tendra que contener los precios del activo seleccionado con las fechas por minuto.
    Este tendra que contener columnas con el nombre de close, open, high, low.
    Dentro de esta funcion, el Stop Loss esta fijado en 40 pips y el Take Profit fijado en 80 pips.
    '''
    SLl=[0] * len(posiciones)
    TPl=[0] * len(posiciones)
    SL = 0.0040 #Este se puede cambiar por el que se desee
    TP = 0.0080 #Este se puede cambiar por el que se desee

     #En este bucle fijaremos los Stop Loss y Take profit de las posiciones conrespondientes que arroja el modelo.
    for i in range (len(posiciones)):
        if posiciones.Predictions[i-1] == 'sell':
            SLl[i] = round(posiciones.open[i] + SL,4)
            TPl[i] = round(posiciones.open[i] - TP,4)
        elif posiciones.Predictions[i-1] == 'buy':
            SLl[i] = round(posiciones.open[i] - SL,4)
            TPl[i] = round(posiciones.open[i] + TP,4)
    posiciones['SL'] = SLl
    posiciones['TP'] = TPl

    precios_intradia['Fecha'] = precios_intradia.index.date
    posiciones['result'] = [0] * len(posiciones)


    #En este par de bucles se encontrara si el precio toco alguno de los
    # limites de precio establecidos anteriormente.
    #El resultado 1 sera para stop loss
    #El resultado 2 sera para el take profit
    posiciones = posiciones.head(10)
    print(precios_intradia.iloc[1])
    # for n in range (len(posiciones)):
    #     for i in range (len(precios_intradia)):
    #         print(precios_intradia.Fecha[i].strftime('%Y-%m-%d %H:%M:%S'))
    #         if precios_intradia.Fecha[i] == posiciones.index[n]:
    #             if SLl[n] == precios_intradia.open[i]:
    #                 posiciones['result'][n] = 1
    #             elif SLl[n] == precios_intradia.close[i]:
    #                 posiciones['result'][n] = 1
    #             elif SLl[n] == precios_intradia.high[i]:
    #                 posiciones['result'][n] = 1
    #             elif SLl[n] == precios_intradia.low[i]:
    #                 posiciones['result'][n] = 1
    #             elif TPl[n] == precios_intradia.open[i]:
    #                 posiciones['result'][n] = 2
    #             elif TPl[n] == precios_intradia.close[i]:
    #                 posiciones['result'][n] = 2
    #             elif TPl[n] == precios_intradia.high[i]:
    #                 posiciones['result'][n] = 2
    #             elif TPl[n] == precios_intradia.low[i]:
    #                 posiciones['result'][n] = 2
    # print(posiciones)
    #Por ultimo en base a los resultados anteriores se calcula cual es la perdida o ganancia representada en pips.
    #Si una posicion no se cerro durante el dia, se cerrara en el precio de close.
    # R = [0] * len(posiciones)
    # for n in range (len(posiciones)):
    #     if posiciones.Predictions[n] == 'buy':
    #         if posiciones['result'][n] == 0:
    #             R[n] = posiciones.close[n] - posiciones.open[n]
    #         elif posiciones['result'][n] == 1:
    #             R[n] = -SL
    #         elif posiciones['result'][n] == 2:
    #             R[n] = TP
    #     elif posiciones.Predictions[n] == 'sell':
    #         if posiciones['result'][n] == 0:
    #             R[n] = posiciones.open[n] - posiciones.close[n]
    #         elif posiciones['result'][n] == 1:
    #             R[n] = -SL
    #         elif posiciones['result'][n] == 2:
    #             R[n] = TP
    # posiciones['R'] = R
    # return posiciones
