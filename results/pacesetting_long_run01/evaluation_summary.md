# Control Agent Evaluation — pacesetting_long_run01

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
DATA PROFILING
================================================================================
Shape: (150465, 41)

Null counts (>0 only):
Series([], dtype: int64)

Duplicate rows: 0

Temperature range: -29.80 to 79.30°C
Humidity range: 2 to 100%
Wind kph range: 3.60 to 2963.20
Pressure mb range: 947.00 to 3006.00

================================================================================
DATA CLEANING
================================================================================
Dropped 1 rows with temp outside [-50, 60]°C. Rows: 150465 → 150464
Dropped 1 rows with wind_kph > 300. Rows: 150464 → 150463
Columns after null handling: 41 → 41

================================================================================
FEATURE ENGINEERING
================================================================================
Dropped leakage/timestamp columns: ['last_updated', 'last_updated_epoch', 'temperature_fahrenheit', 'feels_like_celsius', 'feels_like_fahrenheit', 'timezone', 'sunrise', 'sunset', 'moonrise', 'moonset', 'pressure_in', 'wind_mph', 'gust_mph', 'visibility_miles', 'precip_in']
Remaining columns: ['country', 'location_name', 'latitude', 'longitude', 'temperature_celsius', 'condition_text', 'wind_kph', 'wind_degree', 'wind_direction', 'pressure_mb', 'precip_mm', 'humidity', 'cloud', 'visibility_km', 'uv_index', 'gust_kph', 'air_quality_Carbon_Monoxide', 'air_quality_Ozone', 'air_quality_Nitrogen_dioxide', 'air_quality_Sulphur_dioxide', 'air_quality_PM2.5', 'air_quality_PM10', 'air_quality_us-epa-index', 'air_quality_gb-defra-index', 'moon_phase', 'moon_illumination', 'month', 'hour']
Dropped location_name and country (geographic overfitting prevention).
Label-encoded condition_text → condition (57 unique values).
Dropped wind_direction and moon_phase.

✓ Final feature set (23 features):
  ['air_quality_Carbon_Monoxide', 'air_quality_Nitrogen_dioxide', 'air_quality_Ozone', 'air_quality_PM10', 'air_quality_PM2.5', 'air_quality_Sulphur_dioxide', 'air_quality_gb-defra-index', 'air_quality_us-epa-index', 'cloud', 'condition', 'gust_kph', 'hour', 'humidity', 'latitude', 'longitude', 'month', 'moon_illumination', 'precip_mm', 'pressure_mb', 'uv_index', 'visibility_km', 'wind_degree', 'wind_kph']

================================================================================
TRAIN/TEST SPLIT
================================================================================
Train/Test Split: 80/20
Train set: 120370 rows
Test set:  30093 rows
Total: 150463 rows

================================================================================
MODEL TRAINING
================================================================================

================================================================================
RANDOM FOREST RESULTS
================================================================================
R² Score:  0.9590
MAE:       1.3532°C
RMSE:      1.9418°C

Features: 23 total
Feature list: ['air_quality_Carbon_Monoxide', 'air_quality_Nitrogen_dioxide', 'air_quality_Ozone', 'air_quality_PM10', 'air_quality_PM2.5', 'air_quality_Sulphur_dioxide', 'air_quality_gb-defra-index', 'air_quality_us-epa-index', 'cloud', 'condition', 'gust_kph', 'hour', 'humidity', 'latitude', 'longitude', 'month', 'moon_illumination', 'precip_mm', 'pressure_mb', 'uv_index', 'visibility_km', 'wind_degree', 'wind_kph']

Top 5 features (by importance):
    Feature  Importance
   latitude    0.365323
   uv_index    0.251740
pressure_mb    0.119421
      month    0.099145
  longitude    0.049711

================================================================================
RIDGE REGRESSION RESULTS
================================================================================
R² Score:  0.4863
MAE:       5.5285°C
RMSE:      6.8712°C

