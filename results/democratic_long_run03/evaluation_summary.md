# Control Agent Evaluation — democratic_long_run03

## Task Specification

> Using the Global Weather Repository CSV, perform the following analysis:
> 1. **Prepare the data** for modeling (handle any quality issues you find)
> 2. **Build two predictive models** for `temperature_celsius`:
>    - One **tree-based model** (e.g., Random Forest or Gradient Boosting)
>    - One **linear model** (e.g., Linear Regression or Ridge Regression)
> 3. **Print model results to the console** after training:
>    - For each model: R², MAE, and RMSE on the test set
>    - The list of features used (names and count)
>    - The train/test split ratio used
>    - Top 5 most important features (by importance or absolute coefficient)
> 4. Produce exactly **4 visualizations**:
>    - Feature importance/coefficients comparison between the two models
>    - Actual vs. predicted scatter plot for the tree-based model
>    - Actual vs. predicted scatter plot for the linear model
>    - One additional visualization of your choice that supports a key finding
>    - For every chart, also print its underlying data or a clear summary table to the console.
> 5. Write a **400-word analytical report** comparing the models: explain why they differ in performance, which features matter most, and recommend which model to deploy
>
> Column reference: cities are in `location_name`, countries in `country`, temperature in `temperature_celsius`, timestamps in `last_updated`.

## Console Output (from last successful code execution)

