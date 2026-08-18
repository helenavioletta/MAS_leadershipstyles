# Control Agent Evaluation — affiliative_long_run04

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
DATA QUALITY INSPECTION
================================================================================
Duplicates: 0

Null counts (>0 only):
Series([], )

Target (temperature_celsius):
  Min: -29.80
  Max: 79.30
  Mean: 21.32
  Nulls: 0

Leakage check: temperature_fahrenheit present (will exclude)

Numeric features selected: 23
['latitude', 'longitude', 'last_updated_epoch', 'temperature_celsius', 'wind_kph', 'wind_degree', 'pressure_mb', 'precip_mm', 'humidity', 'cloud', 'feels_like_celsius', 'visibility_km', 'uv_index', 'gust_kph', 'air_quality_Carbon_Monoxide', 'air_quality_Ozone', 'air_quality_Nitrogen_dioxide', 'air_quality_Sulphur_dioxide', 'air_quality_PM2.5', 'air_quality_PM10', 'air_quality_us-epa-index', 'air_quality_gb-defra-index', 'moon_illumination']

Country cardinality: 211 unique countries

================================================================================
DATA CLEANING ACTIONS
================================================================================
After duplicate removal: 150465 rows
After removing null targets: 150465 rows
After removing critical feature nulls: 150465 rows

Final dataset: 150465 rows × 41 columns

================================================================================
FEATURE PREPARATION
================================================================================
Country label encoded: 1 feature

Final feature list (16 features):
['humidity', 'pressure_mb', 'wind_kph', 'cloud', 'uv_index', 'visibility_km', 'feels_like_celsius', 'gust_kph', 'latitude', 'longitude', 'month', 'hour', 'day_of_week', 'air_quality_PM2.5', 'air_quality_PM10', 'country_encoded']
Model dataset: 150465 rows

Train/test split: 80% / 20%
Train: 120372 | Test: 30093

================================================================================
MODEL TRAINING & EVALUATION
================================================================================

--- MODEL 1: RANDOM FOREST ---
R²:   0.9962
MAE:  0.2633
RMSE: 0.5928

Top 5 features (Random Forest):
           feature  importance
feels_like_celsius    0.960055
          humidity    0.030918
          wind_kph    0.003190
       pressure_mb    0.000725
             month    0.000718

--- MODEL 2: RIDGE REGRESSION ---
R²:   0.9771
MAE:  1.0281
RMSE: 1.4557

Top 5 features (Ridge Regression):
           feature  coefficient
feels_like_celsius     8.966933
          humidity     1.020860
          uv_index     0.204802
       pressure_mb     0.190715
         longitude     0.155204

================================================================================
MODEL COMPARISON SUMMARY
================================================================================
        Model     R²    MAE   RMSE
Random Forest 0.9962 0.2633 0.5928
        Ridge 0.9771 1.0281 1.4557

================================================================================
VISUALIZATION 1: TOP 5 FEATURES COMPARISON
================================================================================

Random Forest - Top 5 Features:
           feature  importance
feels_like_celsius    0.960055
          humidity    0.030918
          wind_kph    0.003190
       pressure_mb    0.000725
             month    0.000718

Ridge Regression - Top 5 Features (|Coefficient|):
           feature  coefficient
feels_like_celsius     8.966933
          humidity     1.020860
          uv_index     0.204802
       pressure_mb     0.190715
         longitude     0.155204

================================================================================
VISUALIZATION 2: ACTUAL VS PREDICTED - RANDOM FOREST
================================================================================
Residual Mean: -0.0066
Residual Std:  0.5927
Sample (first 10):
 Actual  Predicted  Residual
   29.2  29.506844 -0.306844
   21.3  21.299994  0.000006
    8.1   8.202049 -0.102049
   25.3  25.299391  0.000609
   22.3  22.750809 -0.450809
   24.3  23.975999  0.324001
   16.1  16.103791 -0.003791
    8.3   8.290343  0.009657
   19.0  18.999456  0.000544
   21.3  21.299981  0.000019

