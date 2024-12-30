import matplotlib.pyplot as plt


from app.data_loader import NavLoader
from app.data_loader import AqrLoader
from app.portfolio import Portfolio
from app.visualization import Visualization

'''
Première étape : Importation du benchmark et construction du portefeuille
'''
data_loader = NavLoader()
benchmark = data_loader.load_nav_data("data/fund_analysis/S&P 500 tracker.csv")
port = Portfolio()
# L'argument correspond au nombre de fonds que l'utilisateur souhaite utiliser dans son portefeuille.
# L'utilisateur doit ensuite sélectionner successivement au sein de son arborescence les fichiers
# qu'il souhaite ajouter.
port.fill_portfolio(4)

'''
Deuxième étape : Importation des séries de facteurs pour une zone géographique donnée
'''
path_daily = "data/fund_analysis/Betting Against Beta Equity Factors Daily.xlsx"
path_monthly = "data/fund_analysis/Betting Against Beta Equity Factors Monthly.xlsx"
paths = [path_daily, path_monthly]
aqr_data = AqrLoader()
factor_universe = 'Global'
dict_aqr, dict_rf = aqr_data.fill_factors(paths, factor_universe)

'''
Troisième étape : calcul des statistiques descriptives des fonds en portefeuille
'''
reporting_test = port.reporting(dict_rf, benchmark)
print(reporting_test.head(10))

'''
Quatrième étape : Réalisation d'une analyse factorielle pour chaque fonds en portefeuille
'''
factor_analysis = port.factorial_analysis(dict_aqr)
factor_loadings = factor_analysis["factor loadings"]
ptf_summary = factor_analysis['summary']
print("Charges factorielles : ")
print(factor_loadings)
# pour chaque fonds en portefeuille, affichage du résultat
# de la régression des rendements du fonds sur les facteurs d'AQR
for fund_summary in ptf_summary:
  print(f"\n Résumé des résultats pour le {fund_summary.keys} : ")
  print(fund_summary)

'''
Cinquième étape : visualisation via une application streamlit à 
lancer à l'aide de la commande suivante 
streamlit run path src/interface/streamlit_app.py
'''


"""
Sixième étape : Trace des performance lié à l'implémentation streamlit et 
l'impossibilité de tracer les performance donc affichage dans la main
"""
viz = Visualization()

# Préparer la liste des DataFrames pour plot_performance
nav_series_list = []
for name, fund in port.funds.items():
    nav_series_list.append(fund)

# Tracer les performances
print("\nGénération du graphique des performances...")
fig_perf = viz.plot_performance(nav_series_list)
plt.show()
