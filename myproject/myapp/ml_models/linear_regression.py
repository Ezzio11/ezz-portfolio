import streamlit as st
import pandas as pd
import numpy as np
import statsmodels.api as sm
from statsmodels.stats.outliers_influence import variance_inflation_factor
from statsmodels.stats.stattools import jarque_bera
from statsmodels.stats.diagnostic import het_breuschpagan
from scipy.stats import boxcox
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_squared_error
import plotly.express as px

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
def calculate_vif(X):
    X = X.select_dtypes(include=[np.number]).dropna()
    X = X.loc[:, (X != X.iloc[0]).any()]
    if X.shape[1] < 2:
        return None
    vif_data = pd.DataFrame()
    vif_data["Feature"] = X.columns
    vif_data["VIF"] = [variance_inflation_factor(X.values, i) for i in range(X.shape[1])]
    return vif_data

@st.cache_data
def standardize(X, scale_data):
    if scale_data:
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        return pd.DataFrame(X_scaled, columns=X.columns, index=X.index)
    return X

def main():
    st.title('📈 Linear Regression Analysis')
                                                        
    df = data()

    if df is not None and not df.empty:
        if df.isnull().sum().sum() > 0:
            st.warning("⚠️ Dataset contains missing values. Choose a handling method")
            method = st.selectbox("Choose an imputation method", ['Fill with mean', 'Fill with median', 'Fill with mode', 'Drop rows'])
            if method == 'Fill with mean':
                df.fillna(df.mean(), inplace=True)
            elif method == 'Fill with median':
                df.fillna(df.median(), inplace=True)
            elif method == 'Fill with mode':
                df.fillna(df.mode().iloc[0], inplace=True)
            elif method == 'Drop rows':
                df.dropna(inplace=True)

    st.markdown('---')

    if df is not None:
        col1, col2 = st.columns(2)
        with col1:
            predictor = st.multiselect('🎯 Select Predictor Variable(s)', df.columns)
        with col2:
            target = st.selectbox('📌 Select Target Variable', df.columns)

        if predictor and target:
            X = df[predictor]
            y = df[target]

            st.markdown('---')

            with st.expander("🔄 **Apply Transformations (Optional)**"):
                log_transform = st.checkbox("Apply Log Transformation")
                sqrt_transform = st.checkbox("Apply Square Root Transformation")
                inverse_transform = st.checkbox("Apply Inverse Transformation (If The Data Is Mostly Negative)")
                boxcox_transform = st.checkbox("Apply Box-Cox Transformation (Requires Positive Data)")

                if log_transform:
                    X = np.log1p(X)
                if sqrt_transform:
                    X = np.sqrt(X)
                if inverse_transform:
                    X = 1/(X+1e-6)
                if boxcox_transform:
                    for col in X.columns:
                        if (X[col] > 0).all():
                            X[col], _ = boxcox(X[col] + 1e-6)

            st.markdown('---')

            scale_data = st.checkbox("⚙️ **Standardize predictor(s) values?**")
            X = standardize(X, scale_data)

            st.markdown('---')

            st.subheader("Train-Test Split")
            test_data = st.slider('Test data percentage',10,50,20,step=5)/100
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=test_data, random_state=619)

            st.markdown('---')

            X_train_const = sm.add_constant(X_train)
            X_test_const = sm.add_constant(X_test)

            model = sm.OLS(y_train, X_train_const).fit()
            y_pred = model.predict(X_test_const)
            y_train_pred = model.predict(X_train_const)
            r2 = model.rsquared
            adj_r2 = model.rsquared_adj

            df_results = pd.DataFrame({"Actual": y_test, "Predicted": y_pred})

            st.write('## 📈 Model Performance')
            col1, col2, col3 = st.columns(3)
            if len(predictor) == 1:
                with col1:
                    st.metric(label="R-Squared", value=f"{r2:.4f}")
                if r2 < 0.5:
                    st.warning("⚠️ Low predictive power. Consider feature engineering or a different model.")
                else:
                    st.success(f"✅ {r2:.0%} of the variance in {target} is explained by the predictors!")
                
            elif len(predictor) > 1:
                with col1:
                    st.metric(label="Adjusted R-Squared", value=f"{adj_r2:.4f}")
            with col3:
                st.metric(label="Mean Squared Error", value=f"{mean_squared_error(y_test, y_pred):.4f}")
            
            if len(predictor) > 1:
                if adj_r2 < 0.5:
                    st.warning("⚠️ Adjusted R² is low. Consider adding more meaningful predictors or transformations.")
                else:
                    st.success(f"✅ Adjusted R² suggests that {adj_r2:.0%} of variance is explained, accounting for predictors used!")

            fig = px.scatter(df_results, x="Actual", y="Predicted", title='Actual vs Predicted',
                                labels={"Actual": "Actual Values", "Predicted": "Predicted Values"},
                                color_discrete_sequence=['blue'])
            fig.update_layout(autosize=True)
            st.plotly_chart(fig, use_container_width=True)

            with st.expander("🔬 Advanced Analytics"):
                st.subheader("Model Diagnostics")

                vif_data = calculate_vif(X_train_const)
                st.write("### 🔄 Multicollinearity Check (VIF)")

                if vif_data is not None and not vif_data.empty:                        
                    st.dataframe(vif_data)  
                    high_vif = vif_data[vif_data['VIF'] > 10]

                    if not high_vif.empty:
                        st.warning("⚠️ Features with high VIF (VIF > 10):")
                        st.dataframe(high_vif)
                    else:
                        st.success("✅ No multicollinearity issues detected.")
                else:
                    st.error("ℹ️ Not enough features to calculate VIF.")

                residuals = y_train - y_train_pred
                jb_stat, jb_pval, _, _ = jarque_bera(residuals)
                st.write("### 📊 Normality of Residuals (Jarque-Bera Test)")
                fig_qq = sm.qqplot(residuals, line="s", fit=True)
                st.pyplot(fig_qq.figure)

                st.write(f"JB Statistic: {jb_stat:.4f}, p-value: {jb_pval:.4f}")
                if jb_pval < 0.05:
                    st.warning("⚠️ Residuals are not normally distributed. Consider transformations.")
                else:
                    st.success("✅ Residuals appear normally distributed.")
                
                st.write("### 📉 Homoscedasticity (Breusch-Pagan Test)")
                _, bp_pval, _, _ = het_breuschpagan(residuals, X_train_const)
                fig_residuals = px.scatter(x=y_train_pred, y=residuals, 
                                        labels={'x': 'Fitted Values', 'y': 'Residuals'},
                                        title="Residuals vs Fitted Plot",
                                        color_discrete_sequence=['red'])
                st.plotly_chart(fig_residuals, use_container_width=True)

                st.write(f"p-value: {bp_pval:.4f}")
                if bp_pval < 0.05:
                    st.warning("⚠️ Heteroscedasticity detected. Consider transformations.")
                else:
                    st.success("✅ No significant heteroscedasticity detected.")

                st.write("### 🔍 Model Coefficients & Significance")
                st.dataframe(model.summary2().tables[1])
                st.write("""💡 If a coefficient's P-value > 0.05, it's insignificant. meaning the predictor doesn’t significantly contribute to explaining the target variable.
                        \nPossible reasons:
                        \n - Multicollinearity – Predictors are highly correlated (Check VIF values!).
                        \n - Insufficient Data – Small dataset or high noise.
                        \n - Irrelevant Features – Some predictors just don’t impact the target.
                        \n - Incorrect Model Specification – Maybe a nonlinear relationship exists.""")

            st.write('## 🎯 Make a Prediction')
            user_inputs = {}

            for feature in predictor:
                user_inputs[feature] = st.number_input(f"Enter value for {feature}:", value = float(X_test[feature].mean()))

            if st.button("Predict"):
                user_df = pd.DataFrame([user_inputs], columns = predictor)
                user_df = sm.add_constant(user_df, has_constant='add')
                prediction = model.predict(user_df)
                st.success(f"**Predicted Value for {target}**: {prediction.iloc[0]:.4f}")
                if all(val == 0 for val in user_inputs.values()):
                    with st.expander("💡 **Understanding Baseline Predictions**"):
                            st.markdown("""When using a predictive model, it's important to recognize how it behaves for extreme or unusual inputs. Models rely on mathematical relationships learned from data, but they don't always understand real-world constraints.
                            \nFor example, if a model predicts future sales based on advertising budget, setting the budget to zero might suggest negative sales, which isn't possible. This happens because the model follows a mathematical trend, even when the input goes beyond realistic values.
                            \nKey Takeaways:
                            \n- Baseline predictions occur when some or all input values are set to extreme or default values (like zero).
                            \n- The model may not handle unrealistic scenarios well, leading to strange or impossible predictions.
                            \n- Predictions make the most sense when inputs stay within a reasonable range.
                            \n- If you get an unusual result, consider whether the input values are realistic for the context. This helps ensure meaningful and reliable predictions!""")

    with st.expander("**ℹ️ About Linear Regression Analysis**"):
        st.write("""
                Linear Regression is a fundamental technique for modeling relationships between variables.
                - **Simple Linear Regression**: Models the relationship between one independent variable and a dependent variable.  
                - **Multiple Linear Regression**: Extends to multiple independent variables.  
                - **Assumptions**:
                    - **Linearity**: Relationship between X and Y is linear.  
                    - **Independence**: Residuals are independent of each other.  
                    - **Homoscedasticity**: Constant variance of residuals.  
                    - **Normality**: Residuals are normally distributed.  
                    - **Performance Metrics**: R² score, Mean Squared Error (MSE), Adjusted R².  
                """)
        
if __name__ == '__main__':
    main()