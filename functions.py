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


"""
Cargamos los datos históricos de futuros a memoria con un pkl.
Tanto daily como intraday.
Así como los datos de los escenarios de operaciones tomadas por el sistema.
"""
futuros_hist_intraday = pd.read_pickle("./EUR-USD-OPTIONS/future-historical-intraday.pkl")
futuros_hist_daily = pd.read_pickle("./EUR-USD-OPTIONS/future-historical-daily.pkl")
escenarios = read_escenarios()['SegundoEscenario']

"""
Vamos a colocar en cada operación de loescenario el precio correspondiente histórico.
"""
def precios_escenarios(datos_escenarios, datos_futuros):
    datos_escenarios = datos_escenarios.set_index('Fecha')
    for fecha in datos_escenarios.index:
        datetimeobject = datetime.strptime(fecha, '%d/%m/%y')
        newformat = datetimeobject.strftime('%Y-%m-%d')
        datos_escenarios = datos_escenarios.rename({fecha: newformat}, axis='index')
    datos_escenarios.index = pd.to_datetime(datos_escenarios.index)
    datos_futuros.index = pd.to_datetime(datos_futuros.index)
    result = pd.concat([datos_escenarios, datos_futuros], axis=1).dropna()
    return result

"""
Cargamos los históricos de opciones a memoria con un pkl.
Vamos a hacer un query para ver cuales son las opciones que más nos convienen
dependiendo de la fecha de nuestras posiciones y nuestro precio spot.
"""
opciones_historicos = pd.read_pickle("./EUR-USD-OPTIONS/options.pkl")
def query_opciones(escenario_historicos):
    opciones = opciones_historicos.drop(columns=['Vol', 'Gamma', 'Vega', 'Theta', 'Call Open Interest',
    'Put Open Interest', 'Call Volume', 'Put volume'])
    coberturas = {}
    for fecha in escenario_historicos.index:
        precio_cierre = escenario_historicos.loc[fecha.strftime('%Y-%m-%d')]['close']
        precio_upper = precio_cierre + 0.001
        precio_bottom = precio_cierre - 0.001

        filters = opciones[opciones['Date'] == fecha]
        filters = filters[filters['Price'] < precio_upper]
        filters = filters[filters['Price'] > precio_bottom]

        tipo = escenario_historicos.loc[fecha.strftime('%Y-%m-%d')]['Operaciones']
        if tipo == 'sell':
            filters = filters[filters['Call Delta'] < 0.55]
            filters = filters[filters['Call Delta'] > 0.45]
        else:
            filters = filters[filters['Put Delta'] > -0.55]
            filters = filters[filters['Put Delta'] < -0.45]

        coberturas[fecha] = filters
    return coberturas
