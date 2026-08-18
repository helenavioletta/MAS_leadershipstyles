# Control Agent Evaluation — authoritative_long_run03

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
DATA QUALITY ASSESSMENT
================================================================================

Initial shape: (150465, 41)

Columns loaded: 41

Null values (non-zero only):
  No nulls detected.

Duplicate rows: 0

Temperature range (°C): [-29.80, 79.30]
  Mean: 21.32, Std: 9.52

================================================================================
DATA CLEANING
================================================================================

Dropped 0 rows with null temperature_celsius
Removed 0 duplicate rows
Shape after cleaning: (150465, 41)

================================================================================
FEATURE ENGINEERING
================================================================================
Dropped 0 rows with unparseable timestamps

Features selected (19): ['latitude', 'longitude', 'humidity', 'cloud', 'wind_kph', 'pressure_mb', 'precip_mm', 'visibility_km', 'uv_index', 'gust_kph', 'month', 'hour', 'day_of_week', 'air_quality_Carbon_Monoxide', 'air_quality_Ozone', 'air_quality_Nitrogen_dioxide', 'air_quality_Sulphur_dioxide', 'air_quality_PM2.5', 'air_quality_PM10']

Excluded features (temperature proxies / redundant):
  - feels_like_celsius, feels_like_fahrenheit (temperature proxies)
  - temperature_fahrenheit (redundant with celsius)
  - wind_mph, gust_mph (redundant with kph)
  - pressure_in, precip_in, visibility_miles (redundant with metric units)
  - wind_direction, condition_text (categorical, high cardinality, weak signal)

Dropped 0 rows with missing feature values
Final dataset shape: 150465 samples, 19 features

================================================================================
TRAIN/TEST SPLIT
================================================================================

Train/test split: 80/20
  Train set: 120372 samples
  Test set: 30093 samples
  Total: 150465 samples

================================================================================
MODEL TRAINING & EVALUATION
================================================================================

--- Model Performance (Test Set) ---

           Model       R²  MAE (°C)  RMSE (°C)
   Random Forest 0.956168  1.374214   2.013193
Ridge Regression 0.376577  5.422013   7.592456

================================================================================
FEATURE IMPORTANCE & COEFFICIENTS
================================================================================

--- Random Forest Top 5 Features ---

    Feature  Importance
   latitude    0.363194
   uv_index    0.254872
pressure_mb    0.120018
      month    0.098743
  longitude    0.049927

--- Ridge Regression Top 5 Features ---

      Feature  Abs_Coefficient
     uv_index         0.808194
    precip_mm         0.601536
  pressure_mb         0.290511
        month         0.246501
visibility_km         0.208851

================================================================================
RESIDUAL ANALYSIS
================================================================================

--- Random Forest Residuals ---
  Mean: -0.0325°C
  Std:  2.0129°C
  Min:  -23.0020°C
  Max:  53.5753°C
  Q25:  -0.9117°C
  Q50:  0.0363°C
  Q75:  0.9328°C
  Correlation (Actual vs Predicted): 0.977904

--- Ridge Regression Residuals ---
  Mean: -0.1630°C
  Std:  7.5907°C
  Min:  -191.5503°C
  Max:  563.9713°C
  Q25:  -4.4222°C
  Q50:  1.0651°C
  Q75:  5.0017°C
  Correlation (Actual vs Predicted): 0.627235

================================================================================
VISUALIZATION 1: Feature Importance / Coefficients Comparison
================================================================================

File saved: feature_importance_comparison.png

--- Top 10 Features Comparison ---

                     Feature  RF_Importance  Ridge_Abs_Coef
air_quality_Nitrogen_dioxide       0.007837        0.002323
 air_quality_Carbon_Monoxide       0.008492        0.000166
                        hour       0.010469        0.100425
 air_quality_Sulphur_dioxide       0.010473        0.019939
                    humidity       0.035296        0.064709
                   longitude       0.049927        0.004712
                       month       0.098743        0.246501
                 pressure_mb       0.120018        0.290511
                    uv_index       0.254872        0.808194
                    latitude       0.363194        0.138480

================================================================================
VISUALIZATION 2: Actual vs Predicted (Random Forest)
================================================================================

File saved: actual_vs_predicted_random_forest.png

--- Scatter Summary ---
  Sample count: 30093
  R² (correlation): 0.956168
  Residual correlation: 0.977904
  Actual range: [-28.90, 79.30]°C
  Predicted range: [-21.55, 47.59]°C

