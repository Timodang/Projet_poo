import streamlit as st
import pandas as pd
import tempfile
import os
import sys
import logging
from pathlib import Path
import matplotlib.pyplot as plt

# Configuration logging
logging.basicConfig(
  level=logging.INFO,
  format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Path corrections
BASE_DIR = Path(__file__).resolve().parent.parent.parent
DEFAULT_DATA_DIR = os.path.join(BASE_DIR, 'src', 'data', 'fund_analysis')
DEFAULT_AQR_FILES = {
  'Daily': os.path.join(DEFAULT_DATA_DIR, 'Betting Against Beta Equity Factors Daily.xlsx'),
  'Monthly': os.path.join(DEFAULT_DATA_DIR, 'Betting Against Beta Equity Factors Monthly.xlsx')
}
DEFAULT_BENCHMARK_FILE = os.path.join(DEFAULT_DATA_DIR, 'S&P 500 tracker.csv')

# Ajout du path pour import
sys.path.append(str(BASE_DIR))

from src.app.data_loader import NavLoader, AqrLoader
from src.app.portfolio import Portfolio
from src.app.visualization import Visualization

# Configuration Streamlit
st.set_page_config(
  page_title="Portfolio Analysis Framework",
  layout="wide",
  initial_sidebar_state="expanded"
)


def save_uploaded_file(uploaded_file):
  try:
    if uploaded_file is not None:
      with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded_file.name)[1]) as tmp:
        tmp.write(uploaded_file.getvalue())
        logger.info(f"File saved successfully to {tmp.name}")
        return tmp.name
  except Exception as e:
    logger.error(f"Error saving file: {str(e)}", exc_info=True)
    raise e


def load_fund_data(uploaded_file, nav_loader, fund_number):
  try:
    if uploaded_file is not None:
      temp_path = save_uploaded_file(uploaded_file)
      fund_data = nav_loader.load_nav_data(temp_path)
      logger.info(f"Successfully loaded data for fund {fund_number}")
      return fund_data, temp_path
  except Exception as e:
    logger.error(f"Error loading fund {fund_number}: {str(e)}", exc_info=True)
    raise e
  return None, None


def highlight_extremes(row):
  if not isinstance(row.name, str):
    return [''] * len(row)
  max_value = row.max()
  min_value = row.min()
  colors = [''] * len(row)
  for i, value in enumerate(row):
    if value == max_value:
      colors[i] = 'color: red'
    elif value == min_value:
      colors[i] = 'color: green'
  return colors


