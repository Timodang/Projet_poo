import streamlit as st
import pandas as pd
import tempfile
import os
import sys
import logging
from pathlib import Path
import matplotlib.pyplot as plt

# Configure logging
logging.basicConfig(
  level=logging.DEBUG,
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

# Add path for imports
sys.path.append(str(BASE_DIR))

from src.app.data_loader import NavLoader, AqrLoader
from src.app.portfolio import Portfolio
from src.app.visualization import Visualization

# Streamlit Configuration
st.set_page_config(
  page_title="Portfolio Analysis Framework",
  layout="wide",
  initial_sidebar_state="expanded"
)


def save_uploaded_file(uploaded_file):
  """Save uploaded file to a temporary location and return the path"""
  try:
    if uploaded_file is not None:
      logger.info(f"Attempting to save file: {uploaded_file.name}")
      logger.info(f"File size: {uploaded_file.size / (1024 * 1024):.2f} MB")

      with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded_file.name)[1]) as tmp:
        tmp.write(uploaded_file.getvalue())
        logger.info(f"File saved successfully to {tmp.name}")
        return tmp.name
  except Exception as e:
    logger.error(f"Error saving file: {str(e)}", exc_info=True)
    raise e


def load_fund_data(uploaded_file, nav_loader, fund_number):
  """Load fund data from uploaded file"""
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
  """Apply color highlighting to min/max values"""
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
    # Initialize session state for analysis results
    if 'analysis_complete' not in st.session_state:
      st.session_state.analysis_complete = False
    if 'analysis_data' not in st.session_state:
      st.session_state.analysis_data = None

    # Debug information
    if st.checkbox("Show Debug Info"):
      st.write("DEBUG - Paths:")
      st.write(f"Base Directory: {BASE_DIR}")
      st.write(f"Data Directory: {DEFAULT_DATA_DIR}")
      st.write(f"Daily AQR File Path: {DEFAULT_AQR_FILES['Daily']}")
      st.write(f"Monthly AQR File Path: {DEFAULT_AQR_FILES['Monthly']}")
      st.write(f"Default Benchmark File Path: {DEFAULT_BENCHMARK_FILE}")

    st.title("Portfolio Analysis Framework")

    # Important notice about loading times
    st.warning("""⚠️ Information importante sur les temps de chargement:
        - L'importation des fichiers AQR peut prendre plusieurs minutes selon leur taille
        - Le traitement des fichiers volumineux nécessite plus de temps
        - Ne fermez pas la fenêtre pendant le chargement
        """)

    # Sidebar configuration
    st.sidebar.header("Portfolio Configuration")

    num_funds = st.sidebar.number_input(
      "Number of funds to analyze",
      min_value=1,
      max_value=10,
      value=3
    )

    frequency = st.sidebar.radio(
      "Select data frequency",
      options=["Daily", "Monthly"],
      index=0
    )

    factor_universe = st.sidebar.selectbox(
      "Select factor universe",
      options=["Global", "US", "Europe", "Japan"],
      index=0
    )

    # Initialize loaders and portfolio
    nav_loader = NavLoader()
    portfolio = Portfolio()
    temp_paths = []

    # Fund Selection Section
    st.header("1. Fund Selection")

    for i in range(num_funds):
      st.subheader(f"Fund {i + 1}")
      uploaded_file = st.file_uploader(
        f"Select file for fund {i + 1}",
        type=["csv", "xlsx", "xls"],
        key=f"fund_{i}",
        help="Upload NAV data file (CSV, XLSX, or XLS format)"
      )

      if uploaded_file is not None:
        try:
          file_details = {
            "Filename": uploaded_file.name,
            "FileType": uploaded_file.type,
            "FileSize": f"{uploaded_file.size / (1024 * 1024):.2f} MB"
          }
          st.write("File Details:", file_details)

          with st.spinner(f"Loading fund {i + 1}... This may take a few moments."):
            fund_data, temp_path = load_fund_data(uploaded_file, nav_loader, i + 1)
            if fund_data is not None:
              portfolio.add_fund(f"fund {i + 1}", fund_data)
              temp_paths.append(temp_path)
              st.success("NAV data loaded successfully")
              st.dataframe(fund_data.head())
        except Exception as e:
          st.error(f"Error loading fund {i + 1}: {str(e)}")

    # Benchmark and Factor Selection Section
    st.header("2. Benchmark and Factor Selection")
    col1, col2 = st.columns(2)

    # Benchmark Section
    benchmark_data = None
    with col1:
      st.subheader("Benchmark")
      benchmark_load_method = st.radio(
        "Choose how to load benchmark:",
        ["Use default S&P 500", "Upload custom benchmark"],
        key="benchmark_method"
      )

      if benchmark_load_method == "Use default S&P 500":
        try:
          if not os.path.exists(DEFAULT_BENCHMARK_FILE):
            st.error("Default S&P 500 file not found")
            st.info("Please upload a custom benchmark instead")
          else:
            with st.spinner("Loading default S&P 500 benchmark..."):
              benchmark_data = nav_loader.load_nav_data(DEFAULT_BENCHMARK_FILE)
              st.write("Benchmark Preview:")
              st.dataframe(benchmark_data.head())
              st.success("✅ Default benchmark loaded successfully")
        except Exception as e:
          st.error(f"Error loading default benchmark: {str(e)}")
      else:
        benchmark_file = st.file_uploader(
          "Select custom benchmark file",
          type=["csv", "xlsx", "xls"],
          key="custom_benchmark",
          help="Upload custom benchmark data file"
        )

        if benchmark_file is not None:
          try:
            temp_path = save_uploaded_file(benchmark_file)
            benchmark_data = nav_loader.load_nav_data(temp_path)
            temp_paths.append(temp_path)
            st.success("Custom benchmark loaded successfully")
            st.dataframe(benchmark_data.head())
          except Exception as e:
            st.error(f"Error loading custom benchmark: {str(e)}")

    # AQR Factors Section
    with col2:
      st.subheader("AQR Factors")
      st.write(f"Current frequency: {frequency}")

      st.info("""ℹ️ Note sur l'importation des facteurs AQR:
            - Le chargement peut prendre plusieurs minutes
            - Les fichiers sont volumineux et nécessitent un temps de traitement important
            - Veuillez patienter pendant le chargement
            """)

      aqr_load_method = st.radio(
        "Choose how to load AQR factors:",
        ["Use default file", "Upload custom file"],
        key="aqr_method"
      )

      if aqr_load_method == "Use default file":
        try:
          default_file = DEFAULT_AQR_FILES[frequency]
          if not os.path.exists(default_file):
            st.error(f"Default {frequency} file not found")
            st.info("Please upload a custom file instead")
          else:
            with st.spinner(f"Loading default {frequency} AQR factors... This may take several minutes."):
              aqr_loader = AqrLoader()
              paths = [DEFAULT_AQR_FILES['Daily'], DEFAULT_AQR_FILES['Monthly']]
              aqr_data, rf_data = aqr_loader.fill_factors(paths, factor_universe)

              st.session_state.aqr_factors = aqr_data[frequency]
              st.session_state.rf = rf_data[frequency]

              st.write("AQR Factors Preview:")
              st.dataframe(st.session_state.aqr_factors.head())
              st.write("Risk-Free Rate Preview:")
              st.dataframe(st.session_state.rf.head())

              st.success("✅ Default AQR factors loaded successfully")
        except Exception as e:
          st.error(f"Error loading default AQR factors: {str(e)}")
      else:
        st.info("Please upload both daily and monthly AQR files")
        uploaded_daily = st.file_uploader(
          "Select Daily AQR Factor File",
          type=["xlsx"],
          key="daily_aqr",
          help="Upload daily AQR factors file"
        )

        uploaded_monthly = st.file_uploader(
          "Select Monthly AQR Factor File",
          type=["xlsx"],
          key="monthly_aqr",
          help="Upload monthly AQR factors file"
        )

        if uploaded_daily is not None and uploaded_monthly is not None:
          try:
            daily_path = save_uploaded_file(uploaded_daily)
            monthly_path = save_uploaded_file(uploaded_monthly)
            temp_paths.extend([daily_path, monthly_path])

            with st.spinner("Loading custom AQR factors... This may take several minutes."):
              aqr_loader = AqrLoader()
              paths = [daily_path, monthly_path]
              aqr_data, rf_data = aqr_loader.fill_factors(paths, factor_universe)

              st.session_state.aqr_factors = aqr_data[frequency]
              st.session_state.rf = rf_data[frequency]

              st.write("AQR Factors Preview:")
              st.dataframe(st.session_state.aqr_factors.head())
              st.write("Risk-Free Rate Preview:")
              st.dataframe(st.session_state.rf.head())

              st.success("✅ Custom AQR factors loaded successfully")
          except Exception as e:
            st.error(f"Error loading custom AQR factors: {str(e)}")

    # Analysis section
    if len(portfolio.funds) > 0 and benchmark_data is not None and 'aqr_factors' in st.session_state:
      if st.button("Run Analysis", help="Launch the complete portfolio analysis"):
        st.header("3. Analysis Results")

        with st.spinner("Running analysis... This may take a few moments."):
          try:
            # Store all analysis results in session state
            st.session_state.analysis_data = {
              'stats_report': portfolio.reporting(st.session_state.rf, benchmark_data),
              'factor_analysis': portfolio.factorial_analysis(st.session_state.aqr_factors),
              'nav_data': pd.DataFrame({name: fund.NAV for name, fund in portfolio.funds.items()}),
              'benchmark_nav': benchmark_data.NAV
            }

            # Mark analysis as complete
            st.session_state.analysis_complete = True

          except Exception as e:
            logger.error("Error in analysis:", exc_info=True)
            st.error(f"Error in analysis: {str(e)}")
            return

    # Display results section - only show if analysis is complete
    if st.session_state.analysis_complete:
      # Get data from session state
      data = st.session_state.analysis_data
      factor_loadings = data['factor_analysis'].calculate_factor_loadings()

      # Create tabs
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
        st.dataframe(
          factor_loadings.style
          .format("{:.6f}")
          .apply(highlight_extremes, axis=1)
        )

      with tab3:
        st.subheader("Regression Summaries")
        summaries = data['factor_analysis'].summarize_results()
        for fund_name, summary in summaries.items():
          with st.expander(f"Regression Summary - {fund_name}"):
            st.text(summary)

      with tab4:
        st.subheader("Visualizations")
        viz = Visualization()

        # Configure Matplotlib style
        plt.style.use('seaborn-v0_8-darkgrid')

        col1, col2 = st.columns(2)

        with col1:
          st.subheader("Performance Cumulée")
          fig_perf = viz.plot_performance(data['nav_data'])
          st.pyplot(fig_perf)

        with col2:
          st.subheader("Métriques de Risque")
          fig_risk = viz.plot_risk_metrics(data['stats_report'])
          st.pyplot(fig_risk)

        # Heatmap
        st.subheader("Heatmap des Charges Factorielles")
        try:
          fig_heatmap = viz.plot_factor_heatmap(factor_loadings)
          st.pyplot(fig_heatmap)
        except Exception as e:
          logger.warning(f"Could not generate heatmap: {str(e)}")
          st.warning("Impossible de générer la heatmap")

        # Rolling analysis section with slider
        st.subheader("Analyses Glissantes")

        window_size = st.slider(
          "Fenêtre d'analyse glissante (jours)",
          min_value=30,
          max_value=252,
          value=60,
          help="Ajustez la fenêtre temporelle pour les analyses de corrélations et de beta"
        )

        col3, col4 = st.columns(2)

        with col3:
          st.markdown("##### Corrélations Glissantes")
          fig_corr = viz.plot_rolling_correlation(
            data['nav_data'],
            window=window_size
          )
          if fig_corr is not None:
            st.pyplot(fig_corr)
          else:
            st.info("Corrélations non disponibles - nécessite au moins 2 fonds")

        with col4:
          st.markdown("##### Beta Glissant")
          fig_beta = viz.plot_rolling_beta(
            data['nav_data'],
            data['benchmark_nav'],
            window=window_size
          )
          st.pyplot(fig_beta)

  finally:
    # Cleanup temporary files
    for temp_path in temp_paths:
      try:
        if os.path.exists(temp_path):
          os.unlink(temp_path)
          logger.debug(f"Cleaned up temporary file: {temp_path}")
      except Exception as e:
        logger.error(f"Error cleaning up {temp_path}: {str(e)}")


if __name__ == "__main__":
  main()