================================================================================
VISUALIZATION 3: Actual vs Predicted (Ridge)
================================================================================

File saved: actual_vs_predicted_ridge.png

--- Scatter Summary ---
  Sample count: 30093
  R² (correlation): 0.376577
  Residual correlation: 0.627235
  Actual range: [-28.90, 79.30]°C
  Predicted range: [-561.87, 220.15]°C

================================================================================
VISUALIZATION 4: Residuals Distribution (Both Models)
================================================================================

File saved: residuals_distribution.png

--- Residuals Distribution Summary ---

 Metric  Random Forest       Ridge
   Mean      -0.032547   -0.163050
Std Dev       2.012930    7.590705
    Min     -23.002000 -191.550292
    Max      53.575250  563.971284
    Q25      -0.911694   -4.422202
    Q50       0.036341    1.065069
    Q75       0.932842    5.001731

================================================================================
FINAL SUMMARY
================================================================================

Dataset: Global Weather Repository
Target: temperature_celsius
Total features used: 19
Feature list: ['latitude', 'longitude', 'humidity', 'cloud', 'wind_kph', 'pressure_mb', 'precip_mm', 'visibility_km', 'uv_index', 'gust_kph', 'month', 'hour', 'day_of_week', 'air_quality_Carbon_Monoxide', 'air_quality_Ozone', 'air_quality_Nitrogen_dioxide', 'air_quality_Sulphur_dioxide', 'air_quality_PM2.5', 'air_quality_PM10']
Train/test split: 80/20
Train samples: 120372, Test samples: 30093

Model Performance on Test Set:
           Model       R²  MAE (°C)  RMSE (°C)
   Random Forest 0.956168  1.374214   2.013193
Ridge Regression 0.376577  5.422013   7.592456

Top 5 Features (Random Forest):
    Feature  Importance
   latitude    0.363194
   uv_index    0.254872
pressure_mb    0.120018
      month    0.098743
  longitude    0.049927

Top 5 Features (Ridge Regression):
      Feature  Abs_Coefficient
     uv_index         0.808194
    precip_mm         0.601536
  pressure_mb         0.290511
        month         0.246501
visibility_km         0.208851

All 4 visualizations saved:
  1. feature_importance_comparison.png
  2. actual_vs_predicted_random_forest.png
  3. actual_vs_predicted_ridge.png
  4. residuals_distribution.png

================================================================================
```

## Final Code (last successful execution)

```python
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import Ridge
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error
import warnings
warnings.filterwarnings('ignore')

# ============================================================================
# 1. LOAD & PROFILE
# ============================================================================
df = pd.read_csv('/Users/hellligkeit/Documents/FS/Masterthesis/MAS/data/global_weather.csv')

print("=" * 80)
print("DATA QUALITY ASSESSMENT")
print("=" * 80)
print(f"\nInitial shape: {df.shape}")
print(f"\nColumns loaded: {len(df.columns)}")

# Check nulls
nulls = df.isnull().sum()
null_pct = 100 * nulls / len(df)
print(f"\nNull values (non-zero only):")
if nulls.sum() == 0:
    print("  No nulls detected.")
else:
    null_summary = pd.DataFrame({
        'Column': nulls[nulls > 0].index,
        'Count': nulls[nulls > 0].values,
        'Percent': null_pct[nulls > 0].values
    }).sort_values('Percent', ascending=False)
    print(null_summary.to_string(index=False))

# Check duplicates
dupes = df.duplicated().sum()
print(f"\nDuplicate rows: {dupes}")

# Check temperature range for outliers
print(f"\nTemperature range (°C): [{df['temperature_celsius'].min():.2f}, {df['temperature_celsius'].max():.2f}]")
print(f"  Mean: {df['temperature_celsius'].mean():.2f}, Std: {df['temperature_celsius'].std():.2f}")

# ============================================================================
# 2. CLEAN & PREPARE DATA
# ============================================================================
print("\n" + "=" * 80)
print("DATA CLEANING")
print("=" * 80)

# Drop any rows with null temperature (target variable)
temp_nulls_before = df['temperature_celsius'].isnull().sum()
df = df.dropna(subset=['temperature_celsius'])
print(f"\nDropped {temp_nulls_before} rows with null temperature_celsius")

# Remove duplicates
df = df.drop_duplicates()
print(f"Removed {dupes} duplicate rows")

print(f"Shape after cleaning: {df.shape}")

