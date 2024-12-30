import pandas as pd
from pandas import to_datetime

class DataFormating:
    """
    Classe permettant de nettoyer et d'harmoniser les données importées
    depuis les fichiers contenant les NAV des fonds et les facteurs AQR.

    Methodes :
    ----------

    - _header_row : Méthode permettant d'identifier la  ligne contenant les entêtes pour
    l'import des données.
    - _date_converter : Méthode permettant de transformer les colonnes date de chaque série
    en datetime lorsqu'elles sont renseignées en tant que chaîne de caractères.
    - _float_converter : Méthode permettant de transformer les séries de prix / facteurs en nombre
    lorsque ces dernières sont renseignées en tant que chaine de caractères.
    """

    @staticmethod
    def _header_row(df_imported : pd.DataFrame):
        """
        Cette méthode cherche à identifier un élément correspondant à l'entête de la colonne
        avec les dates afin de déterminer à partir de quelle ligne les fichiers doivent être
        importés dans le cas où il y a des lignes vides / non pertinentes au début de l'excel / csv.

        Plusieurs valeurs d'entête sont testées. Si aucune n'est trouvée, la méthode renvoie 0.
        Dans ce cas, si la première ligne du fichier ne correspond pas à l'entête, une erreur sera renvoyée
        car les imports ne fonctionneront pas.

        Parameters :
        - df_imported : DataFrame contenant des données importées à partir d'un fichier excel/csv
        dont on cherche à identifier les entêtes.

        Returns :
        Le numero de la ligne suivant les entêtes afin de déterminer à partir de quelle ligne
        il faut importer les données.
        """
        for i, row in df_imported.iterrows():
            if ('Date' in row.values) or ("DATE" in row.values) or ('Date de valorisation' in row.values):
                return i + 1
        return 0

    @staticmethod
    def _date_converter(df_imported: pd.DataFrame):
        """
        Méthode permettant de convertir des dates
        renseignées au format string dans le fichier importé en datetime.

        La tentative de conversion générique permet de tenir compte du cas
        où un format date trop spécifique est utilisée dans le fichier (ex : fonds AQR).

        Parameters :
        - df_imported : DataFrame importé avec une colonne 'Date' qui peut
        être renseignée au format datetime ou string selon le fichier d'entrée.

        Returns :
        Le DataFrame d'entrée avec la colonne de Date convertie en datetime
        si elle était renseignée en string.
        """
        try:
            # Tentative de conversion générique
            result = to_datetime(df_imported['Date'])
            return result
        except ValueError:
            # Test de plusieurs formats courants afin d'identifier celui
            # correspondant à la chaine de caractère renseignée dans les fichier
            for fmt in ('%Y-%m-%d', '%d.%m.%Y', '%d/%m/%Y', '%m/%d/%Y'):
                try:
                    result = to_datetime(df_imported['Date'], format=fmt)
                    return result
                except ValueError:
                    pass

    @staticmethod
    def _float_converter(df_imported:pd.DataFrame):
        """
        Méthode permettant de convertir la série de NAV d'un fonds en float dans le cas
        où elle est renseignée en tant que chaîne de caractères (= object de pandas)

        Parameters :
        - df_imported : DataFrame importéc ontenant des valeurs renseignées en tant qu'object
        correspondant à la série temporelle de la NAV du fonds
        que l'utilisateur souhaite ajouter au portefeuille

        Returns :
        - le dataframe correspondant avec la série NAV convertie en float.
        """
        for column_name, column_data in df_imported.items():
            if column_name != "Date":
                # dans le cas où les NAV sont renseignées avec des nombres
                # au format européen, une transformation est effectuée pour
                # pouvoir les convertir (changement de séparateur)
                if df_imported[column_name].dtype == 'object':
                    df_imported[column_name] = [val.replace(',', '.') for val in
                                                df_imported[column_name]]
                    df_imported[column_name] = df_imported[column_name].astype(float)

        return df_imported