Features: 23 total
Feature list: ['air_quality_Carbon_Monoxide', 'air_quality_Nitrogen_dioxide', 'air_quality_Ozone', 'air_quality_PM10', 'air_quality_PM2.5', 'air_quality_Sulphur_dioxide', 'air_quality_gb-defra-index', 'air_quality_us-epa-index', 'cloud', 'condition', 'gust_kph', 'hour', 'humidity', 'latitude', 'longitude', 'month', 'moon_illumination', 'precip_mm', 'pressure_mb', 'uv_index', 'visibility_km', 'wind_degree', 'wind_kph']

Top 5 features (by |coefficient|):
    Feature  Coefficient
   latitude    -3.347783
   uv_index     2.856184
pressure_mb    -2.185825
   humidity    -1.251703
      month     0.832590

================================================================================
GENERATING CHARTS
================================================================================
✓ Chart 1 saved: chart1_feature_importance_comparison.png

Chart 1 Data (Feature Importances/Coefficients):
Random Forest Top 10:
                     Feature  Importance
                    latitude    0.365323
                    uv_index    0.251740
                 pressure_mb    0.119421
                       month    0.099145
                   longitude    0.049711
                    humidity    0.033441
                        hour    0.009647
 air_quality_Sulphur_dioxide    0.009516
 air_quality_Carbon_Monoxide    0.007150
air_quality_Nitrogen_dioxide    0.006813

Ridge Top 10 (absolute coefficients):
                   Feature  Coefficient
                  latitude    -3.347783
                  uv_index     2.856184
               pressure_mb    -2.185825
                  humidity    -1.251703
                     month     0.832590
         air_quality_PM2.5    -0.786830
                  gust_kph     0.773547
         air_quality_Ozone     0.711709
  air_quality_us-epa-index     0.629051
air_quality_gb-defra-index     0.620925

✓ Chart 2 saved: chart2_rf_actual_vs_predicted.png
Chart 2 Data (RF Actual vs Predicted):
  Prediction range: [-20.37, 47.33]°C
  Actual range: [-26.80, 48.80]°C
  Mean prediction error: -0.0115°C
  Std prediction error: 1.9418°C

✓ Chart 3 saved: chart3_ridge_actual_vs_predicted.png
Chart 3 Data (Ridge Actual vs Predicted):
  Prediction range: [2.36, 51.79]°C
  Actual range: [-26.80, 48.80]°C
  Mean prediction error: -0.0963°C
  Std prediction error: 6.8706°C

✓ Chart 4 saved: chart4_residual_distribution_comparison.png
Chart 4 Data (Residual Distribution):
        Model  Mean Residual  Std Residual  Min Residual  Max Residual
Random Forest      -0.011519      1.941776    -15.527000     16.438000
        Ridge      -0.096331      6.870617    -38.487564     18.264165

================================================================================
MODEL COMPARISON SUMMARY
================================================================================
   Metric Random Forest  Ridge
 R² Score        0.9590 0.4863
 MAE (°C)        1.3532 5.5285
RMSE (°C)        1.9418 6.8712

================================================================================
CHARTS SAVED
================================================================================
✓ chart1_feature_importance_comparison.png
✓ chart2_rf_actual_vs_predicted.png
✓ chart3_ridge_actual_vs_predicted.png
✓ chart4_residual_distribution_comparison.png

================================================================================
END OF CODER OUTPUT
================================================================================
```

## Final Code (last successful execution)

```python
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import Ridge
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error
import warnings
warnings.filterwarnings('ignore')

# ============================================================================
# STEP 1: LOAD AND PROFILE
# ============================================================================
df = pd.read_csv('/Users/hellligkeit/Documents/FS/Masterthesis/MAS/data/global_weather.csv')

print("="*80)
print("DATA PROFILING")
print("="*80)
print(f"Shape: {df.shape}")
print(f"\nNull counts (>0 only):")
nulls = df.isnull().sum()
print(nulls[nulls > 0])
print(f"\nDuplicate rows: {df.duplicated().sum()}")