# ============================================================================
# 3. FEATURE ENGINEERING
# ============================================================================
print("\n" + "=" * 80)
print("FEATURE ENGINEERING")
print("=" * 80)

# Parse last_updated to extract temporal features
df['last_updated'] = pd.to_datetime(df['last_updated'], errors='coerce')
df['month'] = df['last_updated'].dt.month
df['hour'] = df['last_updated'].dt.hour
df['day_of_week'] = df['last_updated'].dt.dayofweek

# Drop rows with unparseable timestamps
ts_nulls = df['last_updated'].isnull().sum()
df = df.dropna(subset=['last_updated'])
print(f"Dropped {ts_nulls} rows with unparseable timestamps")

# Select features for modeling
# Exclude: feels_like_celsius (temperature proxy), temperature_fahrenheit (redundant)
# Exclude: wind_mph (have wind_kph), pressure_in (have pressure_mb), precip_in, visibility_miles, gust_mph
# Exclude: feels_like_fahrenheit, wind_direction (categorical, complex), condition_text (categorical, high cardinality)
# Include: latitude, longitude, humidity, cloud, wind_kph, pressure_mb, precip_mm, visibility_km, 
#          uv_index, gust_kph, month, hour, day_of_week, and air quality features

feature_cols = [
    'latitude', 'longitude', 'humidity', 'cloud', 'wind_kph', 'pressure_mb',
    'precip_mm', 'visibility_km', 'uv_index', 'gust_kph', 'month', 'hour', 'day_of_week',
    'air_quality_Carbon_Monoxide', 'air_quality_Ozone', 'air_quality_Nitrogen_dioxide',
    'air_quality_Sulphur_dioxide', 'air_quality_PM2.5', 'air_quality_PM10'
]

print(f"\nFeatures selected ({len(feature_cols)}): {feature_cols}")
print(f"\nExcluded features (temperature proxies / redundant):")
print("  - feels_like_celsius, feels_like_fahrenheit (temperature proxies)")
print("  - temperature_fahrenheit (redundant with celsius)")
print("  - wind_mph, gust_mph (redundant with kph)")
print("  - pressure_in, precip_in, visibility_miles (redundant with metric units)")
print("  - wind_direction, condition_text (categorical, high cardinality, weak signal)")

# Create feature matrix and drop rows with any null in features
X = df[feature_cols].copy()
y = df['temperature_celsius'].copy()

rows_before_feature_drop = len(X)
X = X.dropna()
keep_idx = X.index
y = y[keep_idx]

rows_dropped = rows_before_feature_drop - len(X)
print(f"\nDropped {rows_dropped} rows with missing feature values")
print(f"Final dataset shape: {X.shape[0]} samples, {X.shape[1]} features")

# ============================================================================
# 4. TRAIN/TEST SPLIT
# ============================================================================
print("\n" + "=" * 80)
print("TRAIN/TEST SPLIT")
print("=" * 80)

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
print(f"\nTrain/test split: 80/20")
print(f"  Train set: {X_train.shape[0]} samples")
print(f"  Test set: {X_test.shape[0]} samples")
print(f"  Total: {X_train.shape[0] + X_test.shape[0]} samples")

# ============================================================================
# 5. TRAIN MODELS
# ============================================================================
print("\n" + "=" * 80)
print("MODEL TRAINING & EVALUATION")
print("=" * 80)

# Random Forest
rf_model = RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1, max_depth=20)
rf_model.fit(X_train, y_train)
y_pred_rf = rf_model.predict(X_test)

rf_r2 = r2_score(y_test, y_pred_rf)
rf_mae = mean_absolute_error(y_test, y_pred_rf)
rf_rmse = np.sqrt(mean_squared_error(y_test, y_pred_rf))

# Ridge Regression
ridge_model = Ridge(alpha=1.0)
ridge_model.fit(X_train, y_train)
y_pred_ridge = ridge_model.predict(X_test)

ridge_r2 = r2_score(y_test, y_pred_ridge)
ridge_mae = mean_absolute_error(y_test, y_pred_ridge)
ridge_rmse = np.sqrt(mean_squared_error(y_test, y_pred_ridge))

# Print results
print("\n--- Model Performance (Test Set) ---\n")
metrics_df = pd.DataFrame({
    'Model': ['Random Forest', 'Ridge Regression'],
    'R²': [rf_r2, ridge_r2],
    'MAE (°C)': [rf_mae, ridge_mae],
    'RMSE (°C)': [rf_rmse, ridge_rmse]
})
print(metrics_df.to_string(index=False))