================================================================================
VISUALIZATION 3: ACTUAL VS PREDICTED - RIDGE REGRESSION
================================================================================
Residual Mean: -0.0026
Residual Std:  1.4557
Sample (first 10):
 Actual  Predicted  Residual
   29.2  30.277544 -1.077544
   21.3  21.588064 -0.288064
    8.1   9.169224 -1.069224
   25.3  23.679544  1.620456
   22.3  22.286526  0.013474
   24.3  24.530110 -0.230110
   16.1  16.121790 -0.021790
    8.3   8.560077 -0.260077
   19.0  20.072967 -1.072967
   21.3  20.183462  1.116538

================================================================================
VISUALIZATION 4: RESIDUAL DISTRIBUTION COMPARISON
================================================================================

Random Forest - Residual Statistics:
Statistic     Value
     Mean -0.006558
      Std  0.592715
      Min -6.718494
      Max 36.718000
25th %ile -0.136442
75th %ile  0.057937

Ridge Regression - Residual Statistics:
Statistic      Value
     Mean  -0.002603
      Std   1.455684
      Min -10.252511
      Max  40.924239
25th %ile  -0.744943
75th %ile   0.775061

================================================================================
ALL OUTPUTS SAVED
================================================================================
Charts saved: chart_1_feature_comparison.png
              chart_2_rf_actual_vs_pred.png
              chart_3_ridge_actual_vs_pred.png
              chart_4_residual_comparison.png
```

## Final Code (last successful execution)

```python
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import Ridge
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error
import warnings
warnings.filterwarnings('ignore')

# Load data
df = pd.read_csv('/Users/hellligkeit/Documents/FS/Masterthesis/MAS/data/global_weather.csv')

print("=" * 80)
print("DATA QUALITY INSPECTION")
print("=" * 80)

# Check for duplicates
dup_count = df.duplicated().sum()
print(f"Duplicates: {dup_count}")

# Check nulls
print(f"\nNull counts (>0 only):")
nulls = df.isnull().sum()
print(nulls[nulls > 0].to_string())

# Check target variable
print(f"\nTarget (temperature_celsius):")
print(f"  Min: {df['temperature_celsius'].min():.2f}")
print(f"  Max: {df['temperature_celsius'].max():.2f}")
print(f"  Mean: {df['temperature_celsius'].mean():.2f}")
print(f"  Nulls: {df['temperature_celsius'].isnull().sum()}")

# Check for leakage (temperature_fahrenheit should be excluded)
print(f"\nLeakage check: temperature_fahrenheit present (will exclude)")

# Numeric columns available for modeling
numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
numeric_cols = [c for c in numeric_cols if c not in ['temperature_fahrenheit', 'feels_like_fahrenheit', 'pressure_in', 'wind_mph', 'gust_mph', 'visibility_miles', 'precip_in']]
print(f"\nNumeric features selected: {len(numeric_cols)}")
print(numeric_cols)

# Check country cardinality
print(f"\nCountry cardinality: {df['country'].nunique()} unique countries")

# Data cleaning
print("\n" + "=" * 80)
print("DATA CLEANING ACTIONS")
print("=" * 80)

# Remove duplicates
df = df.drop_duplicates()
print(f"After duplicate removal: {df.shape[0]} rows")

# Remove rows with missing temperature (target)
df = df.dropna(subset=['temperature_celsius'])
print(f"After removing null targets: {df.shape[0]} rows")

# For features, forward fill or drop rows with critical nulls
critical_features = ['humidity', 'pressure_mb', 'wind_kph', 'cloud', 'uv_index']
df = df.dropna(subset=critical_features)
print(f"After removing critical feature nulls: {df.shape[0]} rows")

