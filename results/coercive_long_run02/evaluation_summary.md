# Control Agent Evaluation — coercive_long_run02

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
DATA AUDIT
================================================================================
Initial shape: (150465, 41)
Duplicate rows: 0

Columns with nulls:
Series([], dtype: int64)

Rows dropped due to null temperature_celsius: 0
Shape after dropping null targets: (150465, 41)

IQR Outlier Detection on temperature_celsius:
  Q1=16.00, Q3=27.90, IQR=11.90
  Lower bound: -1.85, Upper bound: 45.75
  Outliers removed: 2646
Shape after outlier removal: (147819, 41)

================================================================================
LEAKAGE DETECTION & FEATURE CORRELATION
================================================================================

Top correlations with temperature_celsius:
  temperature_fahrenheit                  :   1.0000
  feels_like_celsius                      :   0.9782
  feels_like_fahrenheit                   :   0.9782
  uv_index                                :   0.4875
  humidity                                :  -0.3425
  latitude                                :  -0.3404
  pressure_in                             :  -0.2901
  pressure_mb                             :  -0.2895
  air_quality_Ozone                       :   0.2630
  longitude                               :   0.1723
  last_updated_epoch                      :  -0.1717
  air_quality_Nitrogen_dioxide            :  -0.1355
  cloud                                   :  -0.1290
  air_quality_PM10                        :   0.1131
  visibility_miles                        :   0.1120

Excluded columns:
  wind_mph                                : corr=  0.0956 (>0.95 threshold)
  feels_like_celsius                      : corr=  0.9782 (>0.95 threshold)
  temperature_fahrenheit                  : corr=  1.0000 (>0.95 threshold)
  precip_in                               : corr=  0.0284 (>0.95 threshold)
  pressure_in                             : corr= -0.2901 (>0.95 threshold)
  gust_mph                                : corr=  0.0859 (>0.95 threshold)
  visibility_miles                        : corr=  0.1120 (>0.95 threshold)
  feels_like_fahrenheit                   : corr=  0.9782 (>0.95 threshold)

Selected numeric feature columns (21):
   1. air_quality_Carbon_Monoxide
   2. air_quality_Nitrogen_dioxide
   3. air_quality_Ozone
   4. air_quality_PM10
   5. air_quality_PM2.5
   6. air_quality_Sulphur_dioxide
   7. air_quality_gb-defra-index
   8. air_quality_us-epa-index
   9. cloud
  10. gust_kph
  11. humidity
  12. last_updated_epoch
  13. latitude
  14. longitude
  15. moon_illumination
  16. precip_mm
  17. pressure_mb
  18. uv_index
  19. visibility_km
  20. wind_degree
  21. wind_kph

================================================================================
FEATURE MATRIX PREPARATION
================================================================================
Feature matrix shape: (147819, 21)
Target vector shape: (147819,)
Feature count: 21

================================================================================
TRAIN/TEST SPLIT
================================================================================
Split ratio: 80% train / 20% test
Train set: 118255 rows
Test set: 29564 rows
Total: 147819 rows

================================================================================
MODEL TRAINING
================================================================================

Training Random Forest Regressor...
Random Forest Results:
  R² Score: 0.9573
  MAE: 1.2766
  RMSE: 1.8154

Training Ridge Regression...
Ridge Regression Results:
  R² Score: 0.4628
  MAE: 5.2997
  RMSE: 6.4406

================================================================================
TOP 5 FEATURES
================================================================================

Random Forest Top 5 Features:
           Feature  Importance
          latitude    0.342562
          uv_index    0.285375
       pressure_mb    0.136482
last_updated_epoch    0.077787
         longitude    0.047636

Ridge Regression Top 5 Features (by |coefficient|):
                   Feature  Coefficient
                  uv_index     0.796499
                 precip_mm     0.594184
  air_quality_us-epa-index     0.563582
air_quality_gb-defra-index     0.276229
             visibility_km     0.226127

================================================================================
VISUALIZATION 1: FEATURE IMPORTANCE/COEFFICIENT COMPARISON
================================================================================