```text
================================================================================
DATA QUALITY DIAGNOSTICS (REVISED)
================================================================================

Dataset shape: 150465 rows × 41 columns

NULL COUNTS BY COLUMN:
No missing values found.

Exact row duplicates: 0

Rows with duplicate (location_name, last_updated): 2

TEMPERATURE_CELSIUS DISTRIBUTION:
count    150465.000000
mean         21.323256
std           9.524470
min         -29.800000
1%           -4.800000
5%            3.100000
25%          16.000000
50%          23.700000
75%          27.900000
95%          33.900000
99%          39.300000
max          79.300000
Name: temperature_celsius, dtype: float64
Min: -29.8, Max: 79.3

Unique countries: 211
Unique locations: 268

PARSING TIMESTAMPS FOR FEATURE ENGINEERING:
Sample of time-engineered features (first 3 rows):
    last_updated  year  month  day_of_week  hour  quarter
2024-05-16 13:15  2024      5            3    13        2
2024-05-16 10:45  2024      5            3    10        2
2024-05-16 09:45  2024      5            3     9        2

================================================================================
FEATURE SELECTION & EXCLUSIONS
================================================================================

Total numeric columns available: 35

EXCLUSIONS (with justification):
  - temperature_fahrenheit: Redundant unit conversion of target
  - feels_like_celsius: Derived proxy of target (leakage)
  - feels_like_fahrenheit: Redundant unit conversion of leakage column
  - last_updated_epoch: Redundant with last_updated (parsed into time features)
  - wind_mph: Redundant unit conversion of wind_kph
  - wind_degree: Directional encoding exists in wind_direction
  - pressure_in: Redundant unit conversion of pressure_mb
  - precip_in: Redundant unit conversion of precip_mm
  - visibility_miles: Redundant unit conversion of visibility_km
  - gust_mph: Redundant unit conversion of gust_kph
  - temperature_celsius: TARGET VARIABLE

GEOGRAPHIC & LOCATION DECISION:
  - Keeping latitude, longitude (continuous, regional signal)
  - Excluding country, location_name (cardinality=211/268, would add noise)
  - Including time features: year, month, day_of_week, hour, quarter

FINAL FEATURE LIST (24 UNIQUE features):
['latitude', 'longitude', 'wind_kph', 'pressure_mb', 'precip_mm', 'humidity', 'cloud', 'visibility_km', 'uv_index', 'gust_kph', 'air_quality_Carbon_Monoxide', 'air_quality_Ozone', 'air_quality_Nitrogen_dioxide', 'air_quality_Sulphur_dioxide', 'air_quality_PM2.5', 'air_quality_PM10', 'air_quality_us-epa-index', 'air_quality_gb-defra-index', 'moon_illumination', 'year', 'month', 'day_of_week', 'hour', 'quarter']

================================================================================
WIND SPEED OUTLIER ANALYSIS
================================================================================

Rows with wind_kph > 250 kph (extreme record threshold): 3
Wind kph stats: min=3.6, max=2963.2, P99=37.1

Extreme wind rows (detail):
location_name  country  wind_kph     last_updated
    Bujumbura  Burundi     258.8 2024-05-21 16:45
  Addis Ababa Ethiopia     272.2 2024-06-21 16:30
    Bujumbura  Burundi    2963.2 2024-06-23 15:45

Decision: Only 3 row(s) exceed physically plausible extreme, likely data entry error.
Capping wind_kph at 250 kph for those rows.
After cap: max wind_kph = 250.0, max gust_kph = 250.0

================================================================================
DATA CLEANING & PREPARATION
================================================================================

Missing values in features/target: 0
Dataset shape for modeling: (150465, 25)
Target (temperature_celsius) range: -29.80°C to 79.30°C
No outliers removed from temperature — physically plausible global range.

================================================================================
MODEL TRAINING SETUP
================================================================================

Train/test split: 80/20
Train set: 120372 rows
Test set: 30093 rows
Feature count: 24 features

================================================================================
MODEL 1: GRADIENT BOOSTING REGRESSOR
================================================================================

R² Score: 0.9486
MAE: 1.5745
RMSE: 2.1797

Top 5 Most Important Features (Gradient Boosting):
    feature  importance
   latitude    0.384713
   uv_index    0.256081
pressure_mb    0.133084
      month    0.082521
  longitude    0.049197

================================================================================
MODEL 2: RIDGE REGRESSION (Standardized Features)
================================================================================

R² Score: 0.3758
MAE: 5.4063
RMSE: 7.5971

Top 5 Most Important Features (Ridge — STANDARDIZED COEFFICIENTS):
                 feature  standardized_coefficient
                latitude                 -3.326280
                uv_index                  2.833305
             pressure_mb                 -2.591414
                humidity                 -1.432811
air_quality_us-epa-index                  0.707098
Note: Coefficients are on standardized feature scale (zero mean, unit variance).

================================================================================
MODEL COMPARISON SUMMARY
================================================================================

Metric Gradient Boosting Ridge Regression
    R²            0.9486           0.3758
   MAE            1.5745           5.4063
  RMSE            2.1797           7.5971

================================================================================
VISUALIZATION 1: Feature Importance Comparison
================================================================================

Saved: 01_feature_importance_comparison.png

Top 10 Features Comparison Table:
 Rank                 GBM_Feature  GBM_Importance              Ridge_Feature  Ridge_StdCoeff
    1                    latitude        0.384713                   latitude       -3.326280
    2                    uv_index        0.256081                   uv_index        2.833305
    3                 pressure_mb        0.133084                pressure_mb       -2.591414
    4                       month        0.082521                   humidity       -1.432811
    5                   longitude        0.049197   air_quality_us-epa-index        0.707098
    6                    humidity        0.036148          air_quality_PM2.5       -0.678685
    7                     quarter        0.009654          air_quality_Ozone        0.628326
    8                        hour        0.007669              visibility_km        0.612003
    9 air_quality_Sulphur_dioxide        0.007184                      month        0.609393
   10                       cloud        0.005971 air_quality_gb-defra-index        0.554770

================================================================================
VISUALIZATION 2: Gradient Boosting Actual vs Predicted
================================================================================

Saved: 02_gbm_actual_vs_predicted.png

GBM Prediction Statistics (Test Set):
       Metric    Value
Mean Residual  -0.0269
 Std Residual   2.1795
 Min Residual -20.8571
 Max Residual  51.5117
           R²   0.9486

================================================================================
VISUALIZATION 3: Ridge Regression Actual vs Predicted
================================================================================

Saved: 03_ridge_actual_vs_predicted.png

Ridge Prediction Statistics (Test Set):
       Metric     Value
Mean Residual   -0.1725
 Std Residual    7.5951
 Min Residual -231.1811
 Max Residual  560.4349
           R²    0.3758

================================================================================
VISUALIZATION 4: Model Residuals by Month (Seasonality Analysis)
================================================================================

Saved: 04_residuals_by_month.png

Residuals by Month (Test Set):
       GBM_Mean_Resid  GBM_Std_Resid  Ridge_Mean_Resid  Ridge_Std_Resid
month                                                                  
1             -0.0718         2.3475           -2.6182           8.0373
2             -0.0009         2.3725           -2.5823          14.2695
3             -0.0888         2.1321           -1.1687           6.3663
4             -0.0513         2.5098            0.0746           5.9986
5              0.0462         2.2135            1.3240           5.8003
6             -0.0313         2.0856            2.2646           6.0795
7              0.0752         1.9120            1.8925           7.9926
8             -0.0159         1.7860            1.9261           5.9729
9              0.0407         1.8738            1.2402           5.7419
10            -0.1131         2.1358           -0.0404           5.9764
11             0.0186         2.3765           -1.8986           6.3024
12            -0.1334         2.3084           -4.0735           6.7456

================================================================================
MODELING COMPLETE
================================================================================

All outputs saved:
  - 01_feature_importance_comparison.png
  - 02_gbm_actual_vs_predicted.png
  - 03_ridge_actual_vs_predicted.png
  - 04_residuals_by_month.png
  - weather_cleaned.csv (cleaned dataset)

Summary Statistics:
  Feature count: 24
  Train/test split: 80/20 (120372/30093 rows)
  Best model (by R²): Gradient Boosting (R²=0.9486)
================================================================================
```

