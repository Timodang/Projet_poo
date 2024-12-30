import pandas as pd
import os
from abc import ABC, abstractmethod

from src.app.data_formating import DataFormating


class DataImportError(Exception):
  """
  Classe permettant de lever une erreur personnalisée
  afin d'informer l'utilisateur si l'importation a échoué
  """
  def __init__(self, cls, method, *args):
    self.cls = cls
    self.method = method
    self.args = args

  def __str__(self):
    return f"Error in class '{self.cls.__name__}', method '{self.method}' with arguments {self.args}"

class Loader(ABC):
  """
  Classe abstraite afin de garantir
  la présence d'une méthode _load_file dans les
  classes qui doivent importer des fichiers depuis l'ordinateur.
  """
  @abstractmethod
  def _load_file(self, *args):
    pass

class NavLoader(Loader, DataFormating):
  """
  Classe permettant de charger et de retraiter les fichiers de données contenant les NAV
  des fonds que l'utilisateur souhaite ajouter à son portefeuille.

  Paramètres :
  ------------

  - Classe Loader : classe abstraite contenant la méthode _load_file qui est
  implémentée par toutes les classes réalisant des imports de données.
  - Classe DataFormating : classe utilitaire contenant plusieurs méthodes
  permettant de formaliser les données importées.

  Attributs :
  -----------

  - self.nav_data : dataframe contenant les dates et les NAV associées pour un fonds choisi
  par l'utilisateur.

  Méthodes:
  ---------

  - _load_file : Méthode permettant à l'utilisateur d'importer un fichier contenant les
  NAV d'un fonds depuis son ordinateur. Cette méthode n'est utilisée que les classes d'imports
  (NavLoader & AqrLoader).
  - _clean_dataframe : méthode permettant de retraiter les données obtenues pour faciliter
  les traitements futurs.
  - load_nav_data : Méthode permettant de récupérer les NAV retraités du fonds sélectionné
  par l'utilisateur.
  """

  def __init__(self):
    self.nav_data = None

  def _load_file(self, file_path:str):
    """
    Méthode permettant à l'utilisateur de sélectionner le fichier contenant les NAV
    qu'il souhaite importer.

    Une bonne utilisation implique que la série temporelle des NAV soit renseignée au
    sein de la première feuille du fichier. Une erreur est levée s
    i le programme ne parvient pas à récupérer les données.

     Parameters :
     - Le chemin d'accès au fichier sélectionné par l'utilisateur au sein de son arborescence.

     Returns :
     - Un DataFrame contenant toutes les données importées à partir des entêtes.
    """

    # Récupération de l'extension du fichier
    ext = os.path.splitext(file_path)[1].lower()
    try:
      # Distinction selon que le fichier d'entrée soit renseignée en csv ou dans un format excel
      if ext == ".csv":
        # Les données sont chargées 2 fois : une fois pour identifier les entêtes, une seconde
        # fois pour ne récupérer que le tableau renseigné à partir des entêtes.
        data = pd.read_csv(file_path)
        junk_rows = self._header_row(data)
        return pd.read_csv(file_path, sep=",", skiprows=junk_rows)

      elif (ext == ".xlsx") or (ext == ".xls"):
        data = pd.read_excel(file_path)
        junk_rows = self._header_row(data)
        return pd.read_excel(file_path, skiprows=junk_rows)

      else:
        raise ValueError("Unsupported file format. Use .csv, .xlsx, or .xls.")
    # En cas d'erreur lors de l'import des données, une erreur est renvoyée à l'utilisateur
    except Exception:
      raise DataImportError(NavLoader, '_load_file', file_path)

  def load_nav_data(self, file_path:str):
    """
    Méthode permettant de récupérer les NAV importées depuis un fichier csv ou excel
    une fois que les données ont été retraitées.

    Parameters :
    - file_path : chemin vers le fichier contenant les NAV du fonds

    Returns : DataFrame contenant uniquement une colonne Date en datetime
    et une colonne NAV en float.
    """
    try:
      self.nav_data = self._load_file(file_path)
      self.nav_data = self._clean_dataframe()
      print("Données NAV chargées avec succès.")
      return self.nav_data
    except Exception:
      raise DataImportError(NavLoader, '_load_nav_data', file_path)

  def _clean_dataframe(self):
    """
    Méthode permettant de nettoyer le dataframe importé
    afin de ne conserver qu'une série temporelle contenant les NAV du fonds,
    triées par ordre chronologique (donnée,la plus ancienne -> donnée la plus récente).
    Les entêtes des colonnes conservées sont renommées en tant que Date et NAV

    Cette méthode est sensible aux noms d'entêtes du fichier choisi par l'utilisateur. Plusieurs cas
    sont testés pour déterminés où se trouvent les dates / NAV. En pratique, une erreur
    sera renvoyée si l'une de ces 2 séries de données n'est pas trouvée.

    Returns :
    Le dataframe contenant les dates et les NAV du fonds avec :
    - Les dates au format datetime
    - Les NAV en float
    - Des données triées par rapport aux dates (de la plus ancienne à la plus récente)
    """
    result = pd.DataFrame()
    column_names = self.nav_data.columns
    for elem in column_names:
      # Identification de la colonne des dates. L'entête de la colonne contenant
      # les dates peut avoir plusieurs valeurs possibles.
      if (elem == "Date") or (elem == " Date de valorisation") or(elem == "DATE"):
        result[elem] = self.nav_data[elem]
      # Identification de la colonne contenant les NAV. L'entête de la colonne
      # contenant les NAV peut avoir plusieurs valeurs possibles.
      if ((elem == "NAV") or (elem == "Price") or (elem == "VL") or
        (elem == "NAV ($)") or (elem == 'Clôture/Dernier') or (elem == "Close")
         or elem == "Nav"):
        result[elem] = self.nav_data[elem]

    # Les colonnes sont renommées pour uniformiser les traitements ultérieurs
    result.columns = ['Date', 'NAV']
    # Retraitement des données
    result = result.dropna()
    result['Date'] = self._date_converter(result)
    result = self._float_converter(result)
    result = result.sort_values(by='Date', ascending=True)
    result = result.reset_index(drop=True)
    return result

