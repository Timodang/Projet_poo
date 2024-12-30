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

    return df

  def plot_performance(self, nav_series):
    """
    Trace la performance cumulée des fonds
    """
    data = self._standardize_data(nav_series)

    fig, ax = plt.subplots(figsize=(12, 6))

    # Remplacer les valeurs infinies ou NaN par 0
    data = data.replace([np.inf, -np.inf], np.nan)
    data = data.fillna(method='ffill')

    # Calculer les rendements pour chaque fonds
    for col in data.columns:
      # Calculer les rendements en évitant les problèmes de division par zéro
      series = data[col]
      returns = series.pct_change()
      cumul_returns = (1 + returns).cumprod() - 1
      ax.plot(cumul_returns.index, cumul_returns.values, label=col)

    # Formater l'axe des dates
    locator = mdates.AutoDateLocator()
    ax.xaxis.set_major_locator(locator)
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))

    ax.set_title("Performance Cumulée")
    ax.set_xlabel("Date")
    ax.set_ylabel("Performance (%)")
    ax.grid(True)
    ax.legend(title="Fonds", bbox_to_anchor=(1.05, 1), loc='upper left')

    plt.xticks(rotation=45)
    plt.tight_layout()
    return fig

  def plot_rolling_correlation(self, nav_data, window=60):
    """
    Trace les corrélations glissantes entre les fonds
    """
    if len(nav_data.columns) < 2:
      return None

    data = self._standardize_data(nav_data)

    # Calculer les rendements
    returns = data.pct_change().fillna(0)

    fig, ax = plt.subplots(figsize=(12, 6))

    # Calculer et tracer les corrélations pour chaque paire de fonds
    for i in range(len(returns.columns)):
      for j in range(i + 1, len(returns.columns)):
        col_i, col_j = returns.columns[i], returns.columns[j]
        corr = returns[col_i].rolling(window).corr(returns[col_j])
        ax.plot(corr.index, corr.values, label=f'{col_i} vs {col_j}')

    # Formater l'axe des dates
    locator = mdates.AutoDateLocator()
    ax.xaxis.set_major_locator(locator)
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))

    ax.set_title(f"Corrélations Glissantes (fenêtre: {window} jours)")
    ax.set_xlabel("Date")
    ax.set_ylabel("Corrélation")
    ax.grid(True)
    ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    ax.set_ylim(-1, 1)

    plt.xticks(rotation=45)
    plt.tight_layout()
    return fig

  def plot_rolling_beta(self, nav_data, benchmark_data, window=60):
    """
    Trace le beta glissant des fonds par rapport au benchmark
    """
    # Standardiser les données des fonds
    data = self._standardize_data(nav_data)

    # Standardiser le benchmark
    if isinstance(benchmark_data, pd.Series):
      bench = pd.DataFrame(benchmark_data)
      bench = self._standardize_data(bench)
    else:
      bench = self._standardize_data(pd.DataFrame(benchmark_data))

    fig, ax = plt.subplots(figsize=(12, 6))

    # Calculer les rendements
    fund_returns = data.pct_change().fillna(0)
    bench_returns = bench.iloc[:, 0].pct_change().fillna(0)

    for fund in fund_returns.columns:
      # S'assurer que nous avons des dates communes
      common_dates = fund_returns.index.intersection(bench_returns.index)
      if len(common_dates) > window:
        fund_ret = fund_returns.loc[common_dates, fund]
        bench_ret = bench_returns.loc[common_dates]

        # Calculer le beta glissant
        rolling_cov = fund_ret.rolling(window).cov(bench_ret)
        rolling_var = bench_ret.rolling(window).var()
        rolling_beta = rolling_cov / rolling_var

        ax.plot(rolling_beta.index, rolling_beta.values, label=fund)

    # Formater l'axe des dates
    locator = mdates.AutoDateLocator()
    ax.xaxis.set_major_locator(locator)
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))

    ax.set_title(f"Beta Glissant (fenêtre: {window} jours)")
    ax.set_xlabel("Date")
    ax.set_ylabel("Beta")
    ax.grid(True)
    ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    ax.axhline(y=1, color='gray', linestyle='--', alpha=0.5)

    plt.xticks(rotation=45)
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