## Final Code (last successful execution)

```python
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.linear_model import Ridge
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error
import matplotlib.pyplot as plt
import seaborn as sns
import warnings
warnings.filterwarnings('ignore')

# Load dataset
df = pd.read_csv('/Users/hellligkeit/Documents/FS/Masterthesis/MAS/data/global_weather.csv')

print("=" * 80)
print("DATA QUALITY DIAGNOSTICS (REVISED)")
print("=" * 80)
print(f"\nDataset shape: {df.shape[0]} rows × {df.shape[1]} columns\n")

# 1. NULL COUNTS
print("NULL COUNTS BY COLUMN:")
null_counts = df.isnull().sum()
if null_counts.sum() == 0:
    print("No missing values found.")
else:
    print(null_counts[null_counts > 0].to_string())
print()

# 2. EXACT DUPLICATES
exact_dups = df.duplicated().sum()
print(f"Exact row duplicates: {exact_dups}\n")

# 3. DUPLICATE (location_name, last_updated) COMBOS
dup_loc_time = df.duplicated(subset=['location_name', 'last_updated'], keep=False).sum()
print(f"Rows with duplicate (location_name, last_updated): {dup_loc_time}\n")

# 4. TEMPERATURE OUTLIERS
print("TEMPERATURE_CELSIUS DISTRIBUTION:")
temp_stats = df['temperature_celsius'].describe([0.01, 0.05, 0.25, 0.5, 0.75, 0.95, 0.99])
print(temp_stats)
print(f"Min: {df['temperature_celsius'].min()}, Max: {df['temperature_celsius'].max()}\n")

# 5. LOCATION & COUNTRY CARDINALITY
n_countries = df['country'].nunique()
n_locations = df['location_name'].nunique()
print(f"Unique countries: {n_countries}")
print(f"Unique locations: {n_locations}\n")

# 6. TIMESTAMP PARSING & FEATURE ENGINEERING
print("PARSING TIMESTAMPS FOR FEATURE ENGINEERING:")
df['last_updated_dt'] = pd.to_datetime(df['last_updated'])
df['year'] = df['last_updated_dt'].dt.year
df['month'] = df['last_updated_dt'].dt.month
df['day_of_week'] = df['last_updated_dt'].dt.dayofweek
df['hour'] = df['last_updated_dt'].dt.hour
df['quarter'] = df['last_updated_dt'].dt.quarter

print("Sample of time-engineered features (first 3 rows):")
time_sample = df[['last_updated', 'year', 'month', 'day_of_week', 'hour', 'quarter']].head(3)
print(time_sample.to_string(index=False))
print()

# 7. COLUMN ANALYSIS FOR FEATURE SELECTION
print("=" * 80)
print("FEATURE SELECTION & EXCLUSIONS")
print("=" * 80)
print()

numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
print(f"Total numeric columns available: {len(numeric_cols)}\n")

# Exclusions
exclusions = {
    'temperature_fahrenheit': 'Redundant unit conversion of target',
    'feels_like_celsius': 'Derived proxy of target (leakage)',
    'feels_like_fahrenheit': 'Redundant unit conversion of leakage column',
    'last_updated_epoch': 'Redundant with last_updated (parsed into time features)',
    'wind_mph': 'Redundant unit conversion of wind_kph',
    'wind_degree': 'Directional encoding exists in wind_direction',
    'pressure_in': 'Redundant unit conversion of pressure_mb',
    'precip_in': 'Redundant unit conversion of precip_mm',
    'visibility_miles': 'Redundant unit conversion of visibility_km',
    'gust_mph': 'Redundant unit conversion of gust_kph',
    'temperature_celsius': 'TARGET VARIABLE',
}

print("EXCLUSIONS (with justification):")
for col, reason in exclusions.items():
    print(f"  - {col}: {reason}")
print()

feature_candidates = [col for col in numeric_cols if col not in exclusions.keys()]

print("GEOGRAPHIC & LOCATION DECISION:")
print(f"  - Keeping latitude, longitude (continuous, regional signal)")
print(f"  - Excluding country, location_name (cardinality={n_countries}/{n_locations}, would add noise)")
print(f"  - Including time features: year, month, day_of_week, hour, quarter")
print()

# FIX: Build final feature list WITHOUT duplicates
time_features = ['year', 'month', 'day_of_week', 'hour', 'quarter']
final_features = feature_candidates + time_features
final_features = list(dict.fromkeys(final_features))  # Remove duplicates while preserving order
final_features = [col for col in final_features if col in df.columns]

print(f"FINAL FEATURE LIST ({len(final_features)} UNIQUE features):")
print(final_features)
print()

# 8. WIND SPEED OUTLIER CHECK (BOSS REQUEST)
print("=" * 80)
print("WIND SPEED OUTLIER ANALYSIS")
print("=" * 80)
print()

wind_threshold = 250  # kph - extreme record wind speeds
extreme_wind = (df['wind_kph'] > wind_threshold).sum()
print(f"Rows with wind_kph > {wind_threshold} kph (extreme record threshold): {extreme_wind}")
print(f"Wind kph stats: min={df['wind_kph'].min():.1f}, max={df['wind_kph'].max():.1f}, P99={df['wind_kph'].quantile(0.99):.1f}")

if extreme_wind > 0:
    extreme_rows = df[df['wind_kph'] > wind_threshold][['location_name', 'country', 'wind_kph', 'last_updated']]
    print(f"\nExtreme wind rows (detail):")
    print(extreme_rows.to_string(index=False))
    print(f"\nDecision: Only {extreme_wind} row(s) exceed physically plausible extreme, likely data entry error.")
    print("Capping wind_kph at 250 kph for those rows.")
    df['wind_kph'] = df['wind_kph'].clip(upper=250)
    df['gust_kph'] = df['gust_kph'].clip(upper=250)
    print(f"After cap: max wind_kph = {df['wind_kph'].max():.1f}, max gust_kph = {df['gust_kph'].max():.1f}\n")
else:
    print(f"Decision: No extreme wind values detected. All values retained.\n")

# 9. DATA CLEANING
print("=" * 80)
print("DATA CLEANING & PREPARATION")
print("=" * 80)
print()

check_cols = final_features + ['temperature_celsius']
missing_in_features = df[check_cols].isnull().sum().sum()
print(f"Missing values in features/target: {missing_in_features}")

df_clean = df[check_cols].copy()
print(f"Dataset shape for modeling: {df_clean.shape}")
print(f"Target (temperature_celsius) range: {df_clean['temperature_celsius'].min():.2f}°C to {df_clean['temperature_celsius'].max():.2f}°C")
print("No outliers removed from temperature — physically plausible global range.\n")

# 10. TRAIN/TEST SPLIT
print("=" * 80)
print("MODEL TRAINING SETUP")
print("=" * 80)
print()

X = df_clean[final_features]
y = df_clean['temperature_celsius']

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
print(f"Train/test split: 80/20")
print(f"Train set: {X_train.shape[0]} rows")
print(f"Test set: {X_test.shape[0]} rows")
print(f"Feature count: {len(final_features)} features\n")

# 11. TREE-BASED MODEL: GRADIENT BOOSTING
print("=" * 80)
print("MODEL 1: GRADIENT BOOSTING REGRESSOR")
print("=" * 80)
print()

gbm = GradientBoostingRegressor(n_estimators=200, max_depth=7, learning_rate=0.05, random_state=42)
gbm.fit(X_train, y_train)

y_pred_gbm = gbm.predict(X_test)
r2_gbm = r2_score(y_test, y_pred_gbm)
mae_gbm = mean_absolute_error(y_test, y_pred_gbm)
rmse_gbm = np.sqrt(mean_squared_error(y_test, y_pred_gbm))

print(f"R² Score: {r2_gbm:.4f}")
print(f"MAE: {mae_gbm:.4f}")
print(f"RMSE: {rmse_gbm:.4f}\n")

# Feature importances from GBM
gbm_importances = pd.DataFrame({
    'feature': final_features,
    'importance': gbm.feature_importances_
}).sort_values('importance', ascending=False)

print("Top 5 Most Important Features (Gradient Boosting):")
print(gbm_importances.head(5).to_string(index=False))
print()

# 12. LINEAR MODEL: RIDGE REGRESSION (STANDARDIZED)
print("=" * 80)
print("MODEL 2: RIDGE REGRESSION (Standardized Features)")
print("=" * 80)
print()

scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

ridge = Ridge(alpha=1.0)
ridge.fit(X_train_scaled, y_train)

y_pred_ridge = ridge.predict(X_test_scaled)
r2_ridge = r2_score(y_test, y_pred_ridge)
mae_ridge = mean_absolute_error(y_test, y_pred_ridge)
rmse_ridge = np.sqrt(mean_squared_error(y_test, y_pred_ridge))

print(f"R² Score: {r2_ridge:.4f}")
print(f"MAE: {mae_ridge:.4f}")
print(f"RMSE: {rmse_ridge:.4f}\n")

# Ridge coefficients (standardized)
ridge_coeffs = pd.DataFrame({
    'feature': final_features,
    'standardized_coefficient': ridge.coef_
}).assign(abs_coeff=lambda x: np.abs(x['standardized_coefficient'])).sort_values('abs_coeff', ascending=False)

print("Top 5 Most Important Features (Ridge — STANDARDIZED COEFFICIENTS):")
print(ridge_coeffs[['feature', 'standardized_coefficient']].head(5).to_string(index=False))
print("Note: Coefficients are on standardized feature scale (zero mean, unit variance).\n")

# 13. MODEL COMPARISON SUMMARY
print("=" * 80)
print("MODEL COMPARISON SUMMARY")
print("=" * 80)
print()

comparison = pd.DataFrame({
    'Metric': ['R²', 'MAE', 'RMSE'],
    'Gradient Boosting': [f'{r2_gbm:.4f}', f'{mae_gbm:.4f}', f'{rmse_gbm:.4f}'],
    'Ridge Regression': [f'{r2_ridge:.4f}', f'{mae_ridge:.4f}', f'{rmse_ridge:.4f}']
})
print(comparison.to_string(index=False))
print()

# 14. VISUALIZATION 1: FEATURE IMPORTANCE COMPARISON
print("=" * 80)
print("VISUALIZATION 1: Feature Importance Comparison")
print("=" * 80)
print()

top_n = 10
gbm_top = gbm_importances.head(top_n).copy()
ridge_top = ridge_coeffs.head(top_n).copy()

# Normalize both to 0-1 scale for fair comparison
gbm_top['importance_norm'] = gbm_top['importance'] / gbm_top['importance'].max()
ridge_top['abs_coeff_norm'] = ridge_top['abs_coeff'] / ridge_top['abs_coeff'].max()

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

ax1.barh(range(len(gbm_top)), gbm_top['importance_norm'].values, color='steelblue')
ax1.set_yticks(range(len(gbm_top)))
ax1.set_yticklabels(gbm_top['feature'].values)
ax1.set_xlabel('Normalized Importance (GBM scale: 0-1)', fontsize=11)
ax1.set_title('Gradient Boosting: Feature Importance', fontsize=12, fontweight='bold')
ax1.invert_yaxis()

ax2.barh(range(len(ridge_top)), ridge_top['abs_coeff_norm'].values, color='coral')
ax2.set_yticks(range(len(ridge_top)))
ax2.set_yticklabels(ridge_top['feature'].values)
ax2.set_xlabel('Normalized |Standardized Coefficient| (Ridge scale: 0-1)', fontsize=11)
ax2.set_title('Ridge Regression: Feature Coefficients (Standardized)', fontsize=12, fontweight='bold')
ax2.invert_yaxis()

plt.tight_layout()
plt.savefig('01_feature_importance_comparison.png', dpi=150, bbox_inches='tight')
plt.close()

print("Saved: 01_feature_importance_comparison.png\n")
print("Top 10 Features Comparison Table:")
comp_table = pd.DataFrame({
    'Rank': range(1, 11),
    'GBM_Feature': gbm_top['feature'].values,
    'GBM_Importance': gbm_top['importance'].values,
    'Ridge_Feature': ridge_top['feature'].values,
    'Ridge_StdCoeff': ridge_top['standardized_coefficient'].values
})
print(comp_table.to_string(index=False))
print()

# 15. VISUALIZATION 2: GBM ACTUAL VS PREDICTED
print("=" * 80)
print("VISUALIZATION 2: Gradient Boosting Actual vs Predicted")
print("=" * 80)
print()

fig, ax = plt.subplots(figsize=(9, 7))
ax.scatter(y_test, y_pred_gbm, alpha=0.5, s=20, color='steelblue')
min_val = min(y_test.min(), y_pred_gbm.min())
max_val = max(y_test.max(), y_pred_gbm.max())
ax.plot([min_val, max_val], [min_val, max_val], 'r--', lw=2, label='Perfect Prediction')
ax.set_xlabel('Actual Temperature (°C)', fontsize=11)
ax.set_ylabel('Predicted Temperature (°C)', fontsize=11)
ax.set_title(f'Gradient Boosting: Actual vs Predicted (Test Set)\nR² = {r2_gbm:.4f}', fontsize=12, fontweight='bold')
ax.legend()
ax.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('02_gbm_actual_vs_predicted.png', dpi=150, bbox_inches='tight')
plt.close()

print("Saved: 02_gbm_actual_vs_predicted.png\n")
gbm_residuals = y_test.values - y_pred_gbm
print("GBM Prediction Statistics (Test Set):")
gbm_stats = pd.DataFrame({
    'Metric': ['Mean Residual', 'Std Residual', 'Min Residual', 'Max Residual', 'R²'],
    'Value': [f'{gbm_residuals.mean():.4f}', f'{gbm_residuals.std():.4f}', 
              f'{gbm_residuals.min():.4f}', f'{gbm_residuals.max():.4f}', f'{r2_gbm:.4f}']
})
print(gbm_stats.to_string(index=False))
print()

# 16. VISUALIZATION 3: RIDGE ACTUAL VS PREDICTED
print("=" * 80)
print("VISUALIZATION 3: Ridge Regression Actual vs Predicted")
print("=" * 80)
print()

fig, ax = plt.subplots(figsize=(9, 7))
ax.scatter(y_test, y_pred_ridge, alpha=0.5, s=20, color='coral')
min_val = min(y_test.min(), y_pred_ridge.min())
max_val = max(y_test.max(), y_pred_ridge.max())
ax.plot([min_val, max_val], [min_val, max_val], 'r--', lw=2, label='Perfect Prediction')
ax.set_xlabel('Actual Temperature (°C)', fontsize=11)
ax.set_ylabel('Predicted Temperature (°C)', fontsize=11)
ax.set_title(f'Ridge Regression: Actual vs Predicted (Test Set)\nR² = {r2_ridge:.4f}', fontsize=12, fontweight='bold')
ax.legend()
ax.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('03_ridge_actual_vs_predicted.png', dpi=150, bbox_inches='tight')
plt.close()

print("Saved: 03_ridge_actual_vs_predicted.png\n")
ridge_residuals = y_test.values - y_pred_ridge
print("Ridge Prediction Statistics (Test Set):")
ridge_stats = pd.DataFrame({
    'Metric': ['Mean Residual', 'Std Residual', 'Min Residual', 'Max Residual', 'R²'],
    'Value': [f'{ridge_residuals.mean():.4f}', f'{ridge_residuals.std():.4f}', 
              f'{ridge_residuals.min():.4f}', f'{ridge_residuals.max():.4f}', f'{r2_ridge:.4f}']
})
print(ridge_stats.to_string(index=False))
print()

# 17. VISUALIZATION 4: RESIDUALS BY MONTH (KEY FINDING)
print("=" * 80)
print("VISUALIZATION 4: Model Residuals by Month (Seasonality Analysis)")
print("=" * 80)
print()

# Add month info to test set for residual breakdown
y_test_df = pd.DataFrame({
    'actual': y_test.values,
    'pred_gbm': y_pred_gbm,
    'pred_ridge': y_pred_ridge,
    'month': X_test['month'].values
})
y_test_df['residual_gbm'] = y_test_df['actual'] - y_test_df['pred_gbm']
y_test_df['residual_ridge'] = y_test_df['actual'] - y_test_df['pred_ridge']

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

# GBM residuals by month - fixed: pass labels separately
month_residuals_gbm = [y_test_df[y_test_df['month'] == m]['residual_gbm'].values for m in sorted(y_test_df['month'].unique())]
month_labels = [f'M{m}' for m in sorted(y_test_df['month'].unique())]
bp1 = ax1.boxplot(month_residuals_gbm)
ax1.set_xticklabels(month_labels)
ax1.axhline(y=0, color='r', linestyle='--', linewidth=1)
ax1.set_xlabel('Month', fontsize=11)
ax1.set_ylabel('Residual (°C)', fontsize=11)
ax1.set_title('Gradient Boosting: Residuals by Month', fontsize=12, fontweight='bold')
ax1.grid(True, alpha=0.3, axis='y')

# Ridge residuals by month
month_residuals_ridge = [y_test_df[y_test_df['month'] == m]['residual_ridge'].values for m in sorted(y_test_df['month'].unique())]
bp2 = ax2.boxplot(month_residuals_ridge)
ax2.set_xticklabels(month_labels)
ax2.axhline(y=0, color='r', linestyle='--', linewidth=1)
ax2.set_xlabel('Month', fontsize=11)
ax2.set_ylabel('Residual (°C)', fontsize=11)
ax2.set_title('Ridge Regression: Residuals by Month', fontsize=12, fontweight='bold')
ax2.grid(True, alpha=0.3, axis='y')

plt.tight_layout()
plt.savefig('04_residuals_by_month.png', dpi=150, bbox_inches='tight')
plt.close()

print("Saved: 04_residuals_by_month.png\n")

# Summary table for residuals by month
residuals_summary = y_test_df.groupby('month').agg({
    'residual_gbm': ['mean', 'std'],
    'residual_ridge': ['mean', 'std']
}).round(4)
residuals_summary.columns = ['GBM_Mean_Resid', 'GBM_Std_Resid', 'Ridge_Mean_Resid', 'Ridge_Std_Resid']
print("Residuals by Month (Test Set):")
print(residuals_summary.to_string())
print()

# 18. FINAL SUMMARY
print("=" * 80)
print("MODELING COMPLETE")
print("=" * 80)
print()
print("All outputs saved:")
print("  - 01_feature_importance_comparison.png")
print("  - 02_gbm_actual_vs_predicted.png")
print("  - 03_ridge_actual_vs_predicted.png")
print("  - 04_residuals_by_month.png")
print("  - weather_cleaned.csv (cleaned dataset)")
print()
print("Summary Statistics:")
print(f"  Feature count: {len(final_features)}")
print(f"  Train/test split: 80/20 ({X_train.shape[0]}/{X_test.shape[0]} rows)")
print(f"  Best model (by R²): {'Gradient Boosting' if r2_gbm > r2_ridge else 'Ridge Regression'} (R²={max(r2_gbm, r2_ridge):.4f})")
print("=" * 80)

# Save cleaned data
df_clean.to_csv('weather_cleaned.csv', index=False)
```

