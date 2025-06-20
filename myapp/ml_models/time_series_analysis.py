import streamlit as st
import pandas as pd
import numpy as np
import statsmodels.api as sm
from statsmodels.stats.outliers_influence import variance_inflation_factor
from statsmodels.tsa.stattools import adfuller
from statsmodels.tsa.seasonal import seasonal_decompose
from pmdarima import auto_arima
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_squared_error, root_mean_squared_error, mean_absolute_percentage_error, mean_absolute_error
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import matplotlib.pyplot as plt

def load_data():
    """Load data from uploaded file with error handling and proper formatting."""
    uploaded_data = st.file_uploader('📂 Upload Data File', type=['csv', 'txt', 'xlsx', 'xls'])
    if uploaded_data is not None:
        try:
            if uploaded_data.type == 'text/plain':
                delimiter = st.radio('Select delimiter (separator)', [',', '\t', '|', ' ', 'Auto Detect'])
                if delimiter == 'Auto Detect':
                    df = pd.read_csv(uploaded_data, sep=None, engine='python')
                else:
                    df = pd.read_csv(uploaded_data, sep=delimiter)
            elif uploaded_data.type == 'text/csv':
                df = pd.read_csv(uploaded_data)
            elif uploaded_data.type in ['application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', 
                                      'application/vnd.ms-excel']:
                df = pd.read_excel(uploaded_data)
            
            st.write('### 🔍 Dataset Preview')
            st.dataframe(df.head())
            return df
        except Exception as e:
            st.error(f"Error loading file: {str(e)}")
            return None
    return None

@st.cache_data
def standardize(X, scale_data):
    """Standardize data if requested."""
    if scale_data:
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        return pd.DataFrame(X_scaled, columns=X.columns, index=X.index)
    return X

