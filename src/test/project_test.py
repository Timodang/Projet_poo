import unittest
import datetime as dt
import pandas as pd

from src.app.data_loader import NavLoader
from src.app.data_loader import AqrLoader
from src.app.portfolio import Portfolio

class TestImportNavData(unittest.TestCase):
  """
  Classe permettant de vérifier le bon fonctionnement des modules d'import
  de la classe de NAV à partir d'un exemple fourni dans le fichier Fund test import
  """

  def setUp(self):
    data_loader = NavLoader()
    self.fund_test = data_loader.load_nav_data('Fund test import.xlsx')
    data = {'Date':[dt.datetime(2024,1,31), dt.datetime(2024,2,1),
                    dt.datetime(2024,2,2), dt.datetime(2024,2,5),
                    dt.datetime(2024,2,6), dt.datetime(2024,2,7),
                    dt.datetime(2024,2,8), dt.datetime(2024,2,9)],
            'NAV':[100, 97.9, 105.2,110.92, 101.9, 103, 102.4,112.5]}
    self.expected = pd.DataFrame(data, columns = ['Date', 'NAV'])

  def test_import_result(self):
    """
    Vérification que le DataFrame renvoyé corresponde bien
    au tableau de donnée de l'excel trié de manière croissante par rapport aux dates.
    """
    self.assertEqual(True, self.fund_test.equals(self.expected))

class TestPortfolioImplementation(unittest.TestCase):
  """
  Test de la création du portefeuille et des calculs renvoyés.

  Etant donné que les données d'AQR / RF sont fusionnés au sein de méthodes
  propres au portefeuille, il n'est pas possible de tester que les données utilisées
  pour les calculs sont bonnes. Seules les NAV peuvent être vérifiées.

  Les valeurs utilisées pour comparer les performances figure dans le fichier excel joint
  dans la feuille '

  Remarque : la précision utilisée pour vérifier les calculs est de 4 décimales. Avec cette précision,
  les tests sur le ratio de Sharpe et de Sortino sont rejetés. Ce rejet est lié à un décalage
  dans le calcul du rendement excédentaire annualisé à partir de la troisième décimale.
  Les résultats obtenus renvoyés par le code restent néanmoins très proche de ceux de l'excel.

  Remarque : les tests sur les statistiques prennent beaucoup de temps car les
  fichiers sont importés une fois par tests (soit environ une trentaine de minutes pour l'exécution
  de l'ensemble des tests).
  """

  def setUp(self):
    data_loader = NavLoader()
    benchmark = data_loader.load_nav_data("/Users/timotheedangleterre/PycharmProjects/PythonPOO/src/data/fund_analysis/S&P 500 tracker.csv")
    port = Portfolio()
    port.fill_portfolio(2)  # Sélection du fichier de test deux fois d'affilé pour vérifier qu'il n'y a qu'un import
    path_daily = "/Users/timotheedangleterre/PycharmProjects/PythonPOO/src/data/fund_analysis/Betting Against Beta Equity Factors Daily.xlsx"
    path_monthly = "/Users/timotheedangleterre/PycharmProjects/PythonPOO/src/data/fund_analysis/Betting Against Beta Equity Factors Monthly.xlsx"
    paths = [path_daily, path_monthly]
    aqr_data = AqrLoader()
    factor_universe = 'Global'
    self.dict_aqr, self.dict_rf = aqr_data.fill_factors(paths, factor_universe)
    self.stats = port.reporting(self.dict_rf, benchmark)
    self.stats_expected = pd.read_excel('Fund test import.xlsx', 'Fund stats calc on excel')

  def test_performance(self):
    self.assertAlmostEqual(self.stats.iloc[0,0], self.stats_expected.iloc[0,1], 4)
    self.assertAlmostEqual(self.stats.iloc[1,0], self.stats_expected.iloc[1,1], 4)

  def test_vol(self):
    self.assertAlmostEqual(self.stats.iloc[2,0], self.stats_expected.iloc[2,1], 4)

  def test_excess_perf(self):
    self.assertAlmostEqual(self.stats.iloc[6,0], self.stats_expected.iloc[6,1], 4)
    self.assertAlmostEqual(self.stats.iloc[7,0], self.stats_expected.iloc[7,1], 4)

  def test_sharpe(self):
    self.assertAlmostEqual(self.stats.iloc[3,0], self.stats_expected.iloc[3,1], 4)

  def test_downside_vol(self):
    self.assertAlmostEqual(self.stats.iloc[5,0], self.stats_expected.iloc[5,1], 4)

  def test_sortino(self):
    self.assertAlmostEqual(self.stats.iloc[4,0], self.stats_expected.iloc[4,1], 4)

  def test_alpha_beta(self):
    self.assertAlmostEqual(self.stats.iloc[8,0], self.stats_expected.iloc[8,1], 4)
    self.assertAlmostEqual(self.stats.iloc[6,0], self.stats_expected.iloc[6,1], 4)

  def test_TE(self):
    self.assertAlmostEqual(self.stats.iloc[9,0], self.stats_expected.iloc[9,1], 4)

if __name__ == "__main__":
  unittest.main()
