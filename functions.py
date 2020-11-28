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
import time
from datetime import datetime, date, time, timedelta
import pandas as pd
pd.set_option("display.max_rows", None, "display.max_columns", None)
pd.options.display.width=None

"""
Cargamos los datos históricos de futuros a memoria con un pkl.
Tanto daily como intraday.
Así como los datos de los escenarios de operaciones tomadas por el sistema.
"""
futuros_hist_intraday = pd.read_pickle("./backtest/future-historical-intraday.pkl")
futuros_hist_daily = pd.read_pickle("./backtest/future-historical-daily.pkl")
futuros_hist_daily_modelo = pd.read_csv("./escenarios/ResultadosModelo.csv")

"""
Vamos a colocar en cada operación pronosticada el precio correspondiente histórico.
"""
def precios_escenarios(futuros_hist_daily_modelo, datos_futuros):
    datos_escenarios = futuros_hist_daily_modelo.set_index('DATE2').drop(columns=["Date","YEAR", "MONTH", "DAY"])
    datos_escenarios.index = pd.to_datetime(datos_escenarios.index)
    datos_futuros.index = pd.to_datetime(datos_futuros.index)
    result = pd.concat([datos_escenarios, datos_futuros], axis=1).dropna()
    result['p_ap_op'] = result.open
    return result


"""
Cargamos los históricos de opciones a memoria con un pkl.
Vamos a hacer un query para ver cuales son las opciones que más nos convienen
dependiendo de la fecha de nuestras posiciones y nuestro precio spot.

Esta función arroja un solo DataFrame con la info de la posición, el precio de entrada y además
la información del hedge que se tiene que tomar.
"""

opciones_historicos = pd.read_pickle("./backtest/options.pkl")
def query_opciones(escenario_historicos):
    opciones = opciones_historicos.drop(columns=['Gamma', 'Vega', 'Theta', 'Call Open Interest',
    'Put Open Interest', 'Call Volume', 'Put volume'])
    coberturas = {}
    coberturas_df = pd.DataFrame()

    for fecha in escenario_historicos.index:
        fecha_fix = datetime.strptime(fecha.strftime('%Y-%m-%d'), '%Y-%m-%d')
        fecha_fix_up = fecha_fix + timedelta(days=5)
        fecha_fix_down = fecha_fix - timedelta(days=5)

        precio_cierre = escenario_historicos.loc[fecha.strftime('%Y-%m-%d')]['open']

        precio_upper = precio_cierre + 0.1
        precio_bottom = precio_cierre - 0.1

        filters = opciones[opciones['Date'] < fecha_fix_up] #Filtra por Precio de la Operación
        filters = filters[filters['Date'] > fecha_fix_down] #Filtra por Precio de la Operación
        filters = filters[filters['Date'] == fecha]

        filters = filters[filters['Days'] > 1] #Filtra por Precio de la Operación
        filters = filters[filters['Days'] < 5] #Filtra por Precio de la Operación

        filters = filters[filters['Price'] < precio_upper] #Filtra por Precio de la Operación
        filters = filters[filters['Price'] > precio_bottom] #Filtra por Precio de la Operación

        tipo_operacion = escenario_historicos.loc[fecha.strftime('%Y-%m-%d')]['Predictions']

        if tipo_operacion == 'sell':
            filters = filters[filters['Call Delta'] < 0.55]
            filters = filters[filters['Call Delta'] > 0.45]
            filters['Put Delta'] = 0
        else:
            filters = filters[filters['Put Delta'] > -0.55]
            filters = filters[filters['Put Delta'] < -0.45]
            filters['Call Delta'] = 0

        filters = filters.sort_values(by=['Date'], ascending=False)
        filters['Prediciton Date'] = fecha
        coberturas[fecha] = filters.head(1)
        coberturas_df = coberturas_df.append(coberturas[fecha])
    coberturas_df = coberturas_df.set_index('Date')
    result = pd.concat([escenario_historicos, coberturas_df], axis=1).dropna()

    '''SAVING TO CSV AND PICKLE '''

    result.to_csv('./backtest/queried_options.csv')
    result.to_pickle('./backtest/queried_options.pkl')
    return result

#coberturas_df.to_csv('recomendacion_opcioens.csv')
# futuros_hist_intraday = load_data_intraday(2017, 2020)
# futuros_hist_daily = load_data_daily(2017, 2020)