def main():
    st.title('⏳💹 Time Series Analysis')
                                                        
    @st.cache_data
    def adf_test(series):
        """Perform Augmented Dickey-Fuller test for stationarity."""
        return adfuller(series.dropna())

    @st.cache_data
    def get_auto_arima(series, seasonal=False):
        """Find optimal ARIMA parameters using auto_arima."""
        return auto_arima(
            series, 
            max_p=5, 
            max_q=5, 
            m=12 if seasonal else 1, 
            seasonal=seasonal, 
            stepwise=True, 
            suppress_warnings=True,
            error_action='ignore'
        )

    df = load_data()

    if df is not None:
        col1, col2 = st.columns(2)

        with col1:
            time_column = st.selectbox('⏳ Select Time Column:', df.columns)
        with col2:
            target_column = st.selectbox('📌 Select Target Variable:', [col for col in df.columns if col != time_column])

        try:
            df[time_column] = pd.to_datetime(df[time_column])
            df.set_index(time_column, inplace=True)
        except Exception as e:
            st.error(f"Error converting time column: {str(e)}")
            st.stop()

        date_range_buttons = [
            {"count": 1, "step": "day", "stepmode": "todate", "label": "1D"},
            {"count": 7, "step": "day", "stepmode": "todate", "label": "WTD"},
            {"count": 1, "step": "month", "stepmode": "todate", "label": "1M YTD"},
            {"count": 6, "step": "month", "stepmode": "todate", "label": "6M YTD"},
            {"count": 1, "step": "year", "stepmode": "todate", "label": "1YTD"},
            {"count": 5, "step": "year", "stepmode": "backward", "label": "Last 5Y"},
            {"step": "all", "label": "All"}
        ]

        # Main time series plot
        fig = px.line(df, x=df.index, y=target_column, title=f'Time Series Plot: {target_column}')
        fig.update_layout(
            xaxis=dict(
                rangeselector=dict(buttons=date_range_buttons),
                rangeslider=dict(visible=True),
                type="date"
            ),
            yaxis_title=target_column
        )
        st.plotly_chart(fig, use_container_width=True)

        # Data transformation options
        transform_options = st.radio("Data Transformation:", 
                                   ["Original", "Yearly Average", "Monthly Average", "Quarterly Average"])
        
        if transform_options != "Original":
            if transform_options == "Yearly Average":
                freq = 'Y'
                agg_func = 'mean'
                x_title = "Year"
            elif transform_options == "Monthly Average":
                freq = 'M'
                agg_func = 'mean'
                x_title = "Month"
            else:  # Quarterly Average
                freq = 'Q'
                agg_func = 'mean'
                x_title = "Quarter"
            
            df_transformed = df.resample(freq)[target_column].agg(agg_func).reset_index()
            df_transformed[time_column] = df_transformed[time_column].dt.to_period(freq).astype(str)
            
            fig_transformed = px.line(df_transformed, x=time_column, y=target_column,
                                    title=f'{transform_options} of {target_column}',
                                    labels={time_column: x_title, target_column: f'{transform_options} {target_column}'})
            
            fig_transformed.update_layout(
                xaxis=dict(
                    rangeselector=dict(buttons=date_range_buttons),
                    rangeslider=dict(visible=True),
                    type="category"
                )
            )
            st.plotly_chart(fig_transformed, use_container_width=True)
            
            # Use transformed data for analysis
            analysis_df = df_transformed.set_index(time_column)
        else:
            analysis_df = df[[target_column]]

        with st.expander('🔬 Advanced Analytics'):
            st.subheader('Time-Series Diagnostics')

            # Decomposition
            st.write("### 🔎 Series Decomposition")
            
            if transform_options == "Original":
                max_period = min(365, len(analysis_df) // 2)
                default_period = min(12, max_period)
            else:
                max_period = min(24, len(analysis_df) // 2)
                default_period = min(12, max_period)
            
            decomp_period = st.slider('Seasonal Period', min_value=1, max_value=max_period, 
                                     value=default_period, step=1)

            try:
                decomposed = seasonal_decompose(analysis_df[target_column].dropna(), 
                                               model="additive", 
                                               period=decomp_period)
                
                decomp_fig = make_subplots(
                    rows=4, cols=1, shared_xaxes=True, vertical_spacing=0.05,
                    subplot_titles=["Observed", "Trend", "Seasonal", "Residual"]
                )

                for i, (comp, name, color) in enumerate(zip(
                    [decomposed.observed, decomposed.trend, decomposed.seasonal, decomposed.resid],
                    ["Observed", "Trend", "Seasonal", "Residual"],
                    ["royalblue", "green", "orange", "red"])):
                        decomp_fig.add_trace(
                            go.Scatter(x=analysis_df.index, y=comp, name=name, line=dict(color=color)), 
                            row=i+1, col=1
                        )
                        
                decomp_fig.update_layout(height=800, showlegend=False, template="plotly_white")
                st.plotly_chart(decomp_fig, use_container_width=True)
            except Exception as e:
                st.error(f"Decomposition failed: {str(e)}")

            # Stationarity check
            st.write('### 🚧 Stationarity Check')
            adf_result = adf_test(analysis_df[target_column])
            st.info(f"ADF Statistic: {adf_result[0]:.4f}")
            st.info(f"P-Value: {adf_result[1]:.4f}")
            
            if adf_result[1] < 0.05:
                st.success("✅ Series is stationary.")
            else:
                st.warning("⚠️ Series is not stationary. Consider differencing.")

            # Differencing
            if adf_result[1] >= 0.05:
                st.write("### 🔁 Time-Series Differencing")
                differencing_order = st.slider('Differencing Order', 1, 3, 1)
                
                df_diff = analysis_df[target_column].copy()
                for _ in range(differencing_order):
                    df_diff = df_diff.diff().dropna()

                diff_adf_result = adf_test(df_diff)
                st.info(f"ADF Statistic (Differenced): {diff_adf_result[0]:.4f}")
                st.info(f"P-Value: {diff_adf_result[1]:.4f}")
                
                if diff_adf_result[1] < 0.05:
                    st.success("✅ Now stationary after differencing.")
                    fig_diff = px.line(
                        x=analysis_df.index[-len(df_diff):], 
                        y=df_diff, 
                        title=f'Time Series after Differencing (Order {differencing_order})'
                    )
                    st.plotly_chart(fig_diff, use_container_width=True)
                else:
                    st.warning("⚠️ Still non-stationary. May need further differencing.")

            # ACF/PACF plots
            st.write('### 📉 ACF & PACF Plots')
            
            if adf_result[1] >= 0.05 and 'df_diff' in locals():
                st.info("Showing ACF/PACF of differenced series:")
                series_to_plot = df_diff
            else:
                st.info("Showing ACF/PACF of original series:")
                series_to_plot = analysis_df[target_column]

            max_possible_lag = min(50, len(series_to_plot) // 2)
            max_lag = st.slider("Select number of lags to show", 
                               min_value=5, 
                               max_value=max_possible_lag, 
                               value=min(20, max_possible_lag), 
                               step=1)

            fig, axes = plt.subplots(1, 2, figsize=(12, 4))
            sm.graphics.tsa.plot_acf(series_to_plot, lags=max_lag, ax=axes[0], title="ACF")
            sm.graphics.tsa.plot_pacf(series_to_plot, lags=max_lag, ax=axes[1], title="PACF")
            st.pyplot(fig)

            # Auto ARIMA
            st.write("### 🤖 Automatically-Selected Best ARIMA Order")
            seasonal = st.checkbox("Consider seasonal components?", value=False)
            
            with st.spinner("Finding optimal ARIMA parameters..."):
                try:
                    auto_model = get_auto_arima(analysis_df[target_column].dropna(), seasonal=seasonal)
                    st.success(f"✅ Best ARIMA Order: {auto_model.order}")
                    if seasonal:
                        st.success(f"✅ Seasonal Order: {auto_model.seasonal_order}")
                    
                    st.write("🔍 Auto ARIMA Model Summary")
                    st.dataframe(auto_model.summary().tables[1])
                except Exception as e:
                    st.error(f"ARIMA modeling failed: {str(e)}")

        # Forecasting
        st.write("## 🔮 Forecasting")
        forecast_horizon = st.slider("Forecast Steps", 1, 36, 12)
        
        if 'auto_model' in locals():
            try:
                arima_forecast, conf_int = auto_model.predict(
                    n_periods=forecast_horizon, 
                    return_conf_int=True
                )
                
                # Create forecast index based on data frequency
                if transform_options == "Yearly Average":
                    freq = 'Y'
                elif transform_options == "Monthly Average":
                    freq = 'M'
                elif transform_options == "Quarterly Average":
                    freq = 'Q'
                else:  # Original data
                    freq = 'D' if pd.infer_freq(analysis_df.index) == 'D' else 'M'
                
                last_date = analysis_df.index[-1] if isinstance(analysis_df.index, pd.DatetimeIndex) else pd.to_datetime(analysis_df.index[-1])
                forecast_index = pd.date_range(
                    start=last_date, 
                    periods=forecast_horizon+1, 
                    freq=freq
                )[1:]
                
                forecast_df = pd.DataFrame({
                    "Date": forecast_index,
                    "Forecast": arima_forecast,
                    "Lower CI": conf_int[:, 0],
                    "Upper CI": conf_int[:, 1]
                })

                # Plot forecast
                fig_forecast = go.Figure()
                
                # Historical data
                fig_forecast.add_trace(
                    go.Scatter(
                        x=analysis_df.index,
                        y=analysis_df[target_column],
                        mode='lines',
                        name='Historical',
                        line=dict(color='blue')
                    )
                )
                
                # Forecast
                fig_forecast.add_trace(
                    go.Scatter(
                        x=forecast_df['Date'],
                        y=forecast_df['Forecast'],
                        mode='lines',
                        name='Forecast',
                        line=dict(color='red', dash='dash')
                )
                
                # Confidence interval
                fig_forecast.add_trace(
                    go.Scatter(
                        x=forecast_df['Date'].tolist() + forecast_df['Date'].tolist()[::-1],
                        y=forecast_df['Upper CI'].tolist() + forecast_df['Lower CI'].tolist()[::-1],
                        fill='toself',
                        fillcolor='rgba(255,0,0,0.2)',
                        line=dict(color='rgba(255,255,255,0)'),
                        name='95% Confidence'
                    )
                )
                
                fig_forecast.update_layout(
                    title=f"{forecast_horizon}-Period Forecast",
                    xaxis_title="Date",
                    yaxis_title=target_column
                )
                
                st.plotly_chart(fig_forecast, use_container_width=True)
                
                # Model evaluation
                st.write("## 📊 Model Evaluation")
                
                # Split data into train/test
                train_size = int(len(analysis_df) * 0.8)
                train, test = analysis_df.iloc[:train_size], analysis_df.iloc[train_size:]
                
                # Fit model on training data
                model = get_auto_arima(train[target_column].dropna(), seasonal=seasonal)
                predictions = model.predict(n_periods=len(test))
                
                # Calculate metrics
                if len(test) > 0:
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("RMSE", f"{root_mean_squared_error(test, predictions):.4f}")
                    with col2:
                        st.metric("MSE", f"{mean_squared_error(test, predictions):.4f}")
                    with col3:
                        st.metric("MAE", f"{mean_absolute_error(test, predictions):.4f}")
                    with col4:
                        st.metric("MAPE", f"{mean_absolute_percentage_error(test, predictions):.2%}")
                    
                    # Plot actual vs predicted
                    fig_eval = go.Figure()
                    fig_eval.add_trace(
                        go.Scatter(
                            x=test.index,
                            y=test[target_column],
                            mode='lines',
                            name='Actual',
                            line=dict(color='blue')
                        )
                    )
                    fig_eval.add_trace(
                        go.Scatter(
                            x=test.index,
                            y=predictions,
                            mode='lines',
                            name='Predicted',
                            line=dict(color='red')
                    )
                    fig_eval.update_layout(title="Actual vs Predicted (Test Set)")
                    st.plotly_chart(fig_eval, use_container_width=True)
                
            except Exception as e:
                st.error(f"Forecasting failed: {str(e)}")

    with st.expander("**ℹ️ About Time Series Analysis**"):
        st.write("""
        Time Series Analysis helps in understanding patterns in data over time. 
        - **Trend**: Long-term movement in data.
        - **Seasonality**: Repeating patterns at regular intervals.
        - **Stationarity**: Data has a constant mean and variance over time.
        - **Autocorrelation**: How past values influence future values.
        
        **ARIMA Models** combine:
        - AR (Autoregression): Model uses dependent relationship between observation and lagged observations.
        - I (Integrated): Differencing of raw observations to make time series stationary.
        - MA (Moving Average): Model uses dependency between observation and residual error from moving average.
        """)

if __name__ == '__main__':
    st.set_page_config(page_title="Time Series Analyzer", layout="wide")
    main()
