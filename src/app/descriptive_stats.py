import numpy as np
import pandas as pd

class DescriptiveStatistics2:
    """
    Classe utilisée pour calculer des statistiques descriptives
    sur les performances et les risques d'un fonds.

    Attributes :
    -----------
    nav_series : pd.DataFrame ou pd.Series
        Série temporelle de NAV (valeurs liquidatives) d'un fonds,
        indexée par date.

    rf : pd.DataFrame ou pd.Series
        Série temporelle du taux sans risque, aligné sur la
        même fréquence (idéalement mêmes dates) que le fonds.

    periodicity : int
        Facteur d'annualisation (ex : 252 pour du daily, 12 pour du mensuel, etc.).

    Methods :
    ---------
    calculate_daily_returns :
        Calcule les rendements quotidiens (méthode simple).

    calculate_daily_excess_returns:
        Calcule les rendements excédentaires (rendements - rf).

    calculate_performance :
        Calcule la performance totale et annualisée du fonds.

    calculate_volatility :
        Calcule la volatilité annualisée.

    calculate_excess_returns :
        Calcule la performance excédentaire totale et annualisée.

    calculate_sharpe_ratio :
        Calcule le ratio de Sharpe.

    calculate_downside_volatility :
        Calcule la volatilité à la baisse (downside volatility) annualisée.

    calculate_sortino_ratio :
        Calcule le ratio de Sortino.

    calculate_alpha_beta :
        Calcule l'alpha et le beta par rapport à un benchmark.

    calculate_tracking_error:
        Calcule la tracking error par rapport à un benchmark.

    calculate_maximum_drawdown :
        Calcule le maximum drawdown (MDD).

    calculate_beta_up_and_down :
        Calcule le beta up et le beta down (régime haussier / baissier du benchmark).

    reporting_stats :
        Regroupe toutes les statistiques et les retourne sous forme de liste ou DataFrame.
    """

    def __init__(self, nav_series: pd.DataFrame, rf: pd.DataFrame, periodicity: int):
        """
        Initialise la classe avec une série ou un DataFrame de valeurs liquidatives (NAV).
        :param nav_series: Série ou DataFrame avec les NAV indexées par date.
        :param rf: Série ou DataFrame avec les taux sans risque indexés par date.
        :param periodicity: Facteur d'annualisation (ex: 252 pour un dataset quotidien).
        """
        self.nav_series = nav_series
        self.rf = rf
        self.annualization = periodicity

    @property
    def calculate_daily_returns(self) -> pd.Series:
        """
        Calcule les rendements quotidiens à partir des valeurs NAV.
        :return: Série des rendements quotidiens, alignée par date.
        """
        daily_returns = self.nav_series.pct_change().dropna()
        return daily_returns

    @property
    def calculate_daily_excess_returns(self) -> pd.Series:
        """
        Calcule les rendements excédentaires (rendements - taux sans risque).
        :return: Série des rendements excédentaires alignée par date.
        """
        # On aligne les deux séries (rendements et rf) pour éviter tout décalage d'index
        daily_ret = self.calculate_daily_returns
        aligned_ret, aligned_rf = daily_ret.align(self.rf, join='inner')
        excess_ret = (aligned_ret - aligned_rf).dropna()
        return excess_ret

    def calculate_performance(self) -> dict:
        """
        Calcule la performance totale et annualisée du fonds.
        :return: Dictionnaire contenant la performance totale et annualisée.
        """
        # On s’assure que la série nav_series est bien ordonnée et sans NaN aux extrémités
        nav = self.nav_series.dropna()
        total_return = (nav.iloc[-1] / nav.iloc[0]) - 1

        # Nombre de points observés (ex : nombre de jours boursiers) :
        n_obs = len(nav)

        # Annualisation
        annualized_return = (1 + total_return) ** (self.annualization / n_obs) - 1

        return {"total_return": total_return, "annualized_return": annualized_return}

    def calculate_volatility(self) -> float:
        """
        Calcule la volatilité (écart-type) annualisée du fonds.
        :return: Volatilité annualisée.
        """
        daily_volatility = self.calculate_daily_returns.std()
        annualized_volatility = daily_volatility * np.sqrt(self.annualization)
        return annualized_volatility

    def calculate_excess_returns(self) -> dict:
        """
        Calcule :
        - Le rendement excédentaire total
        - Le rendement excédentaire annualisé
        :return: Dictionnaire avec total_excess_returns et annualized_excess_returns
        """
        excess_returns = self.calculate_daily_excess_returns.dropna()
        if excess_returns.empty:
            return {"total_excess_returns": np.nan, "annualized_excess_returns": np.nan}

        # Calcul cumulatif vectorisé
        total_excess_return = (1 + excess_returns).prod() - 1

        # Annualisation
        n_obs = len(excess_returns)
        annualized_excess = (1 + total_excess_return) ** (self.annualization / n_obs) - 1

        return {
            "total_excess_returns": total_excess_return,
            "annualized_excess_returns": annualized_excess
        }

    def calculate_sharpe_ratio(self) -> float:
        """
        Calcule le ratio de Sharpe = Rendement excédentaire annualisé / Volatilité annualisée.
        :return: Ratio de Sharpe.
        """
        ann_excess = self.calculate_excess_returns()['annualized_excess_returns']
        ann_vol = self.calculate_volatility()

        if ann_vol == 0:
            return np.inf if ann_excess > 0 else -np.inf

        return ann_excess / ann_vol

    def calculate_downside_volatility(self) -> float:
        """
        Calcule la volatilité à la baisse (downside volatility) annualisée :
        on considère uniquement les périodes où le fonds < rf.
        :return: downside volatility annualisée.
        """
        # Aligner daily_returns et rf
        daily_ret, rf_aligned = self.calculate_daily_returns.align(self.rf, join='inner')

        # On calcule le "downside" uniquement quand (fund return - rf) < 0
        diff = daily_ret - rf_aligned
        negative_diff = diff[diff < 0]

        if negative_diff.empty:
            # Pas de rendements négatifs par rapport au rf => downside vol = 0
            return 0.0

        # Écart-type * sqrt(facteur annualisation)
        downside_vol = negative_diff.std() * np.sqrt(self.annualization)
        return downside_vol

    def calculate_sortino_ratio(self) -> float:
        """
        Calcule le ratio de Sortino = Rendement excédentaire annualisé / Downside volatility.
        :return: Ratio de Sortino (float).
        """
        ann_excess = self.calculate_excess_returns()['annualized_excess_returns']
        downside_vol = self.calculate_downside_volatility()

        if downside_vol == 0:
            # Pas de downside => Sortino infini si excès>0
            return np.inf if ann_excess > 0 else -np.inf

        return ann_excess / downside_vol

    def calculate_maximum_drawdown(self) -> float:
        """
        Calcule le maximum drawdown (perte maximale cumulée).
        :return: Valeur (négative) du plus grand drawdown observé.
        """
        daily_ret = self.calculate_daily_returns
        # Cumul de (1 + daily_returns)
        cum_returns = (1 + daily_ret).cumprod()

        # Point haut (peak) historique
        rolling_peak = cum_returns.cummax()

        # Drawdown = (valeur cumulée - peak) / peak
        drawdown = (cum_returns - rolling_peak) / rolling_peak
        max_dd = drawdown.min()  # valeur la plus négative
        return max_dd

    def calculate_tracking_error(self, benchmark_returns: pd.Series) -> float:
        """
        Calcule la tracking error par rapport à un benchmark.
        :param benchmark_returns: Série des rendements quotidiens du benchmark (mêmes dates).
        :return: Tracking error annualisée.
        """
        # Aligner
        fund_ret, bench_ret = self.calculate_daily_returns.align(benchmark_returns, join='inner')
        if fund_ret.empty:
            return np.nan

        diff = fund_ret - bench_ret
        te = diff.std() * np.sqrt(self.annualization)
        return te

    def calculate_alpha_beta(self, benchmark_returns: pd.Series) -> dict:
        """
        Calcule l'alpha et le beta par rapport à un benchmark via la régression
        sur les rendements excédentaires.
        :param benchmark_returns: Série des rendements quotidiens du benchmark.
        :return: Dictionnaire {"alpha": alpha, "beta": beta}.
        """
        # Rdt excédentaires du fonds
        fund_excess = self.calculate_daily_excess_returns

        # Rdt excédentaires du benchmark => on aligne
        bench_excess = (benchmark_returns - self.rf).dropna()
        fund_excess, bench_excess = fund_excess.align(bench_excess, join='inner')

        if fund_excess.empty:
            return {"alpha": np.nan, "beta": np.nan}

        # Calcul cov et var
        cov = np.cov(fund_excess, bench_excess)[0, 1]
        var_bench = np.var(bench_excess)
        if var_bench == 0:
            return {"alpha": np.nan, "beta": np.nan}

        beta = cov / var_bench

        # alpha annualisé = (moyenne fund_excess - beta * moyenne bench_excess) * annualization
        alpha = (fund_excess.mean() - beta * bench_excess.mean()) * self.annualization

        return {"alpha": alpha, "beta": beta}

    def calculate_beta_up_and_down(self, benchmark_returns: pd.Series) -> dict:
        """
        Calcule le beta up et le beta down par rapport à un benchmark,
        en fonction du signe (au-dessus / au-dessous de la moyenne du benchmark).
        :param benchmark_returns: Série des rendements quotidiens du benchmark.
        :return: Dictionnaire {"beta up": ..., "beta down": ...}.
        """
        # Aligner
        fund_excess = self.calculate_daily_excess_returns
        bench_excess = (benchmark_returns - self.rf).dropna()

        fund_excess, bench_excess = fund_excess.align(bench_excess, join='inner')

        if bench_excess.empty:
            return {"beta up": np.nan, "beta down": np.nan}

        mean_bench = bench_excess.mean()

        # Masque up / down
        mask_up = bench_excess >= mean_bench
        mask_down = ~mask_up

        # Sous-séries
        fund_up = fund_excess[mask_up]
        bench_up = bench_excess[mask_up]

        fund_down = fund_excess[mask_down]
        bench_down = bench_excess[mask_down]

        # Beta up
        if len(bench_up) > 1 and np.var(bench_up) != 0:
            cov_up = np.cov(fund_up, bench_up)[0, 1]
            beta_up = cov_up / np.var(bench_up)
        else:
            beta_up = np.nan

        # Beta down
        if len(bench_down) > 1 and np.var(bench_down) != 0:
            cov_down = np.cov(fund_down, bench_down)[0, 1]
            beta_down = cov_down / np.var(bench_down)
        else:
            beta_down = np.nan

        return {"beta up": beta_up, "beta down": beta_down}

    def reporting_stats(self, benchmark_returns: pd.Series):
        """
        Retourne la liste de statistiques calculées pour un fonds.
        :param benchmark_returns: série des rendements du benchmark.
        :return: Liste des stats (ou DataFrame).
        """
        perf = self.calculate_performance()
        excess_perf = self.calculate_excess_returns()
        market_model = self.calculate_alpha_beta(benchmark_returns)
        beta_market_regime = self.calculate_beta_up_and_down(benchmark_returns)

        stats_list = [
            perf["annualized_return"],
            perf["total_return"],
            self.calculate_volatility(),
            self.calculate_sharpe_ratio(),
            self.calculate_sortino_ratio(),
            self.calculate_downside_volatility(),
            excess_perf['total_excess_returns'],
            excess_perf['annualized_excess_returns'],
            market_model['beta'],
            self.calculate_tracking_error(benchmark_returns),
            market_model['alpha'],
            beta_market_regime['beta up'],
            beta_market_regime['beta down'],
            self.calculate_maximum_drawdown()
        ]

        return stats_list
