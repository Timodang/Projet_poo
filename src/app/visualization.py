import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import pandas as pd
import matplotlib.dates as mdates


class Visualization:
    def _standardize_data(self, data):
        """
        Standardise les données sans modifier la structure originale
        """
        df = data.copy()

        # Si l'index n'est pas déjà datetime, essayer de le convertir
        if not isinstance(df.index, pd.DatetimeIndex):
            # Chercher une colonne de date si elle existe
            date_cols = [col for col in df.columns if 'date' in col.lower() or 'valorisation' in col.lower()]
            if date_cols:
                df.set_index(date_cols[0], inplace=True)
            df.index = pd.to_datetime(df.index)

        # S'assurer que l'index est trié
        df = df.sort_index()

        # Déterminer la plage de dates commune
        min_date = df.index.min()
        max_date = df.index.max()

        # Filtrer les données pour la plage commune
        df = df.loc[min_date:max_date]

        return df

    def _get_common_date_range(self, *dataframes):
        """
        Trouve la plage de dates commune à tous les dataframes
        """
        min_dates = []
        max_dates = []

        for df in dataframes:
            if isinstance(df, pd.Series):
                df = df.to_frame()
            df_dates = pd.to_datetime(df.index if isinstance(df.index, pd.DatetimeIndex)
                                    else df['Date'] if 'Date' in df.columns
                                    else df[df.columns[0]])
            min_dates.append(df_dates.min())
            max_dates.append(df_dates.max())

        return max(min_dates), min(max_dates)

    def plot_correlation_matrix(self, returns):
        """
        Crée une heatmap de la matrice de corrélation des rendements
        """
        corr_matrix = returns.corr()

        fig, ax = plt.subplots(figsize=(10, 8))
        sns.heatmap(corr_matrix,
                   annot=True,
                   cmap='RdYlBu_r',
                   center=0,
                   vmin=-1,
                   vmax=1,
                   fmt='.2f',
                   ax=ax)
        ax.set_title("Matrice de Corrélation des Rendements")
        plt.tight_layout()

        return fig

    def plot_risk_metrics(self, risk_metrics):
        """
        Visualise les métriques de risque des fonds sous forme de barres
        """
        fig, ax = plt.subplots(figsize=(12, 6))
        risk_metrics.plot(kind="bar", ax=ax)
        ax.set_title("Métriques de Risque")
        ax.set_xlabel("Fonds")
        ax.set_ylabel("Valeur")
        ax.grid(axis="y")
        ax.legend(title="Métrique", bbox_to_anchor=(1.05, 1), loc='upper left')
        plt.xticks(rotation=45)
        plt.tight_layout()
        return fig

    def plot_factor_heatmap(self, factor_loadings):
        """
        Crée une heatmap des charges factorielles
        """
        fig, ax = plt.subplots(figsize=(10, 8))
        sns.heatmap(factor_loadings,
                    annot=True,
                    cmap='RdYlBu_r',
                    center=0,
                    fmt='.2f',
                    ax=ax)
        ax.set_title("Heatmap des Charges Factorielles")
        plt.tight_layout()
        return fig

    def plot_performance(self, nav_series: list):
      """
      Trace la performance cumulée des fonds
      """
      fig, ax = plt.subplots(nrows=len(nav_series), ncols=1, figsize=(12, 6))
      cpt = 0
      for fund in nav_series:
        series = fund['NAV']
        if not series.empty:
          returns = series.pct_change().fillna(0)
          cumul_returns = (1 + returns).cumprod() - 1
          ax[cpt].plot(fund['Date'], cumul_returns * 100)

          ax[cpt].set_title("Performance Cumulée pour le fonds " + str(cpt + 1))
          ax[cpt].set_xlabel("Date")
          ax[cpt].set_ylabel("Performance (en %)")
          ax[cpt].grid(True)
          cpt += 1
      plt.xticks(rotation=45)
      plt.tight_layout()
      return fig
