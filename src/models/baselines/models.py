from sklearn.ensemble import RandomForestClassifier
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler


def build_baselines(seed=42):
    return {"Logistic Regression": make_pipeline(StandardScaler(), LogisticRegression(max_iter=500)),
            "Random Forest": RandomForestClassifier(n_estimators=100, random_state=seed, n_jobs=-1)}


def build_regression_baselines(seed=42):
    return {
        "Linear Regression": make_pipeline(StandardScaler(), LinearRegression()),
        "Random Forest Regressor": RandomForestRegressor(
            n_estimators=100, random_state=seed, n_jobs=-1
        ),
    }