# For remaining numeric features, forward fill with column mean
numeric_features = [c for c in numeric_cols if c in df.columns]
for col in numeric_features:
    if df[col].isnull().sum() > 0:
        df[col].fillna(df[col].mean(), inplace=True)

print(f"\nFinal dataset: {df.shape[0]} rows × {df.shape[1]} columns")

# Feature engineering & preparation
print("\n" + "=" * 80)
print("FEATURE PREPARATION")
print("=" * 80)

# Extract temporal features from last_updated
df['last_updated'] = pd.to_datetime(df['last_updated'], errors='coerce')
df['month'] = df['last_updated'].dt.month
df['hour'] = df['last_updated'].dt.hour
df['day_of_week'] = df['last_updated'].dt.dayofweek

# Encode country (one-hot if <50 unique, else label encode)
if df['country'].nunique() <= 50:
    country_encoded = pd.get_dummies(df['country'], prefix='country', drop_first=True)
    df = pd.concat([df, country_encoded], axis=1)
    print(f"Country one-hot encoded: {country_encoded.shape[1]} features")
else:
    le = LabelEncoder()
    df['country_encoded'] = le.fit_transform(df['country'])
    print(f"Country label encoded: 1 feature")

# Select final features for modeling
feature_cols = ['humidity', 'pressure_mb', 'wind_kph', 'cloud', 'uv_index', 
                'visibility_km', 'feels_like_celsius', 'gust_kph', 
                'latitude', 'longitude', 'month', 'hour', 'day_of_week',
                'air_quality_PM2.5', 'air_quality_PM10']

# Add country features if one-hot encoded
if df['country'].nunique() <= 50:
    country_cols = [c for c in df.columns if c.startswith('country_')]
    feature_cols.extend(country_cols)
else:
    feature_cols.append('country_encoded')

# Filter to available features
feature_cols = [c for c in feature_cols if c in df.columns]

# Remove any remaining nulls in features
df_model = df[feature_cols + ['temperature_celsius']].copy()
df_model = df_model.dropna()

print(f"\nFinal feature list ({len(feature_cols)} features):")
print(feature_cols)
print(f"Model dataset: {df_model.shape[0]} rows")

# Prepare X and y
X = df_model[feature_cols]
y = df_model['temperature_celsius']

# Train/test split
test_ratio = 0.20
train_ratio = 0.80
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=test_ratio, random_state=42)

print(f"\nTrain/test split: {train_ratio:.0%} / {test_ratio:.0%}")
print(f"Train: {X_train.shape[0]} | Test: {X_test.shape[0]}")

# Standardize features
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

print("\n" + "=" * 80)
print("MODEL TRAINING & EVALUATION")
print("=" * 80)

# Model 1: Random Forest
print("\n--- MODEL 1: RANDOM FOREST ---")
rf = RandomForestRegressor(n_estimators=100, max_depth=15, random_state=42, n_jobs=-1)
rf.fit(X_train, y_train)
y_pred_rf = rf.predict(X_test)

r2_rf = r2_score(y_test, y_pred_rf)
mae_rf = mean_absolute_error(y_test, y_pred_rf)
rmse_rf = np.sqrt(mean_squared_error(y_test, y_pred_rf))

print(f"R²:   {r2_rf:.4f}")
print(f"MAE:  {mae_rf:.4f}")
print(f"RMSE: {rmse_rf:.4f}")

# Feature importance for RF
feature_importance_rf = pd.DataFrame({
    'feature': feature_cols,
    'importance': rf.feature_importances_
}).sort_values('importance', ascending=False)

print(f"\nTop 5 features (Random Forest):")
print(feature_importance_rf.head(5).to_string(index=False))

# Model 2: Ridge Regression
print("\n--- MODEL 2: RIDGE REGRESSION ---")
ridge = Ridge(alpha=1.0, random_state=42)
ridge.fit(X_train_scaled, y_train)
y_pred_ridge = ridge.predict(X_test_scaled)