def main():
  try:
    if 'analysis_complete' not in st.session_state:
      st.session_state.analysis_complete = False
    if 'analysis_data' not in st.session_state:
      st.session_state.analysis_data = None

    st.title("Portfolio Analysis Framework")

    st.warning("""⚠️ Information importante sur les temps de chargement:
            - L'importation des fichiers AQR peut prendre plusieurs minutes
            - Le traitement des fichiers volumineux nécessite plus de temps
            - Ne fermez pas la fenêtre pendant le chargement
            """)

    st.sidebar.header("Portfolio Configuration")
    num_funds = st.sidebar.number_input("Number of funds to analyze", min_value=1, max_value=10, value=3)
    frequency = st.sidebar.radio("Select data frequency", options=["Daily", "Monthly"], index=0)
    factor_universe = st.sidebar.selectbox("Select factor universe",
                                           options=["Global", "US", "Europe", "Japan"], index=0)

    nav_loader = NavLoader()
    portfolio = Portfolio()
    temp_paths = []

    st.header("1. Fund Selection")
    for i in range(num_funds):
      st.subheader(f"Fund {i + 1}")
      uploaded_file = st.file_uploader(f"Select file for fund {i + 1}",
                                       type=["csv", "xlsx", "xls"], key=f"fund_{i}")

      if uploaded_file is not None:
        try:
          with st.spinner(f"Loading fund {i + 1}..."):
            fund_data, temp_path = load_fund_data(uploaded_file, nav_loader, i + 1)
            if fund_data is not None:
              portfolio.add_fund(f"fund {i + 1}", fund_data)
              temp_paths.append(temp_path)
              st.success("NAV data loaded successfully")
              st.dataframe(fund_data.head())
        except Exception as e:
          st.error(f"Error loading fund {i + 1}: {str(e)}")

    list_fund = []
    for name, fund in portfolio.funds:
      list_fund.append(fund)

    st.header("2. Benchmark and Factor Selection")
    col1, col2 = st.columns(2)

    benchmark_data = None
    with col1:
      st.subheader("Benchmark")
      benchmark_load_method = st.radio("Choose how to load benchmark:",
                                       ["Use default S&P 500", "Upload custom benchmark"])

      if benchmark_load_method == "Use default S&P 500":
        try:
          if os.path.exists(DEFAULT_BENCHMARK_FILE):
            with st.spinner("Loading default S&P 500 benchmark..."):
              benchmark_data = nav_loader.load_nav_data(DEFAULT_BENCHMARK_FILE)
              st.success("✅ Default benchmark loaded successfully")
          else:
            st.error("Default S&P 500 file not found")
            st.info("Please upload a custom benchmark instead")
        except Exception as e:
          st.error(f"Error loading default benchmark: {str(e)}")
      else:
        benchmark_file = st.file_uploader("Select custom benchmark file",
                                          type=["csv", "xlsx", "xls"], key="custom_benchmark")
        if benchmark_file is not None:
          try:
            temp_path = save_uploaded_file(benchmark_file)
            benchmark_data = nav_loader.load_nav_data(temp_path)
            temp_paths.append(temp_path)
            st.success("Custom benchmark loaded successfully")
            st.dataframe(benchmark_data.head())
          except Exception as e:
            st.error(f"Error loading custom benchmark: {str(e)}")

    with col2:
      st.subheader("AQR Factors")
      st.write(f"Current frequency: {frequency}")

      aqr_load_method = st.radio("Choose how to load AQR factors:",
                                 ["Use default file", "Upload custom file"])

      if aqr_load_method == "Use default file":
        try:
          default_file = DEFAULT_AQR_FILES[frequency]
          if os.path.exists(default_file):
            with st.spinner("Loading default AQR factors..."):
              aqr_loader = AqrLoader()
              paths = [DEFAULT_AQR_FILES['Daily'], DEFAULT_AQR_FILES['Monthly']]
              aqr_data, rf_data = aqr_loader.fill_factors(paths, factor_universe)
              st.session_state.aqr_factors = aqr_data[frequency]
              st.session_state.rf = rf_data[frequency]
              st.success("✅ Default AQR factors loaded successfully")
          else:
            st.error(f"Default {frequency} file not found")
            st.info("Please upload a custom file instead")
        except Exception as e:
          st.error(f"Error loading default AQR factors: {str(e)}")
      else:
        st.info("Please upload both daily and monthly AQR files")
        uploaded_daily = st.file_uploader("Select Daily AQR Factor File",
                                          type=["xlsx"], key="daily_aqr")
        uploaded_monthly = st.file_uploader("Select Monthly AQR Factor File",
                                            type=["xlsx"], key="monthly_aqr")

        if uploaded_daily is not None and uploaded_monthly is not None:
          try:
            daily_path = save_uploaded_file(uploaded_daily)
            monthly_path = save_uploaded_file(uploaded_monthly)
            temp_paths.extend([daily_path, monthly_path])

            with st.spinner("Loading custom AQR factors..."):
              aqr_loader = AqrLoader()
              paths = [daily_path, monthly_path]
              aqr_data, rf_data = aqr_loader.fill_factors(paths, factor_universe)
              st.session_state.aqr_factors = aqr_data[frequency]
              st.session_state.rf = rf_data[frequency]
              st.success("✅ Custom AQR factors loaded successfully")
          except Exception as e:
            st.error(f"Error loading custom AQR factors: {str(e)}")

    if len(portfolio.funds) > 0 and benchmark_data is not None and 'aqr_factors' in st.session_state:
      if st.button("Run Analysis", help="Launch the complete portfolio analysis"):
        st.header("3. Analysis Results")

        with st.spinner("Running analysis... This may take a few moments."):
          try:
            if st.session_state.rf is None or st.session_state.aqr_factors is None:
              raise ValueError("AQR factors or risk-free rate data not loaded properly")

            # Création d'un dictionnaire pour AQR data
            aqr_dict = {
              'Daily': st.session_state.aqr_factors if frequency == "Daily" else None,
              'Monthly': st.session_state.aqr_factors if frequency == "Monthly" else None
            }

            # Création d'un dictionnaire pour RF data
            rf_dict = {
              'Daily': st.session_state.rf if frequency == "Daily" else None,
              'Monthly': st.session_state.rf if frequency == "Monthly" else None
            }

            # Stockage des résultats
            st.session_state.analysis_data = {
              'stats_report': portfolio.reporting(rf=rf_dict, benchmark=benchmark_data),
              'factor_analysis': portfolio.factorial_analysis(dict_aqr=aqr_dict),
              'nav_data': pd.DataFrame({name: fund['NAV'] for name, fund in portfolio.funds.items()}),
              'benchmark_nav': benchmark_data['NAV']
            }
            st.session_state.analysis_complete = True

          except Exception as e:
            logger.error("Error in analysis:", exc_info=True)
            st.error(f"Error in analysis: {str(e)}")
            return

    # Affichage des résultats par section
    if st.session_state.analysis_complete:
      data = st.session_state.analysis_data

      tab1, tab2, tab3, tab4 = st.tabs(
        ["Descriptive Statistics", "Factor Loadings", "Detailed Analysis", "Visualizations"])

      with tab1:
        st.subheader("Descriptive Statistics")
        st.dataframe(
          data['stats_report'].style
          .format("{:.6f}")
          .apply(highlight_extremes, axis=1)
        )

      with tab2:
        st.subheader("Factor Loadings")
        factor_loadings = data['factor_analysis']["factor loadings"]
        st.dataframe(
          factor_loadings.style
          .format("{:.6f}")
          .apply(highlight_extremes, axis=1)
        )

      with tab3:
        st.subheader("Regression Summaries")
        summaries = data['factor_analysis']["summary"]
        for i, fund_summary in enumerate(summaries):
          with st.expander(f"Regression Summary - Fund {i + 1}"):
            st.text(str(fund_summary))

      with tab4:
        st.subheader("Visualizations")
        viz = Visualization()
        plt.style.use('seaborn-v0_8-darkgrid')

        col1, col2 = st.columns(2)
        with col1:
          st.subheader("Métriques de Risque")
          fig_risk = viz.plot_risk_metrics(data['stats_report'])
          st.pyplot(fig_risk)

        st.subheader("Heatmap des Charges Factorielles")
        try:
          fig_heatmap = viz.plot_factor_heatmap(factor_loadings)
          st.pyplot(fig_heatmap)
        except Exception as e:
          logger.warning(f"Could not generate heatmap: {str(e)}")
          st.warning("Impossible de générer la heatmap")

        with col2:
          st.subheader("Performance Cumulée")
          fig_perf = viz.plot_performance(data['nav_data'])
          st.pyplot(fig_perf)
  finally:
    # Nettoyage des ficheirs temporaires
    for temp_path in temp_paths:
      try:
        if os.path.exists(temp_path):
          os.unlink(temp_path)
          logger.debug(f"Cleaned up temporary file: {temp_path}")
      except Exception as e:
        logger.error(f"Error cleaning up {temp_path}: {str(e)}")

  def display_visualizations(data, viz):
    """Fonction pour afficher les visualisations avec gestion des figures"""

    # Performance
    fig_perf = viz.plot_performance(list_fund)
    if fig_perf is not None:
      st.subheader("Performance Cumulée")
      st.pyplot(fig_perf)

    # Métriques de risque
    fig_risk = viz.plot_risk_metrics(data['stats_report'])
    if fig_risk is not None:
      st.subheader("Métriques de Risque")
      st.pyplot(fig_risk)

    # Heatmap factorielle
    try:
      st.subheader("Heatmap des Charges Factorielles")
      fig_heatmap = viz.plot_factor_heatmap(data['factor_loadings'])
      if fig_heatmap is not None:
        st.pyplot(fig_heatmap)
    except Exception as e:
      st.warning("Impossible de générer la heatmap")



if __name__ == "__main__":
  main()
