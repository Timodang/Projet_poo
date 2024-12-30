import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import pandas as pd
import matplotlib.dates as mdates


class Visualization:
    def _standardize_data(self, data):
        """
        Standardise les données sans modifier la structure originale.
        - Convertit l'index en format DatetimeIndex si nécessaire.
        - Trie les données par date pour garantir une cohérence temporelle.
        """
        df = data.copy()

        # Vérifie si l'index est déjà de type datetime, sinon tente une conversion
        if not isinstance(df.index, pd.DatetimeIndex):
            # Cherche une colonne contenant des dates, par exemple 'date' ou 'valorisation'
            date_cols = [col for col in df.columns if 'date' in col.lower() or 'valorisation' in col.lower()]
            if date_cols:
                df.set_index(date_cols[0], inplace=True)
            df.index = pd.to_datetime(df.index)  # Conversion explicite des dates

        # Trie les données pour garantir un ordre chronologique
        df = df.sort_index()

        # Détermine la plage de dates dans les données
        min_date = df.index.min()
        max_date = df.index.max()

        # Filtre les données pour conserver uniquement les dates valides
        df = df.loc[min_date:max_date]

        return df

    def _get_common_date_range(self, *dataframes):
        """
        Trouve la plage de dates commune entre plusieurs DataFrames ou Series.
        - Extrait les dates minimum et maximum de chaque DataFrame.
        - Retourne l'intervalle partagé entre tous.
        """
        min_dates = []
        max_dates = []

        for df in dataframes:
            if isinstance(df, pd.Series):
                df = df.to_frame()  # Convertit une Series en DataFrame pour homogénéité
            df_dates = pd.to_datetime(
                df.index if isinstance(df.index, pd.DatetimeIndex)
                else df['Date'] if 'Date' in df.columns
                else df[df.columns[0]]
            )
            min_dates.append(df_dates.min())  # Date minimum pour chaque DataFrame
            max_dates.append(df_dates.max())  # Date maximum pour chaque DataFrame

        # La plage commune est le maximum des dates minimums et le minimum des dates maximums
        return max(min_dates), min(max_dates)

    def plot_performance(self, nav_series):
        """
        Trace la performance cumulée des fonds, avec une harmonisation des plages de dates.
        """
        data = nav_series.copy()

        # Vérifie et convertit l'index en DatetimeIndex
        if 'Date' in data.columns:
            data.set_index('Date', inplace=True)
        data.index = pd.to_datetime(data.index)

        # Restreint les données à la plage commune
        min_date, max_date = self._get_common_date_range(data)
        data = data.loc[min_date:max_date]

        # Trie l'index après le filtrage
        data = data.sort_index()

        fig, ax = plt.subplots(figsize=(12, 6))

        # Parcourt chaque fonds pour calculer et tracer la performance cumulée
        for col in data.columns:
            series = data[col].dropna()  # Supprime les valeurs manquantes
            if not series.empty:
                returns = series.pct_change().fillna(0)  # Rendements quotidiens
                cumul_returns = (1 + returns).cumprod() - 1  # Rendements cumulés
                ax.plot(series.index, cumul_returns, label=col)

        # Formatte l'axe des dates pour une meilleure lisibilité
        locator = mdates.AutoDateLocator()
        ax.xaxis.set_major_locator(locator)
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))

        ax.set_title("Performance Cumulée")
        ax.set_xlabel("Date")
        ax.set_ylabel("Performance (%)")
        ax.grid(True)
        ax.legend(title="Fonds", bbox_to_anchor=(1.05, 1), loc='upper left')

        # Rotation des étiquettes des dates pour éviter le chevauchement
        plt.xticks(rotation=45)
        plt.tight_layout()
        return fig

    def plot_rolling_correlation(self, nav_data, window=60):
        """
        Trace les corrélations glissantes entre les fonds sur une fenêtre donnée.
        """
        if len(nav_data.columns) < 2:
            return None  # Impossible de calculer les corrélations avec moins de 2 fonds

        data = self._standardize_data(nav_data)
        min_date, max_date = self._get_common_date_range(data)
        data = data.loc[min_date:max_date]

        # Calcule les rendements quotidiens
        returns = data.pct_change().fillna(0)

        fig, ax = plt.subplots(figsize=(12, 6))

        # Boucle sur chaque paire de fonds pour tracer leur corrélation
        for i in range(len(returns.columns)):
            for j in range(i + 1, len(returns.columns)):
                col_i, col_j = returns.columns[i], returns.columns[j]
                corr = returns[col_i].rolling(window).corr(returns[col_j])  # Corrélation glissante
                ax.plot(corr.index, corr.values, label=f'{col_i} vs {col_j}')

        # Formatage des dates et des axes
        locator = mdates.AutoDateLocator()
        ax.xaxis.set_major_locator(locator)
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))

        ax.set_title(f"Corrélations Glissantes (fenêtre: {window} jours)")
        ax.set_xlabel("Date")
        ax.set_ylabel("Corrélation")
        ax.grid(True)
        ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        ax.set_ylim(-1, 1)  # Corrélations entre -1 et 1

        plt.xticks(rotation=45)
        plt.tight_layout()
        return fig