# Check for obvious garbage: negative humidity, impossible temps, extreme winds
print(f"\nTemperature range: {df['temperature_celsius'].min():.2f} to {df['temperature_celsius'].max():.2f}°C")
print(f"Humidity range: {df['humidity'].min()} to {df['humidity'].max()}%")
print(f"Wind kph range: {df['wind_kph'].min():.2f} to {df['wind_kph'].max():.2f}")
print(f"Pressure mb range: {df['pressure_mb'].min():.2f} to {df['pressure_mb'].max():.2f}")

# ============================================================================
# STEP 2: CLEAN DATA
# ============================================================================
print("\n" + "="*80)
print("DATA CLEANING")
print("="*80)

rows_before = len(df)

# Drop exact duplicates
dupes = df.duplicated().sum()
if dupes > 0:
    df = df.drop_duplicates()
    print(f"Dropped {dupes} duplicate rows. Rows: {rows_before} → {len(df)}")

# Drop rows with temp outside [-50, 60]°C
temp_outliers = ((df['temperature_celsius'] < -50) | (df['temperature_celsius'] > 60)).sum()
if temp_outliers > 0:
    df = df[(df['temperature_celsius'] >= -50) & (df['temperature_celsius'] <= 60)]
    print(f"Dropped {temp_outliers} rows with temp outside [-50, 60]°C. Rows: {rows_before} → {len(df)}")
    rows_before = len(df)

# Drop rows with wind_kph > 300
wind_outliers = (df['wind_kph'] > 300).sum()
if wind_outliers > 0:
    df = df[df['wind_kph'] <= 300]
    print(f"Dropped {wind_outliers} rows with wind_kph > 300. Rows: {rows_before} → {len(df)}")
    rows_before = len(df)

# Null handling: <5% missing → impute median; >=5% → drop column
cols_before = len(df.columns)
for col in df.columns:
    null_pct = df[col].isnull().sum() / len(df) * 100
    if null_pct > 0:
        if null_pct < 5:
            if df[col].dtype in ['float64', 'int64']:
                df[col].fillna(df[col].median(), inplace=True)
                print(f"Imputed {col} ({null_pct:.2f}% nulls) with median.")
        else:
            df.drop(columns=[col], inplace=True)
            print(f"Dropped column {col} ({null_pct:.2f}% nulls).")

print(f"Columns after null handling: {cols_before} → {len(df.columns)}")

# ============================================================================
# STEP 3: FEATURE ENGINEERING
# ============================================================================
print("\n" + "="*80)
print("FEATURE ENGINEERING")
print("="*80)

# Extract month and hour from last_updated
df['last_updated'] = pd.to_datetime(df['last_updated'])
df['month'] = df['last_updated'].dt.month
df['hour'] = df['last_updated'].dt.hour

# Drop raw timestamp and leakage columns
leakage_cols = ['last_updated', 'last_updated_epoch', 'temperature_fahrenheit', 
                'feels_like_celsius', 'feels_like_fahrenheit', 'timezone', 'sunrise', 
                'sunset', 'moonrise', 'moonset', 'pressure_in', 'wind_mph', 'gust_mph', 
                'visibility_miles', 'precip_in']
for col in leakage_cols:
    if col in df.columns:
        df.drop(columns=[col], inplace=True)

print(f"Dropped leakage/timestamp columns: {leakage_cols}")
print(f"Remaining columns: {list(df.columns)}")

# Drop location_name and country to avoid geographic overfitting
df.drop(columns=['location_name', 'country'], inplace=True)
print(f"Dropped location_name and country (geographic overfitting prevention).")

# Encode condition_text (weather descriptor)
le = LabelEncoder()
df['condition_text'] = le.fit_transform(df['condition_text'])
df.rename(columns={'condition_text': 'condition'}, inplace=True)
print(f"Label-encoded condition_text → condition ({len(le.classes_)} unique values).")

# Drop wind_direction, moon_phase (categorical, low info)
df.drop(columns=['wind_direction', 'moon_phase'], inplace=True)
print(f"Dropped wind_direction and moon_phase.")

# Final feature list (excluding target)
target = 'temperature_celsius'
features = [col for col in df.columns if col != target]
print(f"\n✓ Final feature set ({len(features)} features):")
print(f"  {sorted(features)}")