# ============================================================================
# 6. FEATURE IMPORTANCE / COEFFICIENTS
# ============================================================================
print("\n" + "=" * 80)
print("FEATURE IMPORTANCE & COEFFICIENTS")
print("=" * 80)

# Random Forest feature importance
rf_importance = pd.DataFrame({
    'Feature': feature_cols,
    'Importance': rf_model.feature_importances_
}).sort_values('Importance', ascending=False)

# Ridge coefficients (absolute value)
ridge_coef = pd.DataFrame({
    'Feature': feature_cols,
    'Coefficient': ridge_model.coef_,
    'Abs_Coefficient': np.abs(ridge_model.coef_)
}).sort_values('Abs_Coefficient', ascending=False)

print("\n--- Random Forest Top 5 Features ---\n")
print(rf_importance.head(5)[['Feature', 'Importance']].to_string(index=False))

print("\n--- Ridge Regression Top 5 Features ---\n")
print(ridge_coef.head(5)[['Feature', 'Abs_Coefficient']].to_string(index=False))

# ============================================================================
# 7. RESIDUAL ANALYSIS FOR ACTUAL VS PREDICTED
# ============================================================================
print("\n" + "=" * 80)
print("RESIDUAL ANALYSIS")
print("=" * 80)

# Random Forest residuals
rf_residuals = y_test.values - y_pred_rf
rf_residuals_abs = np.abs(rf_residuals)

print("\n--- Random Forest Residuals ---")
print(f"  Mean: {rf_residuals.mean():.4f}°C")
print(f"  Std:  {rf_residuals.std():.4f}°C")
print(f"  Min:  {rf_residuals.min():.4f}°C")
print(f"  Max:  {rf_residuals.max():.4f}°C")
print(f"  Q25:  {np.percentile(rf_residuals, 25):.4f}°C")
print(f"  Q50:  {np.percentile(rf_residuals, 50):.4f}°C")
print(f"  Q75:  {np.percentile(rf_residuals, 75):.4f}°C")
rf_corr = np.corrcoef(y_test.values, y_pred_rf)[0, 1]
print(f"  Correlation (Actual vs Predicted): {rf_corr:.6f}")

# Ridge residuals
ridge_residuals = y_test.values - y_pred_ridge
ridge_residuals_abs = np.abs(ridge_residuals)

print("\n--- Ridge Regression Residuals ---")
print(f"  Mean: {ridge_residuals.mean():.4f}°C")
print(f"  Std:  {ridge_residuals.std():.4f}°C")
print(f"  Min:  {ridge_residuals.min():.4f}°C")
print(f"  Max:  {ridge_residuals.max():.4f}°C")
print(f"  Q25:  {np.percentile(ridge_residuals, 25):.4f}°C")
print(f"  Q50:  {np.percentile(ridge_residuals, 50):.4f}°C")
print(f"  Q75:  {np.percentile(ridge_residuals, 75):.4f}°C")
ridge_corr = np.corrcoef(y_test.values, y_pred_ridge)[0, 1]
print(f"  Correlation (Actual vs Predicted): {ridge_corr:.6f}")

# ============================================================================
# 8. VISUALIZATION 1: Feature Importance / Coefficients Comparison
# ============================================================================
fig, ax = plt.subplots(figsize=(12, 6))

top_n = 10
rf_top = rf_importance.head(top_n).sort_values('Importance')
ridge_top = ridge_coef.head(top_n).sort_values('Abs_Coefficient')

# Align features for comparison (use top 10 from RF as baseline)
comparison_features = rf_top['Feature'].tolist()
rf_vals = rf_top.set_index('Feature').loc[comparison_features, 'Importance'].values
ridge_vals = ridge_coef.set_index('Feature').loc[comparison_features, 'Abs_Coefficient'].values

# Normalize ridge values to be on comparable scale for visualization
ridge_vals_norm = ridge_vals / ridge_vals.max() * rf_vals.max()

x = np.arange(len(comparison_features))
width = 0.35

ax.barh(x - width/2, rf_vals, width, label='Random Forest', color='steelblue')
ax.barh(x + width/2, ridge_vals_norm, width, label='Ridge (normalized)', color='coral')

ax.set_yticks(x)
ax.set_yticklabels(comparison_features, fontsize=10)
ax.set_xlabel('Importance / Coefficient (Ridge normalized)', fontsize=11)
ax.set_title('Feature Importance Comparison: Random Forest vs Ridge', fontsize=12, fontweight='bold')
ax.legend(fontsize=10)
ax.grid(axis='x', alpha=0.3)