class AqrLoader(Loader, DataFormating):
  """
  Classe qui hérite de la classe abstraite loader et DataFormating. Son objectif est de gérer
  l'import et la transformation des séries AQR qui seront utilisées ultérieurement pour le calcul
  des statistiques descriptives et la réalisation d'une analyse factorielle.

   Paramètres :
  ------------

  - Classe Loader : classe abstraite contenant la méthode _load_file qui est
  implémentée par toutes les classes réalisant des imports de données.
  - Classe DataFormating : classe utilitaire contenant plusieurs méthodes
  permettant de formaliser les données importées.

  Attributs :
  -----------
  - aqr_data : Dictionnaire contenant les séries de facteurs pour une zone géographique spécifiée
  et pour chaque périodicité
  - rf_data : Dictionnaire contenant la série de taux sans risque pour chaque périodicité

  Méthodes :
  ----------

  - _load_file : Méthode qui permet d'itérer sur les différentes feuilles
  où sont stockées chaque facteur afin de récupérer les séries associées à
  la zone géographique souhaitée par l'utilisateur.
  - load_aqr_factor : Méthode permettant de récupérer et de retraiter l'ensemble
  des séries de facteurs pour une zone géographique donnée.
  - load_RF : Méthode permettant de récupérer et de retraiter
  la série de taux sans risque contenue dans le fichier d'AQR.
  """

  def __init__(self):
    self.aqr_data = {}
    self.rf_data = {}

  def fill_factors(self, paths:list, universe:str):
    """
    Méthode permettant de remplir les dictionnaires dans lesquels seront stockés
    les séries de facteurs d'AQR et de taux sans risque en daily et monthly.

    Parameters:
      - paths : liste contenant le path des fichiers à utiliser
      - universe : Zone Géographique correspondant à l'univers d'investissement

    Returns :
    - Les attributs de la classe remplie
    """

    periodicity_name = ['Daily', 'Monthly']
    # paths contient le chemin relatif vers le fichier daily puis monthly
    for i in range(len(paths)):
      path = paths[i]
      aqr_factors = self.load_aqr_factor(path, universe)
      rf = self.load_rf(path)
      self.aqr_data[periodicity_name[i]] = aqr_factors
      self.rf_data[periodicity_name[i]] = rf

    return self.aqr_data, self.rf_data

  def _load_file(self, file_path:str, factor: str):
    """
    Méthode permettant d'importer le fichier contenant les facteurs AQR.
    La principale différence avec la méthode de la classe NavLoader est liée au fait que les
    données sont stockées sur plusieurs feuilles excel.

    Parameters:
      - file_path : str, chemin du fichier contenant les facteurs AQR
      - factor : str, nom de chaque facteur à importer (une feuille
      par facteur dans les fichiers d'AQR)

    Returns :
    - Un DataFrame contenant un facteur pour de multiples dates / Zones Géographiques
    """
    ext = os.path.splitext(file_path)[1].lower()
    try:
      if (ext == ".xlsx") or (ext == ".xls"):
        df_factors_import_temp = pd.read_excel(file_path, sheet_name=factor)
        junk_rows = self._header_row(df_factors_import_temp)
        return pd.read_excel(file_path, skiprows=junk_rows, sheet_name=factor)
      else:
        raise ValueError("Unsupported file format. Use, .xlsx, or .xls.")
    except Exception:
      raise DataImportError(AqrLoader, '_load_file', file_path)

  def load_aqr_factor(self, file_path:str, inv_universe: str):
    """
    Méthode permettant de récupérer, pour une zone géographique donnée, toutes les
    séries de facteurs retraitées. Cette méthode effectue les imports pour une seule périodicité.

    Parameters :
    - file_path : path du fichier contenant les facteur d'AQR
    - inv_universe : zone géographique pour laquelle on souhaite récupérer les facteurs

    Returns :
    - dataframe aqr_data rempli
    """
    df_aqr_factor = pd.DataFrame()
    # 5 facteurs à importer
    factors_list = ['MKT', 'SMB', 'HML FF', 'HML Devil', 'UMD']
    try:
      # Boucle sur chaque facteur pour effectuer des imports successifs
      for factor in factors_list:
        df_factor_import = self._load_file(file_path, factor)
        cols = df_aqr_factor.columns
        # Récupération de la colonne Date une seule fois car chaque série
        # a les mêmes dates
        if 'Date' not in cols:
          df_aqr_factor['Date'] = df_factor_import['DATE']
        # Récupération de la série associée à l'univers d'investissement renseigné
        df_aqr_factor[factor] = df_factor_import[inv_universe]

      # nettoyage des données
      df_aqr_factor = df_aqr_factor.dropna()
      df_aqr_factor['Date'] = self._date_converter(df_aqr_factor)
      df_aqr_factor = self._float_converter(df_aqr_factor)
      df_aqr_factor = df_aqr_factor.sort_values('Date', ascending=True)
      return df_aqr_factor

    except Exception:
      raise DataImportError(AqrLoader, 'load_aqr_factor', file_path, inv_universe)

  def load_rf(self, file_path):
    """
    Méthode permettant d'importer la série de taux sans risque.

    Parameters :
    - file_path : chemin d'accès au fichier d'AQR

    Returns :
    - un DataFrame contenant la série temporelle de taux sans risque retraitée.
    """
    try:
      df_rf = self._load_file(file_path, factor='RF')
      df_rf = df_rf.dropna()
      df_rf.columns = ['Date', 'RF']
      df_rf['Date'] = self._date_converter(df_rf)
      df_rf = self._float_converter(df_rf)
      df_rf = df_rf.sort_values('Date', ascending=True)
      return df_rf
    except Exception:
      raise DataImportError(AqrLoader, 'load_rf', file_path)