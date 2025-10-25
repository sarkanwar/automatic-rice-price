
from __future__ import annotations
import pandas as pd, numpy as np
from statsmodels.tsa.statespace.sarimax import SARIMAX
from sklearn.metrics import mean_absolute_error, mean_squared_error
from xgboost import XGBRegressor

def fit_sarimax(series: pd.Series, order=(1,1,1), seasonal_order=(0,1,1,7)):
    model = SARIMAX(series, order=order, seasonal_order=seasonal_order,
                    enforce_stationarity=False, enforce_invertibility=False)
    return model.fit(disp=False)

def build_features(s: pd.Series) -> pd.DataFrame:
    df = pd.DataFrame({'price': s})
    df['ret'] = df['price'].pct_change()
    for win in [3,7,14,30]:
        df[f'sma_{win}'] = df['price'].rolling(win).mean()
        df[f'ema_{win}'] = df['price'].ewm(span=win, adjust=False).mean()
        df[f'vol_{win}'] = df['ret'].rolling(win).std()
    for l in [1,2,3,7,14,30]:
        df[f'lag_{l}'] = df['price'].shift(l)
    return df

def train_and_forecast(df: pd.DataFrame, horizons=[7,30,180]):
    df = df.copy()
    df['Date'] = pd.to_datetime(df['Date'])
    df = df.sort_values('Date').set_index('Date')
    s = df['Price'].astype(float).asfreq('D').ffill().rename('price')

    feats = build_features(s).dropna()
    y = feats['price']; X = feats.drop(columns=['price'])

    cutoff = y.index.max() - pd.Timedelta(days=60)
    y_train, y_test = y[y.index <= cutoff], y[y.index > cutoff]
    X_train, X_test = X.loc[y_train.index], X.loc[y_test.index]

    sar = fit_sarimax(y_train)
    base_pred_test = sar.get_forecast(steps=len(y_test)).predicted_mean
    base_pred_test.index = y_test.index

    xgb = XGBRegressor(n_estimators=300, max_depth=4, learning_rate=0.06, subsample=0.9,
                       colsample_bytree=0.9, objective="reg:squarederror", random_state=42)
    resid_train = (y_train - sar.fittedvalues.reindex(y_train.index).ffill()).dropna()
    xgb.fit(X_train.loc[resid_train.index], resid_train.values)
    resid_pred_test = pd.Series(xgb.predict(X_test), index=X_test.index)

    metrics = {
        "MAE": float(mean_absolute_error(y_test, (base_pred_test + resid_pred_test).reindex(y_test.index))),
        "RMSE": float(mean_squared_error(y_test, (base_pred_test + resid_pred_test).reindex(y_test.index), squared=False)),
    }

    # Refit SARIMAX on full history
    sar_full = fit_sarimax(s)
    max_h = max(horizons)
    sar_fore = sar_full.get_forecast(steps=max_h)
    base_mean = sar_fore.predicted_mean
    conf = sar_fore.conf_int(alpha=0.05)
    lower, upper = conf.iloc[:,0], conf.iloc[:,1]
    fut_idx = pd.date_range(s.index.max() + pd.Timedelta(days=1), periods=max_h, freq='D')

    # Residual model on full history
    base_fit = sar_full.fittedvalues.reindex(s.index).ffill()
    resid_full = (s - base_fit).dropna()
    xgb.fit(build_features(s).dropna().drop(columns=['price']).loc[resid_full.index], resid_full.values)

    fut_feats = build_features(pd.concat([s, pd.Series([s.iloc[-1]]*max_h, index=fut_idx)]))\
        .loc[fut_idx].drop(columns=['price'], errors='ignore').fillna(method='ffill').fillna(method='bfill')
    resid = pd.Series(xgb.predict(fut_feats), index=fut_idx)

    out = {}
    for h in horizons:
        idx = fut_idx[:h]
        out[h] = pd.DataFrame({
            "date": idx,
            "forecast": base_mean.loc[idx].values + resid.loc[idx].values,
            "lower_95": lower.loc[idx].values,
            "upper_95": upper.loc[idx].values,
        })
    return metrics, out