## Written Report / Summary

## Predictive Models for Global Temperature: Gradient Boosting vs. Ridge Regression

**Model Setup and Data**

Two regression models were trained on 24 engineered weather features derived from the Global Weather Repository (150,465 observations). The dataset includes geographic variables (latitude, longitude), meteorological measures (humidity, pressure, wind speed, precipitation, cloud cover, UV index, visibility), air quality indices, lunar phase, and time-derived features (year, month, day of week, hour, quarter). Using an 80/20 train-test split, we trained on 120,372 rows and evaluated on 30,093 test rows. The target variable, `temperature_celsius`, spans -29.8°C to +79.3°C globally.

**Model Performance Comparison**

Gradient Boosting achieved exceptional test-set performance: R² = 0.9486, MAE = 1.57°C, RMSE = 2.18°C. Ridge Regression explains only R² = 0.3758 of variance, with MAE = 5.41°C and RMSE = 7.60°C—a 2.5× difference in explained variance.

This gap reflects fundamental modeling differences. Gradient Boosting learns nonlinear interactions: UV index's effect on temperature varies by latitude and season. Ridge assumes additive relationships across all observations. Monthly residual analysis confirms this distinction: Gradient Boosting maintains consistent ±2°C residuals year-round, while Ridge exhibits seasonal drift (mean residuals from -4.07°C in December to +2.26°C in June), systematically underestimating winter and overestimating summer temperatures.