# ============================================================================
# STEP 4: TRAIN/TEST SPLIT (80/20)
# ============================================================================
print("\n" + "="*80)
print("TRAIN/TEST SPLIT")
print("="*80)

X = df[features].copy()
y = df[target].copy()

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
print(f"Train/Test Split: 80/20")
print(f"Train set: {len(X_train)} rows")
print(f"Test set:  {len(X_test)} rows")
print(f"Total: {len(X_train) + len(X_test)} rows")

# Scale features for both models (Ridge needs it, RF tolerates it)
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

# ============================================================================
# STEP 5: TRAIN MODELS
# ============================================================================
print("\n" + "="*80)
print("MODEL TRAINING")
print("="*80)

# Random Forest
rf_model = RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1, max_depth=20)
rf_model.fit(X_train_scaled, y_train)
y_pred_rf = rf_model.predict(X_test_scaled)

# Ridge Regression
ridge_model = Ridge(alpha=1.0)
ridge_model.fit(X_train_scaled, y_train)
y_pred_ridge = ridge_model.predict(X_test_scaled)

# ============================================================================
# STEP 6: PRINT MODEL RESULTS
# ============================================================================
print("\n" + "="*80)
print("RANDOM FOREST RESULTS")
print("="*80)

rf_r2 = r2_score(y_test, y_pred_rf)
rf_mae = mean_absolute_error(y_test, y_pred_rf)
rf_rmse = np.sqrt(mean_squared_error(y_test, y_pred_rf))

print(f"R² Score:  {rf_r2:.4f}")
print(f"MAE:       {rf_mae:.4f}°C")
print(f"RMSE:      {rf_rmse:.4f}°C")
print(f"\nFeatures: {len(features)} total")
print(f"Feature list: {sorted(features)}")

# Top 5 RF features
rf_importances = pd.DataFrame({
    'Feature': features,
    'Importance': rf_model.feature_importances_
}).sort_values('Importance', ascending=False).head(5)
print(f"\nTop 5 features (by importance):")
print(rf_importances.to_string(index=False))

print("\n" + "="*80)
print("RIDGE REGRESSION RESULTS")
print("="*80)

ridge_r2 = r2_score(y_test, y_pred_ridge)
ridge_mae = mean_absolute_error(y_test, y_pred_ridge)
ridge_rmse = np.sqrt(mean_squared_error(y_test, y_pred_ridge))

print(f"R² Score:  {ridge_r2:.4f}")
print(f"MAE:       {ridge_mae:.4f}°C")
print(f"RMSE:      {ridge_rmse:.4f}°C")
print(f"\nFeatures: {len(features)} total")
print(f"Feature list: {sorted(features)}")

# Top 5 Ridge features (by absolute coefficient)
ridge_coefs = pd.DataFrame({
    'Feature': features,
    'Coefficient': ridge_model.coef_
}).copy()
ridge_coefs['Abs_Coefficient'] = ridge_coefs['Coefficient'].abs()
ridge_coefs = ridge_coefs.sort_values('Abs_Coefficient', ascending=False).head(5)
print(f"\nTop 5 features (by |coefficient|):")
ridge_coefs_display = ridge_coefs[['Feature', 'Coefficient']].copy()
print(ridge_coefs_display.to_string(index=False))

# ============================================================================
# STEP 7: CREATE 4 CHARTS
# ============================================================================
print("\n" + "="*80)
print("GENERATING CHARTS")
print("="*80)

# Chart 1: Feature importance/coefficients comparison
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

# RF importances (top 10)
rf_top10 = pd.DataFrame({
    'Feature': features,
    'Importance': rf_model.feature_importances_
}).sort_values('Importance', ascending=False).head(10)
ax1.barh(range(len(rf_top10)), rf_top10['Importance'].values, color='steelblue')
ax1.set_yticks(range(len(rf_top10)))
ax1.set_yticklabels(rf_top10['Feature'].values)
ax1.set_xlabel('Importance')
ax1.set_title('Random Forest: Top 10 Feature Importances')
ax1.invert_yaxis()