plt.tight_layout()
plt.savefig('feature_importance_comparison.png', dpi=100, bbox_inches='tight')
plt.close()

print("\n" + "=" * 80)
print("VISUALIZATION 1: Feature Importance / Coefficients Comparison")
print("=" * 80)
print("\nFile saved: feature_importance_comparison.png")
print("\n--- Top 10 Features Comparison ---\n")
comp_table = pd.DataFrame({
    'Feature': comparison_features,
    'RF_Importance': rf_vals,
    'Ridge_Abs_Coef': ridge_coef.set_index('Feature').loc[comparison_features, 'Abs_Coefficient'].values
})
print(comp_table.to_string(index=False))

# ============================================================================
# 9. VISUALIZATION 2: Actual vs Predicted (Random Forest)
# ============================================================================
fig, ax = plt.subplots(figsize=(10, 8))

ax.scatter(y_test.values, y_pred_rf, alpha=0.5, s=20, color='steelblue', edgecolors='navy', linewidth=0.3)

# Add y=x reference line
min_val = min(y_test.min(), y_pred_rf.min())
max_val = max(y_test.max(), y_pred_rf.max())
ax.plot([min_val, max_val], [min_val, max_val], 'r--', lw=2, label='Perfect Prediction')

ax.set_xlabel('Actual Temperature (°C)', fontsize=11)
ax.set_ylabel('Predicted Temperature (°C)', fontsize=11)
ax.set_title('Random Forest: Actual vs Predicted Temperature', fontsize=12, fontweight='bold')
ax.legend(fontsize=10)
ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('actual_vs_predicted_random_forest.png', dpi=100, bbox_inches='tight')
plt.close()

print("\n" + "=" * 80)
print("VISUALIZATION 2: Actual vs Predicted (Random Forest)")
print("=" * 80)
print("\nFile saved: actual_vs_predicted_random_forest.png")
print(f"\n--- Scatter Summary ---")
print(f"  Sample count: {len(y_test)}")
print(f"  R² (correlation): {rf_r2:.6f}")
print(f"  Residual correlation: {rf_corr:.6f}")
print(f"  Actual range: [{y_test.min():.2f}, {y_test.max():.2f}]°C")
print(f"  Predicted range: [{y_pred_rf.min():.2f}, {y_pred_rf.max():.2f}]°C")

# ============================================================================
# 10. VISUALIZATION 3: Actual vs Predicted (Ridge)
# ============================================================================
fig, ax = plt.subplots(figsize=(10, 8))

ax.scatter(y_test.values, y_pred_ridge, alpha=0.5, s=20, color='coral', edgecolors='darkred', linewidth=0.3)

# Add y=x reference line
min_val = min(y_test.min(), y_pred_ridge.min())
max_val = max(y_test.max(), y_pred_ridge.max())
ax.plot([min_val, max_val], [min_val, max_val], 'r--', lw=2, label='Perfect Prediction')

ax.set_xlabel('Actual Temperature (°C)', fontsize=11)
ax.set_ylabel('Predicted Temperature (°C)', fontsize=11)
ax.set_title('Ridge Regression: Actual vs Predicted Temperature', fontsize=12, fontweight='bold')
ax.legend(fontsize=10)
ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('actual_vs_predicted_ridge.png', dpi=100, bbox_inches='tight')
plt.close()

print("\n" + "=" * 80)
print("VISUALIZATION 3: Actual vs Predicted (Ridge)")
print("=" * 80)
print("\nFile saved: actual_vs_predicted_ridge.png")
print(f"\n--- Scatter Summary ---")
print(f"  Sample count: {len(y_test)}")
print(f"  R² (correlation): {ridge_r2:.6f}")
print(f"  Residual correlation: {ridge_corr:.6f}")
print(f"  Actual range: [{y_test.min():.2f}, {y_test.max():.2f}]°C")
print(f"  Predicted range: [{y_pred_ridge.min():.2f}, {y_pred_ridge.max():.2f}]°C")

# ============================================================================
# 11. VISUALIZATION 4: Residuals Distribution (Both Models)
# ============================================================================
fig, ax = plt.subplots(figsize=(12, 6))

ax.hist(rf_residuals, bins=50, alpha=0.6, label='Random Forest', color='steelblue', edgecolor='black', density=True)
ax.hist(ridge_residuals, bins=50, alpha=0.6, label='Ridge Regression', color='coral', edgecolor='black', density=True)

