import pandas as pd
import statsmodels.api as sm

class FactorAnalysis:
  """
  Classe utilisée pour effectuer l'anaylyse factorielle
  d'un fonds en utilisant les séries de facteurs AQR.

  Attributs :
  -----------

  nav_series : pd.DataFrame / Serie
    Série contenant les NAV d'un fonds ajouté au portefeuille.

  factors_data : pd.DataFrame / Serie
    Série contenant les séries de facteurs d'AQR pour une Zone Géographique donnée.

  Méthodes :
  ----------

  _calculate_daily_returns :
    Méthode permettant de calculer les rendements d'une série de NAV

  regression_analysis :
    Méthode permettant de réaliser une régression linéaire d'une série de rendements
    sur les facteurs d'AQR.

  calculate_factor_loadings :
    Méthode permettant de calculer les charges factorielles générées par la régression.

  summarize_results :
    Méthode permettant de synthétiser les résultats de l'analyse factorielle.
  """

  def __init__(self, nav_series, factors_data):
    """
    Initialise la classe avec les séries NAV et les facteurs.

    Parameters:
    - nav_series: Série ou DataFrame des valeurs liquidatives d'un fonds.
    - factors_data : DataFrame des facteurs (AQR) avec les mêmes dates.
    """
    self.nav_series = nav_series
    self.factors_data = factors_data
    self.returns = self._calculate_returns()

  def _calculate_returns(self):
    """
    Méthode permettant de calculer les rendements des fonds et de supprimer
    les valeurs manquantes.

    Returns :
    - Série ou DataFrame des rendements quotidiens.
    """
    return self.nav_series.pct_change().dropna()

  def _regression_analysis(self):
    """
    Méthode permettant de régresser les rendements d'un fonds
    sur les séries de facteurs d'AQR pour déterminer l'exposition du fonds
    à plusieurs facteur de risque (value, momentum, ...).

    Returns :
    - Un dictionnaire contenant le résultat de la régression linéaire
    """
    results = {}

    name = self.nav_series.columns.values.tolist()[0]
    # Align indices
    y = self.returns
    x = self.factors_data[1:]

    # Add constant for alpha
    x = sm.add_constant(x)

    # Perform regression
    model = sm.OLS(y, x).fit()
    results[name] = model
    return results

  def calculate_factor_loadings(self):
    """
    Méthode permettant de calculer les charges factorielles
    (coefficients des facteurs dans la régression).

    Returns :
    - DataFrame des charges factorielles pour le fonds sur lequel l'analyse est effectuée
    """
    loadings = {}
    regression_results = self._regression_analysis()
    for fund, model in regression_results.items():
      loadings[fund] = model.params.drop('const')  # Exclut l'alpha
    return pd.DataFrame(loadings)

  def summarize_results(self):
    """
    Fournit un résumé des résultats de la régression factorielle pour chaque fonds.
    :return: Dictionnaire contenant les résumés.
    """
    regression_results = self._regression_analysis()
    summaries = {}
    for fund, model in regression_results.items():
      summaries[fund] = model.summary()
    return summaries