Top features from both models:
                     Feature  RF_Importance  Ridge_AbsCoef
                    latitude       0.342562   1.152271e-01
                    uv_index       0.285375   7.964992e-01
                 pressure_mb       0.136482   1.864402e-01
          last_updated_epoch       0.077787   1.407230e-08
                   longitude       0.047636   3.913871e-03
                    humidity       0.036191   5.049359e-02
 air_quality_Sulphur_dioxide       0.011207   3.370052e-03
 air_quality_Carbon_Monoxide       0.007708   4.425513e-04
air_quality_Nitrogen_dioxide       0.007371   2.813075e-02
                 wind_degree       0.007311   3.492167e-04

Visualization 1 saved: viz1_feature_importance_comparison.png

================================================================================
VISUALIZATION 2: ACTUAL VS PREDICTED (RANDOM FOREST)
================================================================================

Random Forest Prediction Summary:
       Metric     Value
Mean Residual -0.028298
 Std Residual  1.815180
Min Predicted -0.974800
Max Predicted 44.997034
   Min Actual -1.800000
   Max Actual 45.700000
Visualization 2 saved: viz2_rf_actual_vs_predicted.png

================================================================================
VISUALIZATION 3: ACTUAL VS PREDICTED (RIDGE)
================================================================================

Ridge Regression Prediction Summary:
       Metric     Value
Mean Residual -0.076236
 Std Residual  6.440141
Min Predicted  4.194628
Max Predicted 42.125695
   Min Actual -1.800000
   Max Actual 45.700000
Visualization 3 saved: viz3_ridge_actual_vs_predicted.png

================================================================================
VISUALIZATION 4: RESIDUAL DISTRIBUTION COMPARISON
================================================================================

Residual Distribution Comparison:
Statistic  RF_Residuals  Ridge_Residuals
     Mean     -0.028298        -0.076236
  Std Dev      1.815180         6.440141
      Min    -14.897247       -26.617657
      Max     13.055120        19.461215
   Median      0.031952         1.084767
Visualization 4 saved: viz4_residual_distribution_comparison.png

================================================================================
FINAL MODEL SUMMARY
================================================================================

          Metric Random Forest Ridge Regression
        R² Score        0.9573           0.4628
             MAE        1.2766           5.2997
            RMSE        1.8154           6.4406
   Feature Count            21               21
Train/Test Split         80/20            80/20
   Test Set Size         29564            29564

================================================================================
EXECUTION COMPLETE
================================================================================
✓ Data cleaned and audited
✓ Leakage columns identified and excluded
✓ 21 features selected
✓ Models trained on 80/20 split
✓ 4 visualizations generated and saved
✓ Full console output logged
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
# STEP 1: LOAD AND AUDIT DATA
# ============================================================================
df = pd.read_csv('/Users/hellligkeit/Documents/FS/Masterthesis/MAS/data/global_weather.csv')
print("=" * 80)
print("DATA AUDIT")
print("=" * 80)
print(f"Initial shape: {df.shape}")

# Check for duplicates
dupe_count = df.duplicated().sum()
print(f"Duplicate rows: {dupe_count}")
if dupe_count > 0:
    df = df.drop_duplicates()
    print(f"Shape after removing duplicates: {df.shape}")

# Check nulls
null_summary = df.isnull().sum()
null_cols = null_summary[null_summary > 0]
print(f"\nColumns with nulls:\n{null_cols}")

# Drop rows with null temperature_celsius
temp_nulls_before = df['temperature_celsius'].isnull().sum()
df = df.dropna(subset=['temperature_celsius'])
print(f"\nRows dropped due to null temperature_celsius: {temp_nulls_before}")
print(f"Shape after dropping null targets: {df.shape}")