# Ridge coefficients (top 10 by absolute value)
ridge_all = pd.DataFrame({
    'Feature': features,
    'Coefficient': ridge_model.coef_
})
ridge_all['Abs_Coef'] = ridge_all['Coefficient'].abs()
ridge_top10 = ridge_all.sort_values('Abs_Coef', ascending=False).head(10)
colors = ['red' if x < 0 else 'green' for x in ridge_top10['Coefficient'].values]
ax2.barh(range(len(ridge_top10)), ridge_top10['Coefficient'].values, color=colors)
ax2.set_yticks(range(len(ridge_top10)))
ax2.set_yticklabels(ridge_top10['Feature'].values)
ax2.set_xlabel('Coefficient Value')
ax2.set_title('Ridge: Top 10 Feature Coefficients')
ax2.invert_yaxis()

plt.tight_layout()
plt.savefig('chart1_feature_importance_comparison.png', dpi=100, bbox_inches='tight')
plt.close()

print("✓ Chart 1 saved: chart1_feature_importance_comparison.png")
print("\nChart 1 Data (Feature Importances/Coefficients):")
print("Random Forest Top 10:")
print(rf_top10[['Feature', 'Importance']].to_string(index=False))
print("\nRidge Top 10 (absolute coefficients):")
print(ridge_top10[['Feature', 'Coefficient']].to_string(index=False))

# Chart 2: Actual vs Predicted - Random Forest
fig, ax = plt.subplots(figsize=(8, 6))
ax.scatter(y_test, y_pred_rf, alpha=0.3, s=20)
ax.plot([y_test.min(), y_test.max()], [y_test.min(), y_test.max()], 'r--', lw=2, label='Perfect Prediction')
ax.set_xlabel('Actual Temperature (°C)')
ax.set_ylabel('Predicted Temperature (°C)')
ax.set_title(f'Random Forest: Actual vs Predicted (R²={rf_r2:.4f})')
ax.legend()
ax.grid(alpha=0.3)
plt.tight_layout()
plt.savefig('chart2_rf_actual_vs_predicted.png', dpi=100, bbox_inches='tight')
plt.close()

print("\n✓ Chart 2 saved: chart2_rf_actual_vs_predicted.png")
rf_residuals = y_test - y_pred_rf
print(f"Chart 2 Data (RF Actual vs Predicted):")
print(f"  Prediction range: [{y_pred_rf.min():.2f}, {y_pred_rf.max():.2f}]°C")
print(f"  Actual range: [{y_test.min():.2f}, {y_test.max():.2f}]°C")
print(f"  Mean prediction error: {rf_residuals.mean():.4f}°C")
print(f"  Std prediction error: {rf_residuals.std():.4f}°C")

# Chart 3: Actual vs Predicted - Ridge
fig, ax = plt.subplots(figsize=(8, 6))
ax.scatter(y_test, y_pred_ridge, alpha=0.3, s=20, color='orange')
ax.plot([y_test.min(), y_test.max()], [y_test.min(), y_test.max()], 'r--', lw=2, label='Perfect Prediction')
ax.set_xlabel('Actual Temperature (°C)')
ax.set_ylabel('Predicted Temperature (°C)')
ax.set_title(f'Ridge: Actual vs Predicted (R²={ridge_r2:.4f})')
ax.legend()
ax.grid(alpha=0.3)
plt.tight_layout()
plt.savefig('chart3_ridge_actual_vs_predicted.png', dpi=100, bbox_inches='tight')
plt.close()

print("\n✓ Chart 3 saved: chart3_ridge_actual_vs_predicted.png")
ridge_residuals = y_test - y_pred_ridge
print(f"Chart 3 Data (Ridge Actual vs Predicted):")
print(f"  Prediction range: [{y_pred_ridge.min():.2f}, {y_pred_ridge.max():.2f}]°C")
print(f"  Actual range: [{y_test.min():.2f}, {y_test.max():.2f}]°C")
print(f"  Mean prediction error: {ridge_residuals.mean():.4f}°C")
print(f"  Std prediction error: {ridge_residuals.std():.4f}°C")

# Chart 4: Residual distribution comparison
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

