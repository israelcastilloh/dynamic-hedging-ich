
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
from functions import *

load_data_intraday()
escenario_historicos = precios_escenarios(futuros_hist_daily_modelo, futuros_hist_daily)
#print(escenario_historicos)

coberturas_historicas = query_opciones(escenario_historicos)
#print(coberturas_historicas)

SLTP = SLTP(coberturas_historicas, futuros_hist_intraday)
print(SLTP)