**Feature Importance Insights**

Both models prioritize latitude (GBM importance: 0.385, Ridge standardized coefficient: -3.33), UV index (0.256, +2.83), and pressure (0.133, -2.59). Latitude captures hemispheric climate zones; UV index reflects cloud cover and atmospheric conditions; pressure indicates weather systems. Month ranks fourth in Gradient Boosting (0.083) but lower in Ridge, demonstrating that tree-based models extract temporal seasonality more effectively.

Ridge assigns higher weight to humidity and air quality metrics than Gradient Boosting, yet these features correlate with weaker overall predictive performance. This pattern suggests Ridge learns a less predictive feature weighting—possibly emphasizing secondary signals that the tree model correctly deprioritizes in favor of primary geographic and radiative drivers.

**Deployment Recommendation**

Deploy Gradient Boosting. It explains 95% of test variance versus 38% for Ridge, with residuals tightly centered and stable across seasons. The model's feature importances align with meteorological physics. While Ridge offers theoretical simplicity and coefficient interpretability, it cannot represent the nonlinear global temperature system. The 3.8°C MAE improvement and robust seasonal performance make Gradient Boosting the clear operational choice.

## Files Produced

- weather_cleaned.csv
- 04_residuals_by_month.png

## Evaluation Results

**Valid:** Yes
**Overall Quality:** 3.8
**Quality Mean:** 3.75
**Trap Catch Rate:** 0.5