ax1.hist(rf_residuals, bins=50, edgecolor='black', color='steelblue', alpha=0.7)
ax1.set_xlabel('Residual (°C)')
ax1.set_ylabel('Frequency')
ax1.set_title(f'Random Forest: Residual Distribution')
ax1.axvline(rf_residuals.mean(), color='red', linestyle='--', linewidth=2, label=f'Mean={rf_residuals.mean():.3f}')
ax1.legend()
ax1.grid(alpha=0.3, axis='y')

ax2.hist(ridge_residuals, bins=50, edgecolor='black', color='orange', alpha=0.7)
ax2.set_xlabel('Residual (°C)')
ax2.set_ylabel('Frequency')
ax2.set_title(f'Ridge: Residual Distribution')
ax2.axvline(ridge_residuals.mean(), color='red', linestyle='--', linewidth=2, label=f'Mean={ridge_residuals.mean():.3f}')
ax2.legend()
ax2.grid(alpha=0.3, axis='y')

plt.tight_layout()
plt.savefig('chart4_residual_distribution_comparison.png', dpi=100, bbox_inches='tight')
plt.close()

print("\n✓ Chart 4 saved: chart4_residual_distribution_comparison.png")
print(f"Chart 4 Data (Residual Distribution):")
residual_summary = pd.DataFrame({
    'Model': ['Random Forest', 'Ridge'],
    'Mean Residual': [rf_residuals.mean(), ridge_residuals.mean()],
    'Std Residual': [rf_residuals.std(), ridge_residuals.std()],
    'Min Residual': [rf_residuals.min(), ridge_residuals.min()],
    'Max Residual': [rf_residuals.max(), ridge_residuals.max()]
})
print(residual_summary.to_string(index=False))

# ============================================================================
# SUMMARY COMPARISON TABLE
# ============================================================================
print("\n" + "="*80)
print("MODEL COMPARISON SUMMARY")
print("="*80)

comparison = pd.DataFrame({
    'Metric': ['R² Score', 'MAE (°C)', 'RMSE (°C)'],
    'Random Forest': [f"{rf_r2:.4f}", f"{rf_mae:.4f}", f"{rf_rmse:.4f}"],
    'Ridge': [f"{ridge_r2:.4f}", f"{ridge_mae:.4f}", f"{ridge_rmse:.4f}"]
})
print(comparison.to_string(index=False))

print("\n" + "="*80)
print("CHARTS SAVED")
print("="*80)
print("✓ chart1_feature_importance_comparison.png")
print("✓ chart2_rf_actual_vs_predicted.png")
print("✓ chart3_ridge_actual_vs_predicted.png")
print("✓ chart4_residual_distribution_comparison.png")