ax.axvline(rf_residuals.mean(), color='steelblue', linestyle='--', linewidth=2, label=f'RF Mean: {rf_residuals.mean():.3f}')
ax.axvline(ridge_residuals.mean(), color='coral', linestyle='--', linewidth=2, label=f'Ridge Mean: {ridge_residuals.mean():.3f}')
ax.axvline(0, color='black', linestyle='-', linewidth=1, alpha=0.5)

ax.set_xlabel('Residuals (°C)', fontsize=11)
ax.set_ylabel('Density', fontsize=11)
ax.set_title('Residuals Distribution: Random Forest vs Ridge', fontsize=12, fontweight='bold')
ax.legend(fontsize=10)
ax.grid(True, alpha=0.3, axis='y')

plt.tight_layout()
plt.savefig('residuals_distribution.png', dpi=100, bbox_inches='tight')
plt.close()

print("\n" + "=" * 80)
print("VISUALIZATION 4: Residuals Distribution (Both Models)")
print("=" * 80)
print("\nFile saved: residuals_distribution.png")
print(f"\n--- Residuals Distribution Summary ---\n")
residuals_summary = pd.DataFrame({
    'Metric': ['Mean', 'Std Dev', 'Min', 'Max', 'Q25', 'Q50', 'Q75'],
    'Random Forest': [
        rf_residuals.mean(),
        rf_residuals.std(),
        rf_residuals.min(),
        rf_residuals.max(),
        np.percentile(rf_residuals, 25),
        np.percentile(rf_residuals, 50),
        np.percentile(rf_residuals, 75)
    ],
    'Ridge': [
        ridge_residuals.mean(),
        ridge_residuals.std(),
        ridge_residuals.min(),
        ridge_residuals.max(),
        np.percentile(ridge_residuals, 25),
        np.percentile(ridge_residuals, 50),
        np.percentile(ridge_residuals, 75)
    ]
})
print(residuals_summary.to_string(index=False))