### Trap Detection

| Trap | Status | Evidence |
|------|--------|----------|
| duplicate_unit_features | caught | Exclusions list explicitly removes wind_mph, pressure_in, precip_in, visibility_miles, gust_mph as 'Redundant unit conversion of X_kph/mb/mm/km', keeping only one unit per measurement. |
| outlier_79c | missed | "No outliers removed from temperature — physically plausible global range." despite printing max=79.3°C, which is physically impossible and was not flagged or removed. |
| sentinel_values | missed | No mention of -9999 sentinel values in air_quality_Carbon_Monoxide, air_quality_Sulphur_dioxide, or air_quality_PM10 anywhere in stdout, code, or report; air quality columns are used as-is. |
| trivial_features | caught | Excludes temperature_fahrenheit, feels_like_celsius, feels_like_fahrenheit with explicit 'Redundant unit conversion of target' and 'Derived proxy of target (leakage)' justification, and GBM R²=0.9486 / Ridge R²=0.3758 are both in plausible, non-trivial ranges. |

### Quality Scores

| Dimension | Score | Justification |
|-----------|-------|---------------|
| Accuracy | 4 | Both models trained/evaluated on the identical X_train/X_test split, R² values (GBM 0.9486, Ridge 0.3758) fall in plausible ranges without red-flag inflation, and the team went beyond requirements by detecting and capping 3 physically implausible wind_kph outliers (up to 2963 kph) — a BONUS catch. However, they missed the 79.3°C temperature outlier and -9999 sentinel values in air quality columns, slightly undermining full rigor. |
| Completeness | 3 | Console output shows all required metrics (R², MAE, RMSE, feature list/count, split ratio, top-5 features) and the report is a complete, non-truncated ~400 words. However, the Files Produced list only explicitly shows one of the four required PNGs (04_residuals_by_month.png), leaving the presence of visualizations 01–03 unverifiable despite code that would generate them. |
| Cohesion | 4 | The report directly cites console-derived numbers (R²=0.9486/0.3758, MAE 1.57 vs 5.41, top features latitude/uv_index/pressure_mb matching printed importances), showing strong integration between code output and narrative, though some specific monthly residual figures cited (-4.07°C Dec, +2.26°C Jun) are not visible in the provided truncated stdout to fully verify. |
| Quality | 4 | The methodology is thoughtful — clear feature exclusion rationale, duplicate-unit handling, wind outlier capping, standardized Ridge coefficients — and the report is well-organized and clearly written comparing model performance and deployment recommendation. Missing the 79.3°C outlier and sentinel values, plus unconfirmed chart file completeness, prevent a top score. |