def SLTP(posiciones, precios_intradia):
    '''
    La funcion recibe dos dataframes, el primero contiene las posiciones que se efectuaran en el sistema,
    con el cual hizo la prediccion. Este DataFrame tendra que contener columnas con el nombre de Predictions,
    close, high, low, open.
    El otro DataFrame tendra que contener los precios del activo seleccionado con las fechas por minuto.
    Este tendra que contener columnas con el nombre de close, open, high, low.
    Dentro de esta funcion, el Stop Loss esta fijado en 5 pips y el Take Profit fijado en 10 pips.
    '''
    SLl=[0] * len(posiciones)
    TPl=[0] * len(posiciones)

    SL = 0.0010 #Este se puede cambiar por el que se desee
    TP = 0.0010 #Este se puede cambiar por el que se desee

     #En este bucle fijaremos los Stop Loss y Take profit de las posiciones conrespondientes que arroja el modelo.
    for i in range (len(posiciones)):
        if posiciones.Predictions[i-1] == 'sell':
            SLl[i] = round(posiciones.open[i] + SL, 4)
            TPl[i] = round(posiciones.open[i] - TP, 4)
        elif posiciones.Predictions[i-1] == 'buy':
            SLl[i] = round(posiciones.open[i] - SL, 4)
            TPl[i] = round(posiciones.open[i] + TP, 4)
    posiciones['SL'] = SLl
    posiciones['TP'] = TPl

    posiciones['result'] = ''
    posiciones['p_c_op'] = 0.0
    posiciones['pips'] = float(0.00000)
    #posiciones = posiciones.head(5) ### eliminar

    daily_df = pd.DataFrame()
    for d in range(len(posiciones.index)):

        position_day = posiciones.index[d].strftime('%Y-%m-%d')
        intraday_date = precios_intradia.index.strftime('%Y-%m-%d')
        intrady_indexer_filter = precios_intradia[intraday_date == position_day]
        minute_df = pd.DataFrame()

        for minute in intrady_indexer_filter.index:

            high = intrady_indexer_filter.loc[minute]['high']
            open = intrady_indexer_filter.loc[minute]['open']
            close = intrady_indexer_filter.loc[minute]['close']
            low = intrady_indexer_filter.loc[minute]['low']

            stop_loss =  posiciones.loc[position_day]['SL']
            take_profit = posiciones.loc[position_day]['TP']

            condition_sell_sl = (high >= stop_loss or low >= stop_loss or open >= stop_loss or close >= stop_loss)
            condition_sell_tp = (high <= take_profit or low <=  take_profit or open <= take_profit or close <= take_profit)

            condition_buy_sl = (high <= stop_loss or low <= stop_loss or open <= stop_loss or close <= stop_loss)
            condition_buy_tp = (high >= take_profit or low >=  take_profit or open >= take_profit or close >= take_profit)

            '''
            SELL SIDE
            '''
            if posiciones.Predictions[d] == 'sell':
                if condition_sell_tp == True:
                    posiciones.result[d] = 'TP'
                    posiciones.p_c_op[d] = posiciones.close[d]
                    posiciones.pips[d] = posiciones.p_ap_op[d]-posiciones.TP[d]
                    minute_df = minute_df.append(posiciones.loc[position_day])
                    break
                elif condition_sell_sl == True:
                    posiciones.result[d] = 'SL'
                    posiciones.pips[d] = posiciones.p_ap_op[d]-posiciones.SL[d]
                    minute_df = minute_df.append(posiciones.loc[position_day])
                    break
                else:
                    posiciones.result[d] = 'FLOAT'
                    posiciones.p_c_op[d] =posiciones.close[d]
                    posiciones.pips[d] = posiciones.TP[d]-posiciones.close[d]
                    minute_df = minute_df.append(posiciones.loc[position_day])

            '''
            BUY SIDE
            '''
            if posiciones.Predictions[d] == 'buy':
                if condition_buy_tp == True:
                    posiciones.result[d] = 'TP'
                    posiciones.p_c_op[d] = posiciones.close[d]
                    posiciones.pips[d] = posiciones.TP[d]- posiciones.p_ap_op[d]
                    minute_df = minute_df.append(posiciones.loc[position_day])
                    break
                elif condition_buy_sl == True:
                    posiciones.result[d] = 'SL'
                    posiciones.pips[d] = posiciones.SL[d]-posiciones.p_ap_op[d]
                    minute_df = minute_df.append(posiciones.loc[position_day])
                    break
                else:
                    posiciones.result[d] = 'FLOAT'
                    posiciones.p_c_op[d] =posiciones.close[d]
                    posiciones.pips[d] = posiciones.close[d]-posiciones.p_ap_op[d]
                    minute_df = minute_df.append(posiciones.loc[position_day])
            posiciones.pips = posiciones.pips * 10_000
        daily_df = daily_df.append(minute_df.tail(1))

        ''' SAVING THE DATA TO CSV AND PICKLE '''

        daily_df.to_csv('./backtest/sltp_backtest.csv')
        daily_df.to_pickle('./backtest/sltp_backtest.pkl')
    return daily_df