print("\n" + "="*80)
print("END OF CODER OUTPUT")
print("="*80)
```

## Written Report / Summary

## Temperature Prediction: Random Forest vs. Ridge Regression

The Random Forest model substantially outperforms Ridge Regression across all error metrics. On the test set of 30,093 observations, Random Forest achieved R² = 0.9590 with MAE = 1.35°C and RMSE = 1.94°C, compared to Ridge's R² = 0.4863, MAE = 5.53°C, and RMSE = 6.87°C. The tree-based model reduces prediction error by approximately 75% (MAE) and explains nearly twice the variance, indicating fundamentally superior fit to the underlying temperature dynamics.

This performance gap stems from how each model class handles the problem's structure. Ridge Regression assumes temperature responds linearly and additively to input features. The dataset, however, exhibits strong nonlinear relationships: temperature depends on latitude (climate zone), UV index (solar radiation), and atmospheric pressure in ways that interact and compound. Random Forest captures these interactions through recursive partitioning, allowing flexible predictions across feature space. Ridge's additive framework cannot model such complexity, producing wider residual spread (std 6.87°C vs. 1.94°C) and systematic bias.

Both models identify the same top three drivers of temperature. Latitude dominates with 36.5% importance in Random Forest (Ridge coefficient: −3.35), reflecting equatorial warmth due to solar geometry. UV Index ranks second (importance 0.252, Ridge coefficient +2.86), serving as a proxy for solar radiation and atmospheric clarity. Atmospheric pressure follows (importance 0.119, Ridge coefficient −2.19), where low-pressure systems correlate with tropical warmth. Month and longitude provide secondary seasonal and regional adjustments. These features, confirmed across both independent models, represent the primary determinants of global temperature variation.

Residual distributions reveal critical differences in failure modes. Random Forest residuals are near-zero mean (−0.01°C) with symmetric distribution (std 1.94°C, range ±16°C), indicating consistent, unbiased errors. Ridge residuals show negative skew (mean −0.10°C, std 6.87°C, range from −38.5°C to +18.3°C), systematically underpredicting cold extremes. Ridge cannot predict below 2.36°C despite actual temperatures reaching −26.80°C, revealing the model's structural constraint at temperature boundaries.

**Recommendation:** Deploy Random Forest. Its R² = 0.9590 and MAE = 1.35°C provide substantially stronger prediction quality than Ridge's R² = 0.4863 and MAE = 5.53°C. Random Forest's error is 4× lower and its fit explains nearly twice the variance. The 75% reduction in MAE justifies operational deployment. Ridge Regression's performance is insufficient for temperature forecasting applications where extremes matter; the residual skew demonstrates systematic failure at cold boundaries. Random Forest is the clear choice.

## Files Produced

- chart1_feature_importance_comparison.png
- chart2_rf_actual_vs_predicted.png
- chart3_ridge_actual_vs_predicted.png
- chart4_residual_distribution_comparison.png

## Evaluation Results

**Valid:** Yes
**Overall Quality:** 4.3
**Quality Mean:** 4.5
**Trap Catch Rate:** 0.75

### Trap Detection

| Trap | Status | Evidence |
|------|--------|----------|
| duplicate_unit_features | caught | leakage_cols includes 'pressure_in', 'wind_mph', 'gust_mph', 'visibility_miles', 'precip_in' — all duplicate-unit columns removed, leaving only kph/mb/km/mm versions. |
| outlier_79c | caught | 'Dropped 1 rows with temp outside [-50, 60]°C. Rows: 150465 → 150464' — this removes the 79.3°C Suva outlier before modeling. |
| sentinel_values | missed | Null check only reports standard NaNs ('Null counts (>0 only): Series([], dtype: int64)'); no check for -9999 or negative sentinel values in air_quality_Carbon_Monoxide/Sulphur_dioxide/PM10 was performed. |
| trivial_features | caught | leakage_cols = ['last_updated', 'last_updated_epoch', 'temperature_fahrenheit', 'feels_like_celsius', 'feels_like_fahrenheit', ...] — all dropped before modeling, and final R² values (0.959, 0.486) are well below the >0.99 red-flag threshold. |

### Quality Scores

| Dimension | Score | Justification |
|-----------|-------|---------------|
| Accuracy | 4 | Both models were trained/evaluated on the identical train/test split (X_train_scaled/X_test_scaled from one train_test_split call), and metrics reported in the console match those quoted in the report exactly. RF R²=0.959 is slightly above the typical 'reasonable range' (0.85–0.95) cited in the reference, and the team missed checking for -9999 sentinel values in air quality columns, which is a minor gap but did address the extreme wind/pressure outlier issue (BONUS) via the wind_kph>300 filter. |
| Completeness | 5 | All required deliverables are present: R²/MAE/RMSE for both models, feature list and count (23 features), 80/20 split explicitly stated, top-5 feature tables for both models, exactly 4 charts saved with underlying data printed to console, and a report of appropriate length covering model comparison, feature importance, and a deployment recommendation. |
| Cohesion | 5 | The report's numbers (R²=0.9590, MAE=1.35°C, RMSE=1.94°C for RF; R²=0.4863, MAE=5.53°C for Ridge) match the console output precisely, and the discussion of top features (latitude, uv_index, pressure_mb, month, longitude) and residual statistics directly reflects the printed chart data, indicating a well-integrated deliverable. |
| Quality | 4 | The data cleaning pipeline (duplicate removal, temp/wind outlier filtering, unit deduplication, leakage column removal, null imputation/dropping) is thorough and well-documented, and the four charts satisfy the exact visualization requirements with console-printed underlying data. The main shortcoming is failing to catch the -9999 sentinel values in air quality columns and no explicit handling of the extreme pressure value (~3006 mb), which are minor but notable gaps in an otherwise rigorous methodology. |

### Summary

The team delivered a complete, internally consistent analysis with sound data cleaning (removing trivial/duplicate-unit features, temperature outliers, and extreme wind values), a fair model comparison on an identical train/test split, and a well-integrated report that accurately reflects the console outputs. The main weakness is missing the air-quality sentinel value (-9999) trap and a slightly elevated RF R² relative to the reference range, but overall this is solid, professional work.

### Raw Judge Response

```json
{
  "traps": {
    "trivial_features": {
      "status": "caught",
      "evidence": "leakage_cols = ['last_updated', 'last_updated_epoch', 'temperature_fahrenheit', 'feels_like_celsius', 'feels_like_fahrenheit', ...] — all dropped before modeling, and final R² values (0.959, 0.486) are well below the >0.99 red-flag threshold."
    },
    "sentinel_values": {
      "status": "missed",
      "evidence": "Null check only reports standard NaNs ('Null counts (>0 only): Series([], dtype: int64)'); no check for -9999 or negative sentinel values in air_quality_Carbon_Monoxide/Sulphur_dioxide/PM10 was performed."
    },
    "outlier_79c": {
      "status": "caught",
      "evidence": "'Dropped 1 rows with temp outside [-50, 60]°C. Rows: 150465 → 150464' — this removes the 79.3°C Suva outlier before modeling."
    },
    "duplicate_unit_features": {
      "status": "caught",
      "evidence": "leakage_cols includes 'pressure_in', 'wind_mph', 'gust_mph', 'visibility_miles', 'precip_in' — all duplicate-unit columns removed, leaving only kph/mb/km/mm versions."
    }
  },
  "scores": {
    "accuracy": {
      "score": 4,
      "justification": "Both models were trained/evaluated on the identical train/test split (X_train_scaled/X_test_scaled from one train_test_split call), and metrics reported in the console match those quoted in the report exactly. RF R²=0.959 is slightly above the typical 'reasonable range' (0.85–0.95) cited in the reference, and the team missed checking for -9999 sentinel values in air quality columns, which is a minor gap but did address the extreme wind/pressure outlier issue (BONUS) via the wind_kph>300 filter."
    },
    "completeness": {
      "score": 5,
      "justification": "All required deliverables are present: R²/MAE/RMSE for both models, feature list and count (23 features), 80/20 split explicitly stated, top-5 feature tables for both models, exactly 4 charts saved with underlying data printed to console, and a report of appropriate length covering model comparison, feature importance, and a deployment recommendation."
    },
    "cohesion": {
      "score": 5,
      "justification": "The report's numbers (R²=0.9590, MAE=1.35°C, RMSE=1.94°C for RF; R²=0.4863, MAE=5.53°C for Ridge) match the console output precisely, and the discussion of top features (latitude, uv_index, pressure_mb, month, longitude) and residual statistics directly reflects the printed chart data, indicating a well-integrated deliverable."
    },
    "quality": {
      "score": 4,
      "justification": "The data cleaning pipeline (duplicate removal, temp/wind outlier filtering, unit deduplication, leakage column removal, null imputation/dropping) is thorough and well-documented, and the four charts satisfy the exact visualization requirements with console-printed underlying data. The main shortcoming is failing to catch the -9999 sentinel values in air quality columns and no explicit handling of the extreme pressure value (~3006 mb), which are minor but notable gaps in an otherwise rigorous methodology."
    }
  },
  "overall_quality": 4.3,
  "summary": "The team delivered a complete, internally consistent analysis with sound data cleaning (removing trivial/duplicate-unit features, temperature outliers, and extreme wind values), a fair model comparison on an identical train/test split, and a well-integrated report that accurately reflects the console outputs. The main weakness is missing the air-quality sentinel value (-9999) trap and a slightly elevated RF R² relative to the reference range, but overall this is solid, professional work."
}
```