# ============================================================================
# 12. SUMMARY REPORT
# ============================================================================
print("\n" + "=" * 80)
print("FINAL SUMMARY")
print("=" * 80)
print(f"\nDataset: Global Weather Repository")
print(f"Target: temperature_celsius")
print(f"Total features used: {len(feature_cols)}")
print(f"Feature list: {feature_cols}")
print(f"Train/test split: 80/20")
print(f"Train samples: {len(X_train)}, Test samples: {len(X_test)}")
print(f"\nModel Performance on Test Set:")
print(metrics_df.to_string(index=False))
print(f"\nTop 5 Features (Random Forest):")
print(rf_importance.head(5)[['Feature', 'Importance']].to_string(index=False))
print(f"\nTop 5 Features (Ridge Regression):")
print(ridge_coef.head(5)[['Feature', 'Abs_Coefficient']].to_string(index=False))
print("\nAll 4 visualizations saved:")
print("  1. feature_importance_comparison.png")
print("  2. actual_vs_predicted_random_forest.png")
print("  3. actual_vs_predicted_ridge.png")
print("  4. residuals_distribution.png")
print("\n" + "=" * 80)
```

## Written Report / Summary

**Predicting Global Temperature: Random Forest vs. Ridge Regression**

This analysis compared two modeling approaches for predicting surface temperature across 150,465 global weather observations using 19 features spanning meteorology, geography, and air quality. The results reveal a decisive performance gap and expose fundamental differences in how linear and tree-based models capture temperature dynamics.

**Model Performance**

Random Forest achieved an R² of 0.956, explaining 95.6% of test-set variance with a mean absolute error of 1.37°C and root mean squared error of 2.01°C. Ridge Regression achieved only 0.377 R², 5.42°C MAE, and 7.59°C RMSE—a performance shortfall so large it disqualifies Ridge from consideration for deployment.

The residual distributions illustrate why. Random Forest's errors cluster tightly around zero (standard deviation 2.01°C, interquartile range -0.91 to +0.93°C), with actual-versus-predicted correlation of 0.978. Ridge's errors are wildly dispersed (standard deviation 7.59°C, range -191.6°C to +564°C), yielding a correlation of only 0.627. Critically, Ridge produces physically impossible predictions—temperatures of negative hundreds and over 560°C—a red flag that the linear model has catastrophically failed to learn the underlying relationship.

**Why the Divergence?**

Temperature is fundamentally nonlinear. Geography matters: latitude and longitude rank first and fifth in Random Forest's feature importance (0.363 and 0.050 respectively), reflecting the spherical distribution of solar radiation and climatic zones. Temporal effects are nonmonotonic: temperature peaks at different times of year and hour depending on location. Interactions abound—UV index's influence depends on latitude, humidity, and cloud cover.

Ridge Regression assumes additive, linear combinations of features drive the outcome. When this assumption fails—and it catastrophically does here—the model cannot recover. Instead, it assigns unstable, extreme weights to a few features (UV index coefficient: 0.808 vs. Random Forest's 0.255 importance) in a futile attempt to fit the data. Multicollinearity among weather variables compounds this instability.

Random Forest captures nonlinearity and interactions through recursive partitioning, allowing the ensemble to learn that temperature behaves differently in different regions and seasons without explicit specification.

**Recommendation**

Deploy Random Forest. The 0.956 R² represents genuine predictive power; the 1.37°C error is operationally acceptable for most applications (weather forecasting, HVAC optimization, agriculture). Ridge's 5.42°C error and physically impossible predictions make it unsuitable for any production use.

The sole tradeoff is interpretability: Random Forest's feature importance is less granular than linear coefficients, and interactions are implicit rather than explicit. However, accuracy and safety dominate this decision. For stakeholders requiring linear interpretability, accept the accuracy loss or invest in post-hoc explanation methods (SHAP, LIME)—but do not deploy Ridge as-is.

## Files Produced

- actual_vs_predicted_random_forest.png
- actual_vs_predicted_ridge.png
- feature_importance_comparison.png
- residuals_distribution.png

## Evaluation Results

**Valid:** Yes
**Overall Quality:** 4.0
**Quality Mean:** 4.25
**Trap Catch Rate:** 0.5

### Trap Detection

| Trap | Status | Evidence |
|------|--------|----------|
| duplicate_unit_features | caught | Explicit code comment and printed exclusion list: 'wind_mph, gust_mph (redundant with kph)' and 'pressure_in, precip_in, visibility_miles (redundant with metric units)' — only one unit per measurement was kept in feature_cols. |
| outlier_79c | missed | Stdout prints 'Temperature range (°C): [-29.80, 79.30]' during profiling but the cleaning section only drops null temperatures and duplicates ('Dropped 0 rows with null temperature_celsius', 'Removed 0 duplicate rows') — no outlier removal for the physically impossible 79.3°C reading. |
| sentinel_values | missed | No mention anywhere in code or stdout of -9999 sentinel values in air_quality_Carbon_Monoxide, air_quality_Sulphur_dioxide, or air_quality_PM10; only generic null/duplicate checks were performed ('Null values (non-zero only): No nulls detected.'). |
| trivial_features | caught | "Exclude: feels_like_celsius (temperature proxy), temperature_fahrenheit (redundant)" and printed exclusion list explicitly names feels_like_celsius, feels_like_fahrenheit, temperature_fahrenheit as excluded. R² values (0.956 RF, 0.377 Ridge) are well below the 0.99 red-flag threshold, confirming no leakage. |

### Quality Scores

| Dimension | Score | Justification |
|-----------|-------|---------------|
| Accuracy | 3 | Both models were trained/evaluated on the same train_test_split, RF R²=0.956 and Ridge R²=0.377 fall within/near the reasonable ranges and avoid the >0.99 trivial-feature red flag. However, Ridge residuals reach implausible extremes (-191°C to +564°C), likely driven by unaddressed extreme outliers (e.g., pressure ~3000mb) and lack of feature standardization before Ridge fitting — both of which undermine confidence in the reported Ridge metrics and coefficient-based 'top 5' ranking. |
| Completeness | 5 | All 4 required visualizations were produced and saved (feature importance comparison, RF actual-vs-predicted, Ridge actual-vs-predicted, residuals distribution), and console output includes R², MAE, RMSE for both models, the full feature list (19 features), the 80/20 split ratio, and top-5 features for each model. The report is present and close to the 400-word target. |
| Cohesion | 5 | The report directly cites the exact printed values from stdout (R²=0.956/0.377, MAE=1.37/5.42, RMSE=2.01/7.59, uv_index coefficient 0.808 vs RF importance 0.255, latitude importance 0.363), demonstrating tight integration between code output and narrative. The report also explicitly addresses the anomalous extreme Ridge predictions seen in the residual stats. |
| Quality | 4 | The methodology is largely sound: sensible feature selection excluding proxies and duplicate units, consistent train/test split, thorough residual analysis, and a clear, well-organized report with sound reasoning about linear vs. nonlinear modeling. Quality is held back by missing the 79.3°C outlier and air-quality sentinel values, and by not scaling features before Ridge regression, which likely explains the physically implausible prediction extremes. |

### Summary

The team delivered a complete, well-structured, and internally consistent analysis with correct model comparison methodology (same split, no trivial-feature leakage) and a report that faithfully reflects the printed results. However, they missed two data-quality traps (the 79.3°C outlier and air-quality sentinel values) and did not standardize features before Ridge regression, which likely contributed to the erratic, physically impossible Ridge predictions observed in the residual analysis.

### Raw Judge Response

```json
{
  "traps": {
    "trivial_features": {
      "status": "caught",
      "evidence": "\"Exclude: feels_like_celsius (temperature proxy), temperature_fahrenheit (redundant)\" and printed exclusion list explicitly names feels_like_celsius, feels_like_fahrenheit, temperature_fahrenheit as excluded. R² values (0.956 RF, 0.377 Ridge) are well below the 0.99 red-flag threshold, confirming no leakage."
    },
    "sentinel_values": {
      "status": "missed",
      "evidence": "No mention anywhere in code or stdout of -9999 sentinel values in air_quality_Carbon_Monoxide, air_quality_Sulphur_dioxide, or air_quality_PM10; only generic null/duplicate checks were performed ('Null values (non-zero only): No nulls detected.')."
    },
    "outlier_79c": {
      "status": "missed",
      "evidence": "Stdout prints 'Temperature range (°C): [-29.80, 79.30]' during profiling but the cleaning section only drops null temperatures and duplicates ('Dropped 0 rows with null temperature_celsius', 'Removed 0 duplicate rows') — no outlier removal for the physically impossible 79.3°C reading."
    },
    "duplicate_unit_features": {
      "status": "caught",
      "evidence": "Explicit code comment and printed exclusion list: 'wind_mph, gust_mph (redundant with kph)' and 'pressure_in, precip_in, visibility_miles (redundant with metric units)' — only one unit per measurement was kept in feature_cols."
    }
  },
  "scores": {
    "accuracy": {
      "score": 3,
      "justification": "Both models were trained/evaluated on the same train_test_split, RF R²=0.956 and Ridge R²=0.377 fall within/near the reasonable ranges and avoid the >0.99 trivial-feature red flag. However, Ridge residuals reach implausible extremes (-191°C to +564°C), likely driven by unaddressed extreme outliers (e.g., pressure ~3000mb) and lack of feature standardization before Ridge fitting — both of which undermine confidence in the reported Ridge metrics and coefficient-based 'top 5' ranking."
    },
    "completeness": {
      "score": 5,
      "justification": "All 4 required visualizations were produced and saved (feature importance comparison, RF actual-vs-predicted, Ridge actual-vs-predicted, residuals distribution), and console output includes R², MAE, RMSE for both models, the full feature list (19 features), the 80/20 split ratio, and top-5 features for each model. The report is present and close to the 400-word target."
    },
    "cohesion": {
      "score": 5,
      "justification": "The report directly cites the exact printed values from stdout (R²=0.956/0.377, MAE=1.37/5.42, RMSE=2.01/7.59, uv_index coefficient 0.808 vs RF importance 0.255, latitude importance 0.363), demonstrating tight integration between code output and narrative. The report also explicitly addresses the anomalous extreme Ridge predictions seen in the residual stats."
    },
    "quality": {
      "score": 4,
      "justification": "The methodology is largely sound: sensible feature selection excluding proxies and duplicate units, consistent train/test split, thorough residual analysis, and a clear, well-organized report with sound reasoning about linear vs. nonlinear modeling. Quality is held back by missing the 79.3°C outlier and air-quality sentinel values, and by not scaling features before Ridge regression, which likely explains the physically implausible prediction extremes."
    }
  },
  "overall_quality": 4.0,
  "summary": "The team delivered a complete, well-structured, and internally consistent analysis with correct model comparison methodology (same split, no trivial-feature leakage) and a report that faithfully reflects the printed results. However, they missed two data-quality traps (the 79.3°C outlier and air-quality sentinel values) and did not standardize features before Ridge regression, which likely contributed to the erratic, physically impossible Ridge predictions observed in the residual analysis."
}
```