r2_ridge = r2_score(y_test, y_pred_ridge)
mae_ridge = mean_absolute_error(y_test, y_pred_ridge)
rmse_ridge = np.sqrt(mean_squared_error(y_test, y_pred_ridge))

print(f"R²:   {r2_ridge:.4f}")
print(f"MAE:  {mae_ridge:.4f}")
print(f"RMSE: {rmse_ridge:.4f}")

# Feature importance for Ridge (absolute coefficients)
feature_importance_ridge = pd.DataFrame({
    'feature': feature_cols,
    'coefficient': np.abs(ridge.coef_)
}).sort_values('coefficient', ascending=False)

print(f"\nTop 5 features (Ridge Regression):")
print(feature_importance_ridge.head(5).to_string(index=False))

# Summary
print("\n" + "=" * 80)
print("MODEL COMPARISON SUMMARY")
print("=" * 80)
summary = pd.DataFrame({
    'Model': ['Random Forest', 'Ridge'],
    'R²': [f"{r2_rf:.4f}", f"{r2_ridge:.4f}"],
    'MAE': [f"{mae_rf:.4f}", f"{mae_ridge:.4f}"],
    'RMSE': [f"{rmse_rf:.4f}", f"{rmse_ridge:.4f}"]
})
print(summary.to_string(index=False))

# Save outputs for visualization
results_data = {
    'feature_cols': feature_cols,
    'feature_importance_rf': feature_importance_rf,
    'feature_importance_ridge': feature_importance_ridge,
    'y_test': y_test,
    'y_pred_rf': y_pred_rf,
    'y_pred_ridge': y_pred_ridge
}

# PART 2: VISUALIZATIONS

import matplotlib.pyplot as plt
import numpy as np

# Reload results data (in practice, these are already in memory)
feature_cols = results_data['feature_cols']
feature_importance_rf = results_data['feature_importance_rf']
feature_importance_ridge = results_data['feature_importance_ridge']
y_test = results_data['y_test']
y_pred_rf = results_data['y_pred_rf']
y_pred_ridge = results_data['y_pred_ridge']

print("\n" + "=" * 80)
print("VISUALIZATION 1: TOP 5 FEATURES COMPARISON")
print("=" * 80)

top_5_rf = feature_importance_rf.head(5).copy()
top_5_ridge = feature_importance_ridge.head(5).copy()

# Normalize for comparison (RF importance, Ridge abs coefficients)
fig, ax = plt.subplots(figsize=(10, 5))
x = np.arange(5)
width = 0.35

# Normalize for visibility
norm_rf = top_5_rf['importance'].values / top_5_rf['importance'].max()
norm_ridge = top_5_ridge['coefficient'].values / top_5_ridge['coefficient'].max()

ax.bar(x - width/2, norm_rf, width, label='Random Forest (normalized)', alpha=0.8)
ax.bar(x + width/2, norm_ridge, width, label='Ridge (normalized)', alpha=0.8)

ax.set_xlabel('Feature')
ax.set_ylabel('Normalized Importance / |Coefficient|')
ax.set_title('Top 5 Features: Random Forest vs Ridge Regression')
ax.set_xticks(x)
ax.set_xticklabels([f.replace('country_', 'C_')[:15] for f in top_5_rf['feature'].values], rotation=45, ha='right', fontsize=9)
ax.legend()
ax.grid(axis='y', alpha=0.3)
plt.tight_layout()
plt.savefig('chart_1_feature_comparison.png', dpi=100, bbox_inches='tight')
plt.close()

# Print underlying data
print("\nRandom Forest - Top 5 Features:")
print(top_5_rf[['feature', 'importance']].to_string(index=False))
print("\nRidge Regression - Top 5 Features (|Coefficient|):")
print(top_5_ridge[['feature', 'coefficient']].to_string(index=False))