# ============================================================================
# STEP 2: DETECT AND REMOVE OUTLIERS IN temperature_celsius (IQR method)
# ============================================================================
Q1 = df['temperature_celsius'].quantile(0.25)
Q3 = df['temperature_celsius'].quantile(0.75)
IQR = Q3 - Q1
lower_bound = Q1 - 1.5 * IQR
upper_bound = Q3 + 1.5 * IQR
outliers_before = df.shape[0]
df = df[(df['temperature_celsius'] >= lower_bound) & (df['temperature_celsius'] <= upper_bound)]
outliers_removed = outliers_before - df.shape[0]
print(f"\nIQR Outlier Detection on temperature_celsius:")
print(f"  Q1={Q1:.2f}, Q3={Q3:.2f}, IQR={IQR:.2f}")
print(f"  Lower bound: {lower_bound:.2f}, Upper bound: {upper_bound:.2f}")
print(f"  Outliers removed: {outliers_removed}")
print(f"Shape after outlier removal: {df.shape}")

# ============================================================================
# STEP 3: FEATURE SELECTION & LEAKAGE DETECTION
# ============================================================================
print("\n" + "=" * 80)
print("LEAKAGE DETECTION & FEATURE CORRELATION")
print("=" * 80)

# Select numeric columns for correlation analysis
numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
if 'temperature_celsius' in numeric_cols:
    numeric_cols.remove('temperature_celsius')

# Calculate correlation with target
corr_dict = {}
for col in numeric_cols:
    corr = df[col].corr(df['temperature_celsius'])
    corr_dict[col] = corr

# Sort by absolute correlation
corr_sorted = sorted(corr_dict.items(), key=lambda x: abs(x[1]), reverse=True)

# Print correlation table
print("\nTop correlations with temperature_celsius:")
for col, corr in corr_sorted[:15]:
    print(f"  {col:<40s}: {corr:>8.4f}")

# Define exclusions (leakage columns)
exclude_cols = [
    'temperature_fahrenheit',  # Direct conversion, not a separate measurement
    'feels_like_celsius',       # Derived from temperature
    'feels_like_fahrenheit',    # Derived from temperature
    'pressure_in',              # Duplicate of pressure_mb (unit conversion)
    'wind_mph',                 # Duplicate of wind_kph (unit conversion)
    'gust_mph',                 # Duplicate of gust_kph (unit conversion)
    'precip_in',                # Duplicate of precip_mm (unit conversion)
    'visibility_miles'          # Duplicate of visibility_km (unit conversion)
]

# Also exclude any col with |corr| > 0.95
high_corr_cols = [col for col, corr in corr_dict.items() if abs(corr) > 0.95]
exclude_cols.extend(high_corr_cols)
exclude_cols = list(set(exclude_cols))  # Remove duplicates

print(f"\nExcluded columns:")
for col in exclude_cols:
    if col in corr_dict:
        print(f"  {col:<40s}: corr={corr_dict[col]:>8.4f} (>0.95 threshold)")
    else:
        print(f"  {col:<40s}: unit conversion / proxy variable")

# Select features: numeric columns that are not excluded, plus location info
feature_cols = [col for col in numeric_cols if col not in exclude_cols]
feature_cols = sorted(feature_cols)

print(f"\nSelected numeric feature columns ({len(feature_cols)}):")
for i, col in enumerate(feature_cols, 1):
    print(f"  {i:2d}. {col}")

# ============================================================================
# STEP 4: BUILD FEATURE MATRIX AND PREPARE FOR MODELING
# ============================================================================
print("\n" + "=" * 80)
print("FEATURE MATRIX PREPARATION")
print("=" * 80)

X = df[feature_cols].copy()
y = df['temperature_celsius'].copy()

# Fill any remaining nulls in features with median
for col in X.columns:
    if X[col].isnull().sum() > 0:
        X[col].fillna(X[col].median(), inplace=True)

print(f"Feature matrix shape: {X.shape}")
print(f"Target vector shape: {y.shape}")
print(f"Feature count: {X.shape[1]}")

# ============================================================================
# STEP 5: TRAIN/TEST SPLIT
# ============================================================================
print("\n" + "=" * 80)
print("TRAIN/TEST SPLIT")
print("=" * 80)

test_ratio = 0.20
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=test_ratio, random_state=42
)

print(f"Split ratio: {(1-test_ratio):.0%} train / {test_ratio:.0%} test")
print(f"Train set: {X_train.shape[0]} rows")
print(f"Test set: {X_test.shape[0]} rows")
print(f"Total: {X_train.shape[0] + X_test.shape[0]} rows")

# ============================================================================
# STEP 6: TRAIN MODELS
# ============================================================================
print("\n" + "=" * 80)
print("MODEL TRAINING")
print("=" * 80)

# Train Random Forest
print("\nTraining Random Forest Regressor...")
rf_model = RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1, max_depth=20)
rf_model.fit(X_train, y_train)
rf_pred_test = rf_model.predict(X_test)
rf_r2 = r2_score(y_test, rf_pred_test)
rf_mae = mean_absolute_error(y_test, rf_pred_test)
rf_rmse = np.sqrt(mean_squared_error(y_test, rf_pred_test))

print(f"Random Forest Results:")
print(f"  R² Score: {rf_r2:.4f}")
print(f"  MAE: {rf_mae:.4f}")
print(f"  RMSE: {rf_rmse:.4f}")

# Train Ridge Regression
print("\nTraining Ridge Regression...")
ridge_model = Ridge(alpha=1.0, random_state=42)
ridge_model.fit(X_train, y_train)
ridge_pred_test = ridge_model.predict(X_test)
ridge_r2 = r2_score(y_test, ridge_pred_test)
ridge_mae = mean_absolute_error(y_test, ridge_pred_test)
ridge_rmse = np.sqrt(mean_squared_error(y_test, ridge_pred_test))

print(f"Ridge Regression Results:")
print(f"  R² Score: {ridge_r2:.4f}")
print(f"  MAE: {ridge_mae:.4f}")
print(f"  RMSE: {ridge_rmse:.4f}")

# ============================================================================
# STEP 7: FEATURE IMPORTANCE / TOP 5 FEATURES
# ============================================================================
print("\n" + "=" * 80)
print("TOP 5 FEATURES")
print("=" * 80)

# Random Forest: feature_importances_
rf_importance = pd.DataFrame({
    'Feature': X.columns,
    'Importance': rf_model.feature_importances_
}).sort_values('Importance', ascending=False)

print("\nRandom Forest Top 5 Features:")
rf_top5 = rf_importance.head(5).reset_index(drop=True)
print(rf_top5.to_string(index=False))

# Ridge Regression: absolute coefficient values
ridge_coef = pd.DataFrame({
    'Feature': X.columns,
    'Coefficient': ridge_model.coef_,
    'AbsCoefficient': np.abs(ridge_model.coef_)
}).sort_values('AbsCoefficient', ascending=False)

print("\nRidge Regression Top 5 Features (by |coefficient|):")
ridge_top5 = ridge_coef[['Feature', 'Coefficient']].head(5).reset_index(drop=True)
print(ridge_top5.to_string(index=False))

# ============================================================================
# STEP 8: VISUALIZATION 1 - FEATURE IMPORTANCE/COEFFICIENT COMPARISON
# ============================================================================
print("\n" + "=" * 80)
print("VISUALIZATION 1: FEATURE IMPORTANCE/COEFFICIENT COMPARISON")
print("=" * 80)

# Prepare data for comparison: top 10 from each model
rf_top10 = rf_importance.head(10)
ridge_top10 = ridge_coef.head(10)

# Create comparison table
comparison_features = list(set(rf_top10['Feature'].tolist() + ridge_top10['Feature'].tolist()))
comparison_data = []
for feat in comparison_features:
    rf_imp = rf_importance[rf_importance['Feature'] == feat]['Importance'].values
    ridge_abs_coef = ridge_coef[ridge_coef['Feature'] == feat]['AbsCoefficient'].values
    comparison_data.append({
        'Feature': feat,
        'RF_Importance': rf_imp[0] if len(rf_imp) > 0 else 0,
        'Ridge_AbsCoef': ridge_abs_coef[0] if len(ridge_abs_coef) > 0 else 0
    })

comparison_df = pd.DataFrame(comparison_data).sort_values('RF_Importance', ascending=False)
print("\nTop features from both models:")
print(comparison_df.head(10).to_string(index=False))

# Plot
fig, ax = plt.subplots(figsize=(12, 8))
x_pos = np.arange(10)
rf_vals = comparison_df.head(10)['RF_Importance'].values
ridge_vals = comparison_df.head(10)['Ridge_AbsCoef'].values
labels = comparison_df.head(10)['Feature'].values

ax.barh(x_pos - 0.2, rf_vals, 0.4, label='Random Forest', color='#2E86AB')
ax.barh(x_pos + 0.2, ridge_vals, 0.4, label='Ridge (|coef|)', color='#A23B72')
ax.set_yticks(x_pos)
ax.set_yticklabels(labels)
ax.set_xlabel('Importance / |Coefficient|')
ax.set_title('Feature Importance Comparison: Random Forest vs Ridge')
ax.legend()
ax.invert_yaxis()
plt.tight_layout()
plt.savefig('viz1_feature_importance_comparison.png', dpi=300, bbox_inches='tight')
plt.close()

print("\nVisualization 1 saved: viz1_feature_importance_comparison.png")

# ============================================================================
# STEP 9: VISUALIZATION 2 - ACTUAL VS PREDICTED (RANDOM FOREST)
# ============================================================================
print("\n" + "=" * 80)
print("VISUALIZATION 2: ACTUAL VS PREDICTED (RANDOM FOREST)")
print("=" * 80)

rf_residuals = y_test.values - rf_pred_test
rf_summary = pd.DataFrame({
    'Metric': ['Mean Residual', 'Std Residual', 'Min Predicted', 'Max Predicted', 'Min Actual', 'Max Actual'],
    'Value': [
        rf_residuals.mean(),
        rf_residuals.std(),
        rf_pred_test.min(),
        rf_pred_test.max(),
        y_test.min(),
        y_test.max()
    ]
})
print("\nRandom Forest Prediction Summary:")
print(rf_summary.to_string(index=False))

fig, ax = plt.subplots(figsize=(10, 8))
ax.scatter(y_test, rf_pred_test, alpha=0.5, s=20, color='#2E86AB')
min_val = min(y_test.min(), rf_pred_test.min())
max_val = max(y_test.max(), rf_pred_test.max())
ax.plot([min_val, max_val], [min_val, max_val], 'r--', lw=2, label='Perfect Prediction')
ax.set_xlabel('Actual Temperature (°C)')
ax.set_ylabel('Predicted Temperature (°C)')
ax.set_title(f'Random Forest: Actual vs Predicted (R²={rf_r2:.4f})')
ax.legend()
plt.tight_layout()
plt.savefig('viz2_rf_actual_vs_predicted.png', dpi=300, bbox_inches='tight')
plt.close()

print("Visualization 2 saved: viz2_rf_actual_vs_predicted.png")

# ============================================================================
# STEP 10: VISUALIZATION 3 - ACTUAL VS PREDICTED (RIDGE)
# ============================================================================
print("\n" + "=" * 80)
print("VISUALIZATION 3: ACTUAL VS PREDICTED (RIDGE)")
print("=" * 80)

ridge_residuals = y_test.values - ridge_pred_test
ridge_summary = pd.DataFrame({
    'Metric': ['Mean Residual', 'Std Residual', 'Min Predicted', 'Max Predicted', 'Min Actual', 'Max Actual'],
    'Value': [
        ridge_residuals.mean(),
        ridge_residuals.std(),
        ridge_pred_test.min(),
        ridge_pred_test.max(),
        y_test.min(),
        y_test.max()
    ]
})
print("\nRidge Regression Prediction Summary:")
print(ridge_summary.to_string(index=False))

fig, ax = plt.subplots(figsize=(10, 8))
ax.scatter(y_test, ridge_pred_test, alpha=0.5, s=20, color='#A23B72')
min_val = min(y_test.min(), ridge_pred_test.min())
max_val = max(y_test.max(), ridge_pred_test.max())
ax.plot([min_val, max_val], [min_val, max_val], 'r--', lw=2, label='Perfect Prediction')
ax.set_xlabel('Actual Temperature (°C)')
ax.set_ylabel('Predicted Temperature (°C)')
ax.set_title(f'Ridge: Actual vs Predicted (R²={ridge_r2:.4f})')
ax.legend()
plt.tight_layout()
plt.savefig('viz3_ridge_actual_vs_predicted.png', dpi=300, bbox_inches='tight')
plt.close()

print("Visualization 3 saved: viz3_ridge_actual_vs_predicted.png")

# ============================================================================
# STEP 11: VISUALIZATION 4 - RESIDUAL DISTRIBUTION COMPARISON
# ============================================================================
print("\n" + "=" * 80)
print("VISUALIZATION 4: RESIDUAL DISTRIBUTION COMPARISON")
print("=" * 80)

residual_comparison = pd.DataFrame({
    'Statistic': ['Mean', 'Std Dev', 'Min', 'Max', 'Median'],
    'RF_Residuals': [
        rf_residuals.mean(),
        rf_residuals.std(),
        rf_residuals.min(),
        rf_residuals.max(),
        np.median(rf_residuals)
    ],
    'Ridge_Residuals': [
        ridge_residuals.mean(),
        ridge_residuals.std(),
        ridge_residuals.min(),
        ridge_residuals.max(),
        np.median(ridge_residuals)
    ]
})
print("\nResidual Distribution Comparison:")
print(residual_comparison.to_string(index=False))

fig, axes = plt.subplots(1, 2, figsize=(14, 5))

axes[0].hist(rf_residuals, bins=50, color='#2E86AB', alpha=0.7, edgecolor='black')
axes[0].axvline(rf_residuals.mean(), color='red', linestyle='--', lw=2, label=f'Mean={rf_residuals.mean():.3f}')
axes[0].set_xlabel('Residuals (°C)')
axes[0].set_ylabel('Frequency')
axes[0].set_title('Random Forest Residual Distribution')
axes[0].legend()

axes[1].hist(ridge_residuals, bins=50, color='#A23B72', alpha=0.7, edgecolor='black')
axes[1].axvline(ridge_residuals.mean(), color='red', linestyle='--', lw=2, label=f'Mean={ridge_residuals.mean():.3f}')
axes[1].set_xlabel('Residuals (°C)')
axes[1].set_ylabel('Frequency')
axes[1].set_title('Ridge Residual Distribution')
axes[1].legend()

plt.tight_layout()
plt.savefig('viz4_residual_distribution_comparison.png', dpi=300, bbox_inches='tight')
plt.close()

print("Visualization 4 saved: viz4_residual_distribution_comparison.png")

# ============================================================================
# FINAL SUMMARY
# ============================================================================
print("\n" + "=" * 80)
print("FINAL MODEL SUMMARY")
print("=" * 80)

summary_table = pd.DataFrame({
    'Metric': ['R² Score', 'MAE', 'RMSE', 'Feature Count', 'Train/Test Split', 'Test Set Size'],
    'Random Forest': [f'{rf_r2:.4f}', f'{rf_mae:.4f}', f'{rf_rmse:.4f}', str(len(feature_cols)), '80/20', str(X_test.shape[0])],
    'Ridge Regression': [f'{ridge_r2:.4f}', f'{ridge_mae:.4f}', f'{ridge_rmse:.4f}', str(len(feature_cols)), '80/20', str(X_test.shape[0])]
})

print("\n" + summary_table.to_string(index=False))

print("\n" + "=" * 80)
print("EXECUTION COMPLETE")
print("=" * 80)
print(f"✓ Data cleaned and audited")
print(f"✓ Leakage columns identified and excluded")
print(f"✓ {len(feature_cols)} features selected")
print(f"✓ Models trained on 80/20 split")
print(f"✓ 4 visualizations generated and saved")
print(f"✓ Full console output logged")
```

## Written Report / Summary

The Random Forest model dramatically outperforms Ridge Regression across all evaluation metrics, achieving an R² of 0.9573 compared to Ridge's 0.4628—a 2.07-fold performance gap. Random Forest's mean absolute error of 1.2766°C is 4.15 times lower than Ridge's 5.2997°C, and its RMSE of 1.8154°C is 3.55 times superior to Ridge's 6.4406°C. This substantial divergence reflects fundamental differences in how the models capture temperature variation.

Ridge Regression assumes a linear relationship between features and target temperature. The data violates this assumption: temperature prediction is highly non-linear, driven by geographic location, temporal patterns, and complex interactions between weather variables that Ridge cannot learn. Ridge residuals show a standard deviation of 6.440°C with a range from −26.62 to 19.46°C, indicating systematic underfitting across the full temperature spectrum.

Random Forest captures non-linearity through decision trees and ensemble averaging. Its residual distribution is tight—standard deviation of 1.815°C, range −14.90 to 13.06°C—revealing that the model generalizes well to the test set. The tight distribution and near-zero mean residual (−0.028°C) indicate unbiased predictions with consistent accuracy.

Feature importance rankings reveal why the models diverge. Random Forest prioritizes latitude (0.343) and UV index (0.285) as the strongest predictors, followed by pressure (0.136), temporal epoch (0.078), and longitude (0.048). This reflects geography's dominant role in determining temperature zones and UV radiation's correlation with solar intensity. Ridge Regression ranks UV index highest (0.796) but emphasizes precipitation (0.594), air quality indices (0.564 and 0.276), and visibility (0.226). Ridge's emphasis on air quality and precipitation reflects its linear coefficients, which capture marginal correlations rather than predictive importance. These features show true correlation with temperature but contribute less to prediction than geographic and temporal structure.

The divergence confirms that tree-based ensembles are superior for this task: they exploit spatial and temporal heterogeneity that linear methods cannot capture. Ridge's reliance on air quality and precipitation—features with weaker individual predictive power—demonstrates its limitation in handling feature interactions and non-linearity.

**Deployment Recommendation:** Deploy the Random Forest model. Its R² of 0.9573 and MAE of 1.2766°C provide production-grade accuracy for temperature prediction. Ridge Regression's R² of 0.4628 indicates unacceptable underfitting (explaining less than 47% of variance) and is unsuitable for deployment. Random Forest's feature importance hierarchy—latitude, UV index, pressure—aligns with meteorological intuition, enhancing model interpretability and stakeholder trust.

## Files Produced

- viz1_feature_importance_comparison.png
- viz2_rf_actual_vs_predicted.png
- viz3_ridge_actual_vs_predicted.png
- viz4_residual_distribution_comparison.png

## Evaluation Results

**Valid:** Yes
**Overall Quality:** 4.2
**Quality Mean:** 4.25
**Trap Catch Rate:** 0.75

### Trap Detection

| Trap | Status | Evidence |
|------|--------|----------|
| duplicate_unit_features | caught | exclude_cols includes 'pressure_in', 'wind_mph', 'gust_mph', 'precip_in', 'visibility_miles' as 'Duplicate of ... (unit conversion)' |
| outlier_79c | caught | IQR Outlier Detection on temperature_celsius: Upper bound: 45.75, Outliers removed: 2646 -- this bound would exclude the 79.3°C Suva reading. |
| sentinel_values | missed | No mention in code or stdout of -9999 sentinel values in air_quality_Carbon_Monoxide, air_quality_Sulphur_dioxide, or air_quality_PM10; these columns were kept as-is without checking for sentinel/negative values. |
| trivial_features | caught | exclude_cols = ['temperature_fahrenheit', 'feels_like_celsius', 'feels_like_fahrenheit', ...] and stdout shows 'Excluded columns: temperature_fahrenheit : corr=1.0000 (>0.95 threshold)' |

### Quality Scores

| Dimension | Score | Justification |
|-----------|-------|---------------|
| Accuracy | 4 | Both models were trained and evaluated on the identical train/test split (random_state=42), and reported metrics (R²=0.9573/0.4628) are internally consistent with the printed feature importances and residual summaries. RF's R² is slightly above the typical 0.85-0.95 range but well below the 0.99 red-flag threshold, so the comparison remains valid and non-trivial. |
| Completeness | 4 | All 4 required PNGs were saved (viz1-viz4), console output includes R²/MAE/RMSE for both models, feature list (21 features), split ratio (80/20), and top-5 feature tables as required. The final code block was truncated mid-summary-table construction, but this occurred after all required deliverables were already produced, so completeness is only mildly affected. |
| Cohesion | 5 | The report directly cites the exact printed metrics (R²=0.9573, MAE=1.2766, RMSE=1.8154, Ridge R²=0.4628, feature importances 0.343/0.285/0.136/0.078/0.048) verbatim from stdout, demonstrating tight integration between code output and narrative. |
| Quality | 4 | The methodology is sound: proper leakage detection via correlation analysis, outlier removal via IQR, and consistent train/test evaluation. However, the team missed the sentinel-value trap (-9999 placeholders in air quality columns) and did not investigate feature-level physically impossible values (e.g., extreme wind/pressure readings), showing the data audit was not fully exhaustive. |

### Summary

The team executed a methodologically sound workflow: they correctly identified and excluded trivially correlated and duplicate-unit features, removed the 79.3°C outlier via IQR filtering, and used a consistent train/test split for a fair model comparison. Minor gaps include missing the -9999 sentinel value issue and no explicit handling of extreme feature-level outliers, but overall the report is well-integrated with the printed results and all required deliverables (4 charts, metrics, ~400-word report) were produced.

### Raw Judge Response

```json
{
  "traps": {
    "trivial_features": {"status": "caught", "evidence": "exclude_cols = ['temperature_fahrenheit', 'feels_like_celsius', 'feels_like_fahrenheit', ...] and stdout shows 'Excluded columns: temperature_fahrenheit : corr=1.0000 (>0.95 threshold)'"},
    "sentinel_values": {"status": "missed", "evidence": "No mention in code or stdout of -9999 sentinel values in air_quality_Carbon_Monoxide, air_quality_Sulphur_dioxide, or air_quality_PM10; these columns were kept as-is without checking for sentinel/negative values."},
    "outlier_79c": {"status": "caught", "evidence": "IQR Outlier Detection on temperature_celsius: Upper bound: 45.75, Outliers removed: 2646 -- this bound would exclude the 79.3°C Suva reading."},
    "duplicate_unit_features": {"status": "caught", "evidence": "exclude_cols includes 'pressure_in', 'wind_mph', 'gust_mph', 'precip_in', 'visibility_miles' as 'Duplicate of ... (unit conversion)'"}
  },
  "scores": {
    "accuracy": {"score": 4, "justification": "Both models were trained and evaluated on the identical train/test split (random_state=42), and reported metrics (R²=0.9573/0.4628) are internally consistent with the printed feature importances and residual summaries. RF's R² is slightly above the typical 0.85-0.95 range but well below the 0.99 red-flag threshold, so the comparison remains valid and non-trivial."},
    "completeness": {"score": 4, "justification": "All 4 required PNGs were saved (viz1-viz4), console output includes R²/MAE/RMSE for both models, feature list (21 features), split ratio (80/20), and top-5 feature tables as required. The final code block was truncated mid-summary-table construction, but this occurred after all required deliverables were already produced, so completeness is only mildly affected."},
    "cohesion": {"score": 5, "justification": "The report directly cites the exact printed metrics (R²=0.9573, MAE=1.2766, RMSE=1.8154, Ridge R²=0.4628, feature importances 0.343/0.285/0.136/0.078/0.048) verbatim from stdout, demonstrating tight integration between code output and narrative."},
    "quality": {"score": 4, "justification": "The methodology is sound: proper leakage detection via correlation analysis, outlier removal via IQR, and consistent train/test evaluation. However, the team missed the sentinel-value trap (-9999 placeholders in air quality columns) and did not investigate feature-level physically impossible values (e.g., extreme wind/pressure readings), showing the data audit was not fully exhaustive."}
  },
  "overall_quality": 4.2,
  "summary": "The team executed a methodologically sound workflow: they correctly identified and excluded trivially correlated and duplicate-unit features, removed the 79.3°C outlier via IQR filtering, and used a consistent train/test split for a fair model comparison. Minor gaps include missing the -9999 sentinel value issue and no explicit handling of extreme feature-level outliers, but overall the report is well-integrated with the printed results and all required deliverables (4 charts, metrics, ~400-word report) were produced."
}
```