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

def data():
    uploaded_data = st.file_uploader('📂 Upload Data File', type=['csv', 'txt', 'xlsx'])
    if uploaded_data is not None:
        if uploaded_data.type == 'text/plain':
            delimiter = st.radio('Select delimiter (separator)', [',', '/t', '|', ' ', 'Auto Detect'])
            if delimiter == 'Auto Detect':
                try:
                    df = pd.read_csv(uploaded_data, sep=None, engine='python')
                except Exception:
                    st.error("Could not auto-detect delimiter (separator), try selecting one manually.")
                    df = None
            else:
                df = pd.read_csv(uploaded_data, sep=delimiter)
        elif uploaded_data.type == 'text/csv':
            df = pd.read_csv(uploaded_data)
            st.write('### 🔍 Dataset Preview')
            st.dataframe(df.head())
            return df
        elif uploaded_data.type == 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet':
            df = pd.read_excel(uploaded_data)
            st.write('### 🔍 Dataset Preview')
            st.dataframe(df.head())
            return df
            
        return None

@st.cache_data
def standardize(X, scale_data):
    if scale_data:
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        return pd.DataFrame(X_scaled, columns=X.columns, index=X.index)
    return X

def main():
    st.title('⏳💹 Time Series Analysis')
                                                        
    @st.cache_data
    def adf_test(series):
        return adfuller(series.dropna())

    def get_auto_arima(series):
        return auto_arima(series, max_p=2, max_q=2, m=1, seasonal=False, stepwise=True, suppress_warnings=True)

    df = data()

    if df is not None:
        col1, col2 = st.columns(2)

        with col1:
            time_column = st.selectbox('⏳ Select Time Column:', df.columns)
        with col2:
            target_column = st.selectbox('📌 Select Target Variable:', df.columns)

        df[time_column] = pd.to_datetime(df[time_column])
        df.set_index(time_column, inplace = True)

        if target_column == time_column:
            st.warning('Please select a non-time column for the target variable.')
            st.stop()

        date_range_buttons = [
            {"count": 1, "step": "day", "stepmode": "todate", "label": "1D"},
            {"count": 7, "step": "day", "stepmode": "todate", "label": "WTD"},
            {"count": 1, "step": "month", "stepmode": "todate", "label": "1M YTD"},
            {"count": 6, "step": "month", "stepmode": "todate", "label": "6M YTD"},
            {"count": 1, "step": "year", "stepmode": "todate", "label": "1YTD"},
            {"count": 5, "step": "year", "stepmode": "backward", "label": "Last 5Y"},
            {"count": 10, "step": "year", "stepmode": "backward", "label": "Last 10Y"},
            {"count": 15, "step": "year", "stepmode": "backward", "label": "Last 15Y"},
            {"count": 20, "step": "year", "stepmode": "backward", "label": "Last 20Y"},
            {"count": 25, "step": "year", "stepmode": "backward", "label": "Last 25Y"},
            {"count": 30, "step": "year", "stepmode": "backward", "label": "Last 30Y"},
            {"step": "all", "label": "All"}
            ]

        fig = px.line(df, x = df.index, y = target_column, title = 'Time Series Plot', labels = {time_column:"Time"})
        fig.update_layout(
            xaxis=dict(
                rangeselector=dict(
                    buttons=date_range_buttons),
                    rangeslider=dict(visible=True),
                    type="date"))
        st.plotly_chart(fig, use_container_width = True)

        yearly_avg = st.checkbox("Yearly average transformation?")
        if yearly_avg:
            st.write('### Yearly Average Transformation')
    
            df_yearly = df.resample('Y')[target_column].mean().reset_index()
            df_yearly[time_column] = df_yearly[time_column].dt.year
        
            fig2 = px.line(df_yearly, x=time_column, y=target_column,
                            title='Time Series Plot - Yearly Average',
                            labels={time_column: "Year", target_column: "Yearly Avg"})
        
            fig2.update_layout(
                xaxis=dict(
                    tickformat="%Y",
                    dtick=1,
                    rangeselector=dict(buttons=date_range_buttons),
                    rangeslider=dict(visible=True),
                    type="linear"
                )
            )

            st.plotly_chart(fig2, use_container_width=True)

        with st.expander('🔬 Advanced Analytics'):
            st.subheader('Time-Series Diagnoistics')

            st.write("### 🔎 Series Decomposition")
                
            if yearly_avg:
                decomp_period = st.slider('Seasonal Period', min_value=1, max_value=12, value=6, step=1)

                decomposed = seasonal_decompose(df_yearly[target_column], model="additive", period=decomp_period)
                decomp_fig = make_subplots(
                    rows=4, cols=1, shared_xaxes=True, vertical_spacing=0.05,
                    subplot_titles=["Observed", "Trend", "Seasonal", "Residual"]
                )

                for i, (comp, name, color) in enumerate(zip(
                    [decomposed.observed, decomposed.trend, decomposed.seasonal, decomposed.resid],
                    ["Observed", "Trend", "Seasonal", "Residual"],
                    ["royalblue", "green", "orange", "red"])):
                        decomp_fig.add_trace(go.Scatter(x=df_yearly.index, y=comp, name=name, line=dict(color=color)), row=i+1, col=1)
                        
                decomp_fig.update_layout(height=4*250, showlegend=False, template="plotly_white")
                st.plotly_chart(decomp_fig, use_container_width=True)

                st.write('### 🚧 Stationarity Check')
                adf_result = adf_test(df_yearly[target_column].dropna())
                st.info(f"ADF Statistic: {adf_result[0]:.4f}")
                st.info(f"P-Value: {adf_result[1]:.4f}")
                if adf_result[1] < 0.05:
                    st.success("✅ Series is stationary.")
                else:
                    st.warning("⚠️ Series is not stationary. Consider differencing.")

                # Optional Differencing Step
                if adf_result[1] >= 0.05:
                    st.write("### 🔁 Time-Serie Differencing")
                
                    differencing_order = st.slider('Differencing Order', 1, 3, 1)
                
                    df_diff = df_yearly[target_column].copy()
                    for _ in range(differencing_order):
                        df_diff = df_diff.diff().dropna()
    
                    diff_adf_result = adf_test(df_diff)
                    st.info(f"ADF Statistic (Differenced): {diff_adf_result[0]:.4f}")
                    st.info(f"P-Value: {diff_adf_result[1]:.4f}")
                
                    if diff_adf_result[1] < 0.05:
                        st.success("✅ Now stationary after differencing.")
                        fig = px.line(df_diff, x = df_yearly[time_column], y = target_column, title = 'Time Series Plot after Differencing', labels = {time_column:"Time"})
                        fig.update_layout(
                            xaxis=dict(
                                rangeselector=dict(
                                    buttons=date_range_buttons),
                                    rangeslider=dict(visible=True),
                                    type="date"))
                        st.plotly_chart(fig, use_container_width = True)
                    else:
                        st.warning("⚠️ Still non-stationary. May need further differencing.")

                # ACF / PACF depending on stationarity
                st.write('### 📉 ACF & PACF Plots')

                if adf_result[1] >= 0.05:
                    st.info("Showing ACF/PACF of differenced series:")
                    series_to_plot = df_diff
                else:
                    st.info("Series is stationary — showing original ACF/PACF.")
                    series_to_plot = df_yearly[target_column]

                max_possible_lag = min(100, len(series_to_plot) // 2)
                max_lag = st.slider("Select number of lags to show", min_value=10, max_value=max_possible_lag, value=min(40, max_possible_lag), step=5)

                fig, axes = plt.subplots(1, 2, figsize=(12, 5))
                sm.graphics.tsa.plot_acf(series_to_plot, lags = max_lag, ax=axes[0])
                sm.graphics.tsa.plot_pacf(series_to_plot, lags = max_lag, ax=axes[1])
                st.pyplot(fig)

                st.write("### 🤖 Automatically-Selected Best ARIMA Order")
                with st.spinner("Running auto_arima... please wait ⏳"):
                    auto_model = get_auto_arima(df_yearly[target_column])
                st.success(f"✅ Best ARIMA Order: {auto_model.order}")
                st.write("🔍 Auto ARIMA Model Summary")
                st.dataframe(auto_model.summary().tables[1])

            else:
                decomp_period = st.slider('Seasonal Period', min_value=1, max_value=365, value=132, step=1)

                decomposed = seasonal_decompose(df[target_column], model="additive", period=decomp_period)
                decomp_fig = make_subplots(
                    rows=4, cols=1, shared_xaxes=True, vertical_spacing=0.05,
                    subplot_titles=["Observed", "Trend", "Seasonal", "Residual"]
                )

                for i, (comp, name, color) in enumerate(zip(
                    [decomposed.observed, decomposed.trend, decomposed.seasonal, decomposed.resid],
                    ["Observed", "Trend", "Seasonal", "Residual"],
                    ["royalblue", "green", "orange", "red"])):
                        decomp_fig.add_trace(go.Scatter(x=df.index, y=comp, name=name, line=dict(color=color)), row=i+1, col=1)
                        
                decomp_fig.update_layout(height=4*250, showlegend=False, template="plotly_white")
                st.plotly_chart(decomp_fig, use_container_width=True)

                st.write('### 🚧 Stationarity Check')
                adf_result = adf_test(df[target_column].dropna())
                st.info(f"ADF Statistic: {adf_result[0]:.4f}")
                st.info(f"P-Value: {adf_result[1]:.4f}")
                if adf_result[1] < 0.05:
                    st.success("✅ Series is stationary.")
                else:
                    st.warning("⚠️ Series is not stationary. Consider differencing.")

                # Optional Differencing Step
                if adf_result[1] >= 0.05:
                    st.write("### 🔁 Time-Serie Differencing")
                
                    differencing_order = st.slider('Differencing Order', 1, 3, 1)
                
                    df_diff = df[target_column].copy()
                    for _ in range(differencing_order):
                        df_diff = df_diff.diff().dropna()
                
                    diff_adf_result = adf_test(df_diff)
                    st.info(f"ADF Statistic (Differenced): {diff_adf_result[0]:.4f}")
                    st.info(f"P-Value: {diff_adf_result[1]:.4f}")
                
                    if diff_adf_result[1] < 0.05:
                        st.success("✅ Now stationary after differencing.")
                    else:
                        st.warning("⚠️ Still non-stationary. May need further differencing.")

                # ACF / PACF depending on stationarity
                st.write('### 📉 ACF & PACF Plots')

                if adf_result[1] >= 0.05:
                    st.info("Showing ACF/PACF of differenced series:")
                    series_to_plot = df_diff
                else:
                    st.info("Series is stationary — showing original ACF/PACF.")
                    series_to_plot = df[target_column]

                max_possible_lag = min(100, len(series_to_plot) // 2)
                max_lag = st.slider("Select number of lags to show", min_value=10, max_value=max_possible_lag, value=min(40, max_possible_lag), step=5)

                fig, axes = plt.subplots(1, 2, figsize=(12, 5))
                sm.graphics.tsa.plot_acf(series_to_plot, lags = max_lag, ax=axes[0])
                sm.graphics.tsa.plot_pacf(series_to_plot, lags = max_lag, ax=axes[1])
                st.pyplot(fig)

                st.write("### 🤖 Automatically-Selected Best ARIMA Order")
                auto_model = get_auto_arima(df[target_column])
                st.success(f"✅ Best ARIMA Order: {auto_model.order}")
                st.write("🔍 Auto ARIMA Model Summary")
                st.dataframe(auto_model.summary().tables[1])

        if yearly_avg:
            forecast_horizon = st.slider("Forecast Steps", 1, 24, 12, key="s1")
            arima_forecast = auto_model.predict(n_periods=forecast_horizon)
            forecast_index = pd.date_range(start=df.index[-1], periods=forecast_horizon+1, freq = 'Y')[1:]
            forecast_df = pd.DataFrame({"Date": forecast_index, "Forecast": arima_forecast})
    
            fig_forecast = px.line(df_yearly, x=df_yearly[time_column], y=target_column, title="Auto-ARIMA Forecast", labels={time_column: "Year"})
            fig_forecast.add_scatter(x=forecast_df['Date'], y=forecast_df['Forecast'], mode='lines', name='Forecast', line=dict(color='red'))
            st.plotly_chart(fig_forecast)
    
            actuals = df_yearly[target_column][-12:].dropna()
            forecasts = arima_forecast[:len(actuals)]

            if len(actuals) == len(forecasts):
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric(label = "Root Mean Squared Error", value = f"{root_mean_squared_error(actuals, forecasts):.4f}", help="RMSE measures the average magnitude of the errors. Lower values indicate better model performance. Better for real-world explanations.")
                with col2:
                    st.metric(label = "Mean Squared Error", value = f"{mean_squared_error(actuals, forecasts):.4f}", help="MSE measures the average of squared errors. Better for optimizing algorithms")
                with col3:
                    st.metric(label = "Mean Absolute Error", value = f"{mean_absolute_error(actuals, forecasts):.4f}", help="MAE measures the average magnitude of errors in a set of predictions, without considering their direction.")
                with col4:
                    st.metric(label = "Mean Absolute Percentage Error", value=f"{mean_absolute_percentage_error(actuals, forecasts):.2f}%", help="MAPE measures prediction accuracy as a percentage.")

        else:
            forecast_horizon = st.slider("Forecast Steps", 1, 24, 12, key="s2")
            arima_forecast = auto_model.predict(n_periods=forecast_horizon)
            forecast_index = pd.date_range(start=df.index[-1], periods=forecast_horizon+1, freq = 'M')[1:]
            forecast_df = pd.DataFrame({"Date": forecast_index, "Forecast": arima_forecast})
    
            fig_forecast = px.line(df, x=df_yearly[time_column], y=target_column, title="Auto-ARIMA Forecast", labels = {time_column:"Time"})
            fig_forecast.add_scatter(x=forecast_df['Date'], y=forecast_df['Forecast'], mode='lines', name='Forecast', line=dict(color='red'))
            st.plotly_chart(fig_forecast)
    
            actuals = df[target_column][-12:].dropna()
            forecasts = arima_forecast[:len(actuals)]
    
            if len(actuals) == len(forecasts):
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric(label = "Root Mean Squared Error", value = f"{root_mean_squared_error(actuals, forecasts):.4f}", help="RMSE measures the average magnitude of the errors. Lower values indicate better model performance. Better for real-world explanations.")
                with col2:
                    st.metric(label = "Mean Squared Error", value = f"{mean_squared_error(actuals, forecasts):.4f}", help="MSE measures the average of squared errors. Better for optimizing algorithms")
                with col3:
                    st.metric(label = "Mean Absolute Error", value = f"{mean_absolute_error(actuals, forecasts):.4f}", help="MAE measures the average magnitude of errors in a set of predictions, without considering their direction.")
                with col4:
                    st.metric(label = "Mean Absolute Percentage Error", value=f"{mean_absolute_percentage_error(actuals, forecasts):.2f}%", help="MAPE measures prediction accuracy as a percentage.")

    with st.expander("**ℹ️ About Time Series Analysis**"):
        st.write("""
                Time Series Analysis helps in understanding patterns in data over time. 
                - **Trend**: Long-term movement in data.
                - **Seasonality**: Repeating patterns at regular intervals.
                - **Stationarity**: Data has a constant mean and variance over time.
                - **Autocorrelation**: How past values influence future values.
                """)

if __name__ == '__main__':
    main()