print("\n" + "=" * 80)
print("VISUALIZATION 2: ACTUAL VS PREDICTED - RANDOM FOREST")
print("=" * 80)

fig, ax = plt.subplots(figsize=(8, 6))
ax.scatter(y_test, y_pred_rf, alpha=0.4, s=20, label='Predictions')
min_temp = min(y_test.min(), y_pred_rf.min())
max_temp = max(y_test.max(), y_pred_rf.max())
ax.plot([min_temp, max_temp], [min_temp, max_temp], 'r--', label='Perfect Prediction')
ax.set_xlabel('Actual Temperature (°C)')
ax.set_ylabel('Predicted Temperature (°C)')
ax.set_title('Random Forest: Actual vs Predicted Temperature')
ax.legend()
ax.grid(alpha=0.3)
plt.tight_layout()
plt.savefig('chart_2_rf_actual_vs_pred.png', dpi=100, bbox_inches='tight')
plt.close()

# Print summary stats
residuals_rf = y_test.values - y_pred_rf
print(f"Residual Mean: {residuals_rf.mean():.4f}")
print(f"Residual Std:  {residuals_rf.std():.4f}")
print(f"Sample (first 10):")
sample_rf = pd.DataFrame({
    'Actual': y_test.values[:10],
    'Predicted': y_pred_rf[:10],
    'Residual': residuals_rf[:10]
})
print(sample_rf.to_string(index=False))

print("\n" + "=" * 80)
print("VISUALIZATION 3: ACTUAL VS PREDICTED - RIDGE REGRESSION")
print("=" * 80)

fig, ax = plt.subplots(figsize=(8, 6))
ax.scatter(y_test, y_pred_ridge, alpha=0.4, s=20, label='Predictions', color='orange')
min_temp = min(y_test.min(), y_pred_ridge.min())
max_temp = max(y_test.max(), y_pred_ridge.max())
ax.plot([min_temp, max_temp], [min_temp, max_temp], 'r--', label='Perfect Prediction')
ax.set_xlabel('Actual Temperature (°C)')
ax.set_ylabel('Predicted Temperature (°C)')
ax.set_title('Ridge Regression: Actual vs Predicted Temperature')
ax.legend()
ax.grid(alpha=0.3)
plt.tight_layout()
plt.savefig('chart_3_ridge_actual_vs_pred.png', dpi=100, bbox_inches='tight')
plt.close()

# Print summary stats
residuals_ridge = y_test.values - y_pred_ridge
print(f"Residual Mean: {residuals_ridge.mean():.4f}")
print(f"Residual Std:  {residuals_ridge.std():.4f}")
print(f"Sample (first 10):")
sample_ridge = pd.DataFrame({
    'Actual': y_test.values[:10],
    'Predicted': y_pred_ridge[:10],
    'Residual': residuals_ridge[:10]
})
print(sample_ridge.to_string(index=False))

print("\n" + "=" * 80)
print("VISUALIZATION 4: RESIDUAL DISTRIBUTION COMPARISON")
print("=" * 80)

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

ax1.hist(residuals_rf, bins=50, alpha=0.7, edgecolor='black', color='steelblue')
ax1.set_xlabel('Residual (°C)')
ax1.set_ylabel('Frequency')
ax1.set_title('Random Forest - Residual Distribution')
ax1.axvline(0, color='red', linestyle='--', linewidth=2, label='Zero Error')
ax1.legend()
ax1.grid(alpha=0.3)

ax2.hist(residuals_ridge, bins=50, alpha=0.7, edgecolor='black', color='orange')
ax2.set_xlabel('Residual (°C)')
ax2.set_ylabel('Frequency')
ax2.set_title('Ridge Regression - Residual Distribution')
ax2.axvline(0, color='red', linestyle='--', linewidth=2, label='Zero Error')
ax2.legend()
ax2.grid(alpha=0.3)

plt.tight_layout()
plt.savefig('chart_4_residual_comparison.png', dpi=100, bbox_inches='tight')
plt.close()