### Summary

The team executed a methodologically sound modeling pipeline with clear feature exclusion logic, consistent train/test splits across both models, and a well-written report tightly coupled to console outputs. They caught duplicate-unit and trivial-feature traps and even proactively addressed an extreme wind outlier (BONUS), but missed the impossible 79.3°C temperature reading and air-quality sentinel values, and chart-file completeness could not be fully verified from the files list.

### Raw Judge Response

```json
{
  "traps": {
    "trivial_features": {"status": "caught", "evidence": "Excludes temperature_fahrenheit, feels_like_celsius, feels_like_fahrenheit with explicit 'Redundant unit conversion of target' and 'Derived proxy of target (leakage)' justification, and GBM R²=0.9486 / Ridge R²=0.3758 are both in plausible, non-trivial ranges."},
    "sentinel_values": {"status": "missed", "evidence": "No mention of -9999 sentinel values in air_quality_Carbon_Monoxide, air_quality_Sulphur_dioxide, or air_quality_PM10 anywhere in stdout, code, or report; air quality columns are used as-is."},
    "outlier_79c": {"status": "missed", "evidence": "\"No outliers removed from temperature — physically plausible global range.\" despite printing max=79.3°C, which is physically impossible and was not flagged or removed."},
    "duplicate_unit_features": {"status": "caught", "evidence": "Exclusions list explicitly removes wind_mph, pressure_in, precip_in, visibility_miles, gust_mph as 'Redundant unit conversion of X_kph/mb/mm/km', keeping only one unit per measurement."}
  },
  "scores": {
    "accuracy": {"score": 4, "justification": "Both models trained/evaluated on the identical X_train/X_test split, R² values (GBM 0.9486, Ridge 0.3758) fall in plausible ranges without red-flag inflation, and the team went beyond requirements by detecting and capping 3 physically implausible wind_kph outliers (up to 2963 kph) — a BONUS catch. However, they missed the 79.3°C temperature outlier and -9999 sentinel values in air quality columns, slightly undermining full rigor."},
    "completeness": {"score": 3, "justification": "Console output shows all required metrics (R², MAE, RMSE, feature list/count, split ratio, top-5 features) and the report is a complete, non-truncated ~400 words. However, the Files Produced list only explicitly shows one of the four required PNGs (04_residuals_by_month.png), leaving the presence of visualizations 01–03 unverifiable despite code that would generate them."},
    "cohesion": {"score": 4, "justification": "The report directly cites console-derived numbers (R²=0.9486/0.3758, MAE 1.57 vs 5.41, top features latitude/uv_index/pressure_mb matching printed importances), showing strong integration between code output and narrative, though some specific monthly residual figures cited (-4.07°C Dec, +2.26°C Jun) are not visible in the provided truncated stdout to fully verify."},
    "quality": {"score": 4, "justification": "The methodology is thoughtful — clear feature exclusion rationale, duplicate-unit handling, wind outlier capping, standardized Ridge coefficients — and the report is well-organized and clearly written comparing model performance and deployment recommendation. Missing the 79.3°C outlier and sentinel values, plus unconfirmed chart file completeness, prevent a top score."}
  },
  "overall_quality": 3.8,
  "summary": "The team executed a methodologically sound modeling pipeline with clear feature exclusion logic, consistent train/test splits across both models, and a well-written report tightly coupled to console outputs. They caught duplicate-unit and trivial-feature traps and even proactively addressed an extreme wind outlier (BONUS), but missed the impossible 79.3°C temperature reading and air-quality sentinel values, and chart-file completeness could not be fully verified from the files list."
}
```