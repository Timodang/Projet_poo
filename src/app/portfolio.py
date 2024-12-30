import pandas as pd
import tkinter as tk
from tkinter import filedialog

from src.app.data_loader import NavLoader
from src.app.descriptive_stats import DescriptiveStatistics2
from src.app.factor_analysis import FactorAnalysis

class Portfolio:
  """
  Classe permettant de construire un portefeuille de fonds.

  Attributs :
  -----------

  funds : Dict
    Dictionnaire dans lequel on stocke chaque fonds que l'utilisateur ajoute au portefeuille.

  Méthodes :
  ----------

  add_fund :
    Méthode permettant d'ajouter un fonds au portefeuille.

  fill_portfolio :
    Méthode permettant de construire le portefeuille pour un nombre de fonds choisi
    par l'utilisateur.

  _periodicity_adjustement :
    Méthode permettant de déterminer la périodicité des données (daily, monthly, other).

  reporting :
    Méthode permettant de récupérer toutes les statistiques descriptives pour chaque fonds en portefeuille

  factorial_analysis :
    Méthode permettant de réaliser une analyse factorielle pour chaque fonds en portefeuille.
  """

  def __init__(self):
    """
    Initialise un portefeuille vide.
    """
    self.funds = {}

  def add_fund(self, name:str, nav_series:pd.DataFrame):
    """
    Méthode permettant d'ajoute un fonds au portefeuille.

    Parameters :
    - name : str, nom du fonds qui est ajouté (ex : fonds 1, fonds 2, fonds 3, ...).
    - nav_serie :  DataFrame contenant la série temporelle des valeurs liquidatives
    du fonds ajouté par l'utilisateur.

    L'une des limites de cette méthode est est l'utilisation des noms "fonds 1", "fonds 2", ...
    à défaut de pouvoir récupérer précisément le nom des fonds importés.
    """
    self.funds[name] = nav_series

  def fill_portfolio(self, nb_funds: int):
    """
    Méthode permettant, pour un nombre de fonds choisi par l'utilisateur,
    de construire le portefeuuille

    Parameters :
     - nb_funds : int, nombre de fonds que l'utilisateur souhaite ajouter au portefeuille.

    Reuturns :
     - Le dictionnaire self.funds rempli avec, pour chaque fonds, un dataframe
       contenant la série temporelle des NAV.
    """
    data_loader = NavLoader()
    # Création d'une liste vierge pour stocker les paths utilisés pour importer
    # les données.
    list_file = []

    for i in range(nb_funds):
      # Ouverture de l'arborescence des fichiers pour permettre à l'utilisateur
      # de sélectionner un fichier contenant le fonds qu'il souhaite ajouter au portefeuille.
      root = tk.Tk()
      root.withdraw()
      filename = filedialog.askopenfilename()
      # Les paths sont stockés dans une liste. Dans le cas où l'utilisateur souhaite
      # ajouter deux fois le même fonds. Un message lui indique que le fonds est déjà en portefeuille.
      if filename not in list_file:
        list_file.append(filename)
        self.add_fund("fund " + str(i + 1), data_loader.load_nav_data(filename))
      else:
        print('This fund was already added to the portfolio')
    return self.funds

  @staticmethod
  def _periodicity_adjustment(df: pd.DataFrame):
    """
    Méthode permettant d'ajuster le coefficient d'annualisation utilisé pour les calculs
    selon que l'on travaille sur des données quotidiennes ou mensuelles.

    Returns :
    - Un coefficient d'annualisation de 12 si la durée entre deux dates est comprise entre 20 et 31 jours
    - Un coefficient d'annualisation de 252 si la durée entre deux dates est inférieure à 7 jours
    - Une erreur sinon (pas de fichiers AQR pour des périodicités différentes du daily et monthly)
    """
    dates = df['Date']
    # Récupération de la différence de dates entre les deux premières NAV du fichier
    delta_time = dates[2] - dates[1]
    # Un pas de temps de 6 jours est autorisé pour vérifier que les données soit quotidiennes
    # car il peut y avoir un écart de plus d'un jour entre deux dates (we, jour férié, ...).
    if delta_time.days < 7:
      return 252
    elif 27 < delta_time.days <= 31:
      return 12
    else:
      raise Exception(f'Data have to be daily or monthly to compute the calculations')

  def _merging_data_periodicity(self, fund : pd.DataFrame, aqr : dict):
    """
    Méthode utilisée uniquement dans la classe portfolio permettant
    d'aligner les périodes entre les fonds et les fichiers d'AQR pour réaliser le calcul
    des statistiques et l'analyse factorielle.

    Parameters :
    - fund : DataFrame contenant le fonds sur lequel on souhaite effectuer les traitements
    - aqr : DataFrame contenant soit les séries de facteur ou le taux sans risque

    Returns :
    - Un dataframe contenant une colonne date, une colonne NAV et les facteurs / RF mergés selon
    les dates
    """
    # Récupération de la périodicité (252 : daily, 12 monthly, erreur sinon)
    periodicity = self._periodicity_adjustment(fund)

    if periodicity == 252:
      daily_df = aqr['Daily']
      df_merged_data = pd.merge(fund, daily_df, on = 'Date', how = 'inner')
      return df_merged_data, periodicity

    elif periodicity == 12:
      monthly_df = aqr['Monthly']
      df_merged_data = pd.merge(fund, monthly_df, on = 'Date', how = 'inner')
      return df_merged_data, periodicity

  def reporting(self, rf:dict, benchmark:pd.DataFrame):
    """
    Méthode permettant de reporter toutes les statistiques calculées pour un fonds du portefeuille

    Parameters :
    - rf_dict : dictionnaire contenant les séries de taux sans risque en monthly et daily
    - benchmark : DataFrame contenant les prix du benchmark

    Returns :
    - DataFrame contenant les statistiques descriptives pour chaque fonds du portefeuille.
    Ce DataFrame contient un ensemble de statistiques de performance et de risque (ligne)
    pour chaque fonds (colonne).
    """
    reporting = pd.DataFrame()

    # Boucle sur les fonds en portefeuille
    for name, fund in self.funds.items():
      df_fund, periodicity = self._merging_data_periodicity(fund, rf)
      df_data_to_calculate_stats = pd.merge(df_fund, benchmark, on = 'Date', how = 'inner')
      df_data_to_calculate_stats.columns = ['Date', 'NAV Fund', 'RF', 'Bench']

      stats_fund = DescriptiveStatistics2(df_data_to_calculate_stats['NAV Fund'],
                                          df_data_to_calculate_stats['RF'],
                                          periodicity)

      # Construction d'un objet "stats_bench" pour calculer les rendements du benchmark
      # qui sont utilisés pour calculer certaines statistiques
      stats_bench = DescriptiveStatistics2(df_data_to_calculate_stats['Bench'],
                                           df_data_to_calculate_stats['RF'],
                                           periodicity)
      bench_returns = stats_bench.calculate_daily_returns

      reporting[name] = stats_fund.reporting_stats(bench_returns)

    #  Nom des statistiques calculées pour chaque ligne du tableau
    index = {0: 'Perf annualisée', 1: 'Perf totale', 2: 'Vol', 3: 'Sharpe', 4: 'Sortino', 5: 'Downside vol',
             6: 'Rendement excédentaire total', 7: 'Rendemente excédentaire annualisé', 8: 'beta',
             9: 'TE', 10: 'alpha', 11: 'beta up', 12: 'beta down', 13: 'MDD'}
    reporting = reporting.rename(index, axis=0)
    return reporting

  def factorial_analysis(self, dict_aqr:dict):
    """
    Méthode permettant d'effectuer l'analyse factorielle des fonds en portefeuille
    à partir des séries de facteurs d'AQR.

    Parameters :
    - dict_aqr : Dictionnaire contenant les séries temporelles des 5 facteurs d'AQR
    pour une Zone Géographique donnée en fréquence quotidienne et mensuelle.

    Returns :
    - Un dictionnaire contenant les charges factorielles et le résumé de l'analyse factorielle
    réalisée pour chaque fonds.
    """
    df_factor_loadings = pd.DataFrame()
    list_analysis_summary = []

    factors_list = ['MKT', 'SMB', 'HML FF', 'HML Devil', 'UMD']
    for name, fund in self.funds.items():
        # Récupération du DataFrame avec la NAV et les facteurs alignés au niveau des dates
        df_factorial_analysis = self._merging_data_periodicity(fund, dict_aqr)[0]
        # Récupération des séries contenant la NAV et les facteurs AQR
        aqr_series = df_factorial_analysis[factors_list]
        nav_series = df_factorial_analysis.drop(['Date', 'MKT', 'SMB', 'HML FF', 'HML Devil', 'UMD'], axis=1)
        nav_series.columns = [name]
        # Réalisation de l'analyse factorielle et récupération des charges
        factor_analysis = FactorAnalysis(nav_series, aqr_series)
        df_factor_loadings[name] = factor_analysis.calculate_factor_loadings()
        list_analysis_summary.append(factor_analysis.summarize_results())

    return {"factor loadings":df_factor_loadings, "summary":list_analysis_summary}