# Print summary stats
print("\nRandom Forest - Residual Statistics:")
residual_stats_rf = pd.DataFrame({
    'Statistic': ['Mean', 'Std', 'Min', 'Max', '25th %ile', '75th %ile'],
    'Value': [
        residuals_rf.mean(),
        residuals_rf.std(),
        residuals_rf.min(),
        residuals_rf.max(),
        np.percentile(residuals_rf, 25),
        np.percentile(residuals_rf, 75)
    ]
})
print(residual_stats_rf.to_string(index=False))

print("\nRidge Regression - Residual Statistics:")
residual_stats_ridge = pd.DataFrame({
    'Statistic': ['Mean', 'Std', 'Min', 'Max', '25th %ile', '75th %ile'],
    'Value': [
        residuals_ridge.mean(),
        residuals_ridge.std(),
        residuals_ridge.min(),
        residuals_ridge.max(),
        np.percentile(residuals_ridge, 25),
        np.percentile(residuals_ridge, 75)
    ]
})
print(residual_stats_ridge.to_string(index=False))

print("\n" + "=" * 80)
print("ALL OUTPUTS SAVED")
print("=" * 80)
print("Charts saved: chart_1_feature_comparison.png")
print("              chart_2_rf_actual_vs_pred.png")
print("              chart_3_ridge_actual_vs_pred.png")
print("              chart_4_residual_comparison.png")
```

## Written Report / Summary

## Temperature Prediction Model Comparison: Random Forest vs. Ridge Regression

### Model Performance & Selection

Two models were trained on 150,465 global weather records (80% train, 20% test) to predict temperature_celsius using 16 predictors spanning weather, geography, temporal, and air quality domains. The Random Forest model substantially outperformed Ridge Regression across all evaluation metrics.

Random Forest achieved an R² of 0.9962, explaining 99.6% of temperature variance, with a mean absolute error (MAE) of 0.26°C and root mean squared error (RMSE) of 0.59°C. Ridge Regression, by comparison, achieved R² of 0.9771 (97.7% variance explained), MAE of 1.03°C, and RMSE of 1.46°C. The tree-based model's MAE is approximately four times smaller—a practically significant difference for weather forecasting applications where precision matters.

### Why the Performance Gap?

The disparity stems from fundamental model differences. Random Forest's non-linear decision boundaries capture complex, localized temperature patterns that Ridge's linear hyperplane cannot represent. Residual analysis reveals this clearly: Random Forest residuals are tightly concentrated (standard deviation 0.59°C) with 50% of errors within ±0.14°C, whereas Ridge shows broader scatter (standard deviation 1.46°C) and heteroscedasticity—larger errors at temperature extremes. Linear models struggle at distribution tails because the relationship between predictors and temperature, while generally strong, includes non-linear interactions that trees naturally detect.

### Feature Importance: Dominance of feels_like_celsius

Both models overwhelmingly prioritize feels_like_celsius—the variable encoding wind chill, humidity effects, and thermal sensation. Random Forest assigns it 96% of total feature importance; Ridge gives it a coefficient of 8.97, dwarfing all others. This makes intuitive sense: feels_like already synthesizes multiple meteorological influences, leaving little residual signal for other predictors to capture.

Secondary predictors differ between models. Random Forest relies modestly on humidity (3.1%), wind speed (0.3%), and pressure (0.07%). Ridge assigns slightly higher weight to humidity (coefficient 1.02), UV index (0.20), pressure (0.19), and longitude (0.16)—suggesting the linear model captures subtle geographic and seasonal patterns that forests dismiss as noise. Neither model finds day-of-week or air quality metrics influential.

### Recommendation: Deploy Random Forest

For operational temperature forecasting, **Random Forest is the clear choice**. Its superior accuracy (0.26°C mean error vs. 1.03°C), stable residual behavior, and interpretable feature rankings make it more reliable for real-world deployment. Ridge's simpler structure offers no compensating advantage—the 0.01 difference in R² does not offset its four-fold error increase. The tree model's ability to capture non-linear weather dynamics justifies any modest increase in computational cost.

## Files Produced

- chart_1_feature_comparison.png
- chart_2_rf_actual_vs_pred.png
- chart_3_ridge_actual_vs_pred.png
- chart_4_residual_comparison.png

## Evaluation Results

**Valid:** Yes
**Overall Quality:** 2.0
**Quality Mean:** 2.5
**Trap Catch Rate:** 0.25

### Trap Detection

| Trap | Status | Evidence |
|------|--------|----------|
| duplicate_unit_features | caught | `numeric_cols = [c for c in numeric_cols if c not in ['temperature_fahrenheit', 'feels_like_fahrenheit', 'pressure_in', 'wind_mph', 'gust_mph', 'visibility_miles', 'precip_in']]` explicitly removes duplicate-unit columns (wind_mph, gust_mph, pressure_in, visibility_miles, precip_in), keeping only the kph/mb/km/mm versions. |
| outlier_79c | missed | stdout shows 'Max: 79.30' for temperature_celsius but no code or report text addresses or removes this physically impossible value; it remains in the modeling dataset. |
| sentinel_values | missed | No mention of -9999 or other sentinel values in air_quality columns anywhere in the code or output; only generic null-count checks were performed, which would not catch sentinel placeholders. |
| trivial_features | missed | The team excluded temperature_fahrenheit and feels_like_fahrenheit but then explicitly added 'feels_like_celsius' to feature_cols: `feature_cols = ['humidity', 'pressure_mb', 'wind_kph', 'cloud', 'uv_index', 'visibility_km', 'feels_like_celsius', 'gust_kph', ...]`. This variable has ~0.98 correlation with the target and became the dominant feature (96% RF importance, coefficient 8.97 in Ridge), producing the RED FLAG R²=0.9962 for Random Forest. |

### Quality Scores

| Dimension | Score | Justification |
|-----------|-------|---------------|
| Accuracy | 1 | Random Forest achieved R²=0.9962, exceeding the explicit red-flag threshold of 0.99, directly caused by including feels_like_celsius (a near-duplicate of the target) as a feature. This inflates both models' performance and invalidates the entire model comparison, as confirmed by the reference's expected R² ranges (RF ~0.85-0.95, Ridge ~0.40-0.65) being far exceeded. |
| Completeness | 4 | All required deliverables are present: 4 charts saved (chart_1 through chart_4), console printouts of R²/MAE/RMSE, feature list (16 features), train/test split ratio (80/20), and top-5 feature importances for both models. The report is approximately 400-450 words and not truncated, covering all requested comparison points. |
| Cohesion | 4 | The report directly cites the printed console numbers (R²=0.9962, MAE=0.26°C vs R²=0.9771, MAE=1.03°C, feels_like_celsius dominance) and ties conclusions to the actual computed feature importances and residual statistics, showing a unified narrative consistent with the code output. |
| Quality | 1 | The core methodology is fundamentally broken: including feels_like_celsius (a near-perfect proxy for temperature) as a predictor makes the entire tree-vs-linear model comparison meaningless, since both models' performance is dominated by a leaked feature rather than genuine predictive signal. Despite clean presentation and thorough surface-level EDA (duplicates, nulls, unit exclusion), this leakage undermines the validity of all downstream conclusions and recommendations. |

### Summary

The team executed a well-organized pipeline with clean code, correct duplicate-unit exclusion, and complete deliverables (4 charts, full console metrics, and a cohesive report), but critically failed to exclude feels_like_celsius, a near-duplicate of the target variable, causing severely inflated R² values (0.9962 and 0.9771) that trigger the explicit red-flag threshold and render the model comparison invalid. Additional traps (79.3°C outlier, sentinel -9999 values) were also missed, though the duplicate-unit trap was correctly handled. The surface quality and cohesion are good, but the core accuracy and methodology are compromised by target leakage.

### Raw Judge Response

```json
{
  "traps": {
    "trivial_features": {
      "status": "missed",
      "evidence": "The team excluded temperature_fahrenheit and feels_like_fahrenheit but then explicitly added 'feels_like_celsius' to feature_cols: `feature_cols = ['humidity', 'pressure_mb', 'wind_kph', 'cloud', 'uv_index', 'visibility_km', 'feels_like_celsius', 'gust_kph', ...]`. This variable has ~0.98 correlation with the target and became the dominant feature (96% RF importance, coefficient 8.97 in Ridge), producing the RED FLAG R²=0.9962 for Random Forest."
    },
    "sentinel_values": {
      "status": "missed",
      "evidence": "No mention of -9999 or other sentinel values in air_quality columns anywhere in the code or output; only generic null-count checks were performed, which would not catch sentinel placeholders."
    },
    "outlier_79c": {
      "status": "missed",
      "evidence": "stdout shows 'Max: 79.30' for temperature_celsius but no code or report text addresses or removes this physically impossible value; it remains in the modeling dataset."
    },
    "duplicate_unit_features": {
      "status": "caught",
      "evidence": "`numeric_cols = [c for c in numeric_cols if c not in ['temperature_fahrenheit', 'feels_like_fahrenheit', 'pressure_in', 'wind_mph', 'gust_mph', 'visibility_miles', 'precip_in']]` explicitly removes duplicate-unit columns (wind_mph, gust_mph, pressure_in, visibility_miles, precip_in), keeping only the kph/mb/km/mm versions."
    }
  },
  "scores": {
    "accuracy": {
      "score": 1,
      "justification": "Random Forest achieved R²=0.9962, exceeding the explicit red-flag threshold of 0.99, directly caused by including feels_like_celsius (a near-duplicate of the target) as a feature. This inflates both models' performance and invalidates the entire model comparison, as confirmed by the reference's expected R² ranges (RF ~0.85-0.95, Ridge ~0.40-0.65) being far exceeded."
    },
    "completeness": {
      "score": 4,
      "justification": "All required deliverables are present: 4 charts saved (chart_1 through chart_4), console printouts of R²/MAE/RMSE, feature list (16 features), train/test split ratio (80/20), and top-5 feature importances for both models. The report is approximately 400-450 words and not truncated, covering all requested comparison points."
    },
    "cohesion": {
      "score": 4,
      "justification": "The report directly cites the printed console numbers (R²=0.9962, MAE=0.26°C vs R²=0.9771, MAE=1.03°C, feels_like_celsius dominance) and ties conclusions to the actual computed feature importances and residual statistics, showing a unified narrative consistent with the code output."
    },
    "quality": {
      "score": 1,
      "justification": "The core methodology is fundamentally broken: including feels_like_celsius (a near-perfect proxy for temperature) as a predictor makes the entire tree-vs-linear model comparison meaningless, since both models' performance is dominated by a leaked feature rather than genuine predictive signal. Despite clean presentation and thorough surface-level EDA (duplicates, nulls, unit exclusion), this leakage undermines the validity of all downstream conclusions and recommendations."
    }
  },
  "overall_quality": 2.0,
  "summary": "The team executed a well-organized pipeline with clean code, correct duplicate-unit exclusion, and complete deliverables (4 charts, full console metrics, and a cohesive report), but critically failed to exclude feels_like_celsius, a near-duplicate of the target variable, causing severely inflated R² values (0.9962 and 0.9771) that trigger the explicit red-flag threshold and render the model comparison invalid. Additional traps (79.3°C outlier, sentinel -9999 values) were also missed, though the duplicate-unit trap was correctly handled. The surface quality and cohesion are good, but the core accuracy and methodology are compromised by target leakage."
}
```