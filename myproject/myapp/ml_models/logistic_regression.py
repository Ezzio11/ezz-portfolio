import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import statsmodels.api as sm
from statsmodels.stats.outliers_influence import variance_inflation_factor
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, classification_report, roc_curve, roc_auc_score, confusion_matrix

def data():
    uploaded_data = st.file_uploader('📂 Upload Data File', type=['csv', 'txt', 'xlsx'])
    if uploaded_data is not None:
        try:
            if uploaded_data.type == 'text/plain':
                delimiter = st.radio('Select delimiter (separator)', [',', '\t', '|', ' ', 'Auto Detect'])
                if delimiter == 'Auto Detect':
                    df = pd.read_csv(uploaded_data, sep=None, engine='python')
                else:
                    df = pd.read_csv(uploaded_data, sep=delimiter)
                st.write('### 🔍 Dataset Preview')
                st.dataframe(df.head())
                return df
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
        except Exception as e:
            st.error(f"Error loading file: {str(e)}")
            return None
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
    st.title('📊 Logistic Regression Analysis')
                                                        
    df = data()

    if df is not None:
        col1, col2 = st.columns(2)
        with col1:
            predictor = st.multiselect('🎯 Select Predictor Variable(s)', df.columns)
        with col2:
            target = st.selectbox('📌 Select Binary (0,1) Variable', df.columns)

        if predictor and target:
            # Check if target is binary
            unique_values = df[target].unique()
            if len(unique_values) != 2:
                st.error("Error: Target variable must have exactly 2 unique values (binary classification)")
                return
            
            X = df[predictor]
            y = df[target]

            st.markdown('---')

            scale_data = st.checkbox("⚙️ **Standardize predictor(s) values?**")
            X = standardize(X, scale_data)

            st.markdown('---')

            test_data = st.slider("**Test data (%)**", 10,50,20,step=5)/100

            st.markdown('---')

            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=test_data, random_state=619)

            X_train_const = sm.add_constant(X_train)
            X_test_const = sm.add_constant(X_test)

            try:
                logit_model = sm.Logit(y_train, X_train_const).fit()
            except Exception as e:
                st.error(f"Model failed to converge: {str(e)}")
                return

            y_pred_prob = logit_model.predict(X_test_const)
            y_pred = (y_pred_prob > 0.5).astype(int)

            accuracy = accuracy_score(y_test, y_pred)
            roc_auc = roc_auc_score(y_test, y_pred_prob)

            col1, col2 = st.columns(2)

            with col1:
                st.metric(label="Accuracy Score", value=f"{accuracy:.0%}")
            with col2:
                st.metric(label="ROC AUC Score", value = f"{roc_auc:.4f}")

            vis_df = pd.DataFrame({"Actual":y_test, "Predicted Probability":y_pred_prob})

            fig = px.strip(vis_df, x="Actual", y="Predicted Probability", color="Actual",
                            stripmode="overlay", title="Actual vs. Predicted Probability",
                            labels={"Actual":"Actual Class", "Predicted Probability":"Predicted Probability"})

            st.plotly_chart(fig, use_container_width=True)

            with st.expander("🔬 Advanced Analytics"):
                st.subheader("Model Diagnostics")

                st.subheader("📄 Classification Report")
                report = classification_report(y_test, y_pred, output_dict=True)
                report_df = pd.DataFrame(report).T
                st.dataframe(report_df.style.format({"precision":"{:.2f}", "recall":"{:.2f}", "f1-score":"{:.2f}", "support":"{:.0f}"}))

                st.subheader("✖️ Confusion Matrix")
                st.write(pd.DataFrame(confusion_matrix(y_test, y_pred), 
                                index=['Actual Negative (0)', 'Actual Positive (1)'], 
                                columns=['Predicted Negative (0)', 'Predicted Positive (1)']))

                st.subheader("🔢 ROC AUC Score")
                fpr, tpr, _ = roc_curve(y_test, y_pred_prob)

                roc_df = pd.DataFrame({"False Positive Rate":fpr, "True Positive Rate":tpr})

                fig2 = px.line(roc_df, x="False Positive Rate", y="True Positive Rate", title = f"Receiver Operating Characteristic (ROC) Curve (AUC = {roc_auc:.2f})",
                                template= "plotly_white", labels={'False Positive Rate': 'False Positive Rate', 'True Positive Rate': 'True Positive Rate'})

                fig2.add_shape(type="line", x0=0,y0=0,x1=1,y1=1,
                                line={"color":"black", "dash":"dash"})

                st.plotly_chart(fig2, use_container_width = True)

                odds_ratios = pd.DataFrame({
                    'Feature': X_train.columns,
                    'Odds Ratio': np.exp(logit_model.params[1:])
                    }).sort_values(by='Odds Ratio', ascending=False)

                st.subheader("🔎 Feature Importance (Odds Ratios)")
                st.dataframe(odds_ratios)

                st.subheader("🔍 Model Coefficients & Significance")
                st.dataframe(logit_model.summary2().tables[1])

            st.subheader("🔮 Make a Prediction")

            user_input = {}
            for feature in predictor:
                user_input[feature] = st.number_input(f"Enter value for {feature}", value=float(X_test[feature].mean()))

            if st.button("Predict Outcome"):
                user_df = pd.DataFrame([user_input])
                user_df_sm = sm.add_constant(user_df, has_constant="add")

                pred_prob = logit_model.predict(user_df_sm)[0]
                pred_class = int(pred_prob > 0.5)

                st.subheader(f"🎯 Predicted Probability: {pred_prob:.4f}")
                st.subheader(f"0️⃣ 1️⃣ Predicted Class (0 or 1): {pred_class}")

    with st.expander("**ℹ️ About Logistic Regression**"):
        st.write("""
    **Logistic Regression** is a statistical method used for binary and multi-class classification problems.  
    - Unlike linear regression, it predicts **probabilities** using the **sigmoid function**, mapping outputs between 0 and 1.  
    - **Types of Logistic Regression**:  
        - **Binary Logistic Regression**: Predicts one of two possible outcomes (e.g., spam or not spam).  
        - **Multinomial Logistic Regression**: Handles more than two categorical outcomes.  
        - **Ordinal Logistic Regression**: Used when the categories have a meaningful order.  
    - **Assumptions**:  
        - **Independent observations**: Each data point is independent.  
        - **No multicollinearity**: Predictors should not be highly correlated.  
        - **Linear relationship with log-odds**: Independent variables should be linearly related to the log-odds of the dependent variable.  
        - **Large sample size**: Logistic regression performs better with larger datasets.  
    - **Performance Metrics**:  
        - **Accuracy**: The proportion of correctly classified instances.  
        - **Precision & Recall**: Useful for imbalanced datasets.  
        - **F1 Score**: Harmonic mean of precision and recall.  
        - **ROC-AUC Score**: Measures how well the model distinguishes between classes.  
    """)

if __name__ == '__main__':
    main()