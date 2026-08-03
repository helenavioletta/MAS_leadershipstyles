# Model Results & Metrics

## Dataset Overview
- **Total rows:** 150465
- **Features after preparation:** 98
- **Target variable:** temperature_celsius
- **Temperature range (raw data):** -29.80 to 79.30 deg C
- **Duplicates found:** 0
- **Impossible temps identified:** 1

## Train/Test Split
- **Training set:** 120372 rows (80%)
- **Test set:** 30093 rows (20%)
- **Random seed:** 42 (reproducible)

## Random Forest Model Performance
| Metric | Training | Test |
|--------|----------|------|
| R² | 0.9810 | 0.9278 |
| RMSE (deg C) | N/A | 2.5833 |
| MAE (deg C) | N/A | 1.6980 |

### Random Forest Top 15 Features by Importance

| Rank | Feature | Importance |
|------|---------|------------|
| 1 | latitude | 0.357886 |
| 10 | uv_index | 0.295024 |
| 5 | pressure_mb | 0.131821 |
| 2 | longitude | 0.060741 |
| 7 | humidity | 0.039180 |
| 12 | air_quality_Carbon_Monoxide | 0.017529 |
| 15 | air_quality_Sulphur_dioxide | 0.013174 |
| 13 | air_quality_Ozone | 0.011367 |
| 4 | wind_degree | 0.009374 |
| 14 | air_quality_Nitrogen_dioxide | 0.009119 |
| 17 | air_quality_PM10 | 0.008189 |
| 16 | air_quality_PM2.5 | 0.006774 |
| 8 | cloud | 0.006240 |
| 3 | wind_kph | 0.005302 |
| 11 | gust_kph | 0.004781 |


## Ridge Regression Model Performance
| Metric | Training | Test |
|--------|----------|------|
| R² | 0.5136 | 0.4153 |
| RMSE (deg C) | N/A | 7.3529 |
| MAE (deg C) | N/A | 5.2092 |

### Ridge Regression Top 15 Coefficients (by magnitude)

| Rank | Feature | Coefficient | Abs Value |
|------|---------|-------------|----------|
| 22 | condition_text_Blowing snow | -12.730538 | 12.730538 |
| 61 | condition_text_Patchy light rain with thunder | 11.055732 | 11.055732 |
| 70 | condition_text_Severe sandstorm | 10.762379 | 10.762379 |
| 75 | condition_text_Thundery outbreaks possible | 10.708516 | 10.708516 |
| 26 | condition_text_Dust storm | 10.493693 | 10.493693 |
| 47 | condition_text_Moderate or heavy rain with thunder | 10.403713 | 10.403713 |
| 41 | condition_text_Light snow | -10.277975 | 10.277975 |
| 69 | condition_text_Sandstorm | 10.257738 | 10.257738 |
| 68 | condition_text_Patchy snow possible | -9.999570 | 9.999570 |
| 64 | condition_text_Patchy moderate snow | -9.874232 | 9.874232 |
| 66 | condition_text_Patchy rain possible | 9.611486 | 9.611486 |
| 30 | condition_text_Haze | 9.533131 | 9.533131 |
| 46 | condition_text_Moderate or heavy rain shower | 9.114493 | 9.114493 |
| 38 | condition_text_Light rain shower | 8.633234 | 8.633234 |
| 74 | condition_text_Thundery outbreaks in nearby | 8.454060 | 8.454060 |


## Key Findings
1. **Better performing model:** Random Forest with R² = 0.9278
2. **Performance gap:** 0.5125 R² difference
3. **RMSE comparison:** RF = 2.5833 deg C, Ridge = 7.3529 deg C
4. **Overfitting indicator (RF train vs test R²):** 0.0532
5. **Overfitting indicator (Ridge train vs test R²):** 0.0983

## Data Quality Notes
- **Missing values:** 0% (no imputation needed)
- **Columns excluded:** 17 (redundant/leakage/identifiers)
  - Redundant pairs (unit conversions): wind_mph, pressure_in, precip_in, visibility_miles, gust_mph
  - Leakage: feels_like_celsius, feels_like_fahrenheit
  - Identifiers: country, location_name, timezone, etc.
- **Categorical columns encoded:** condition_text, wind_direction, moon_phase

## Visualizations Generated
1. chart_1_feature_importance_comparison.png - Side-by-side comparison of top features
2. chart_2_random_forest_actual_vs_predicted.png - Scatter plot for Random Forest
3. chart_3_ridge_actual_vs_predicted.png - Scatter plot for Ridge Regression
4. chart_4_residual_distribution_comparison.png - Residual analysis for both models
