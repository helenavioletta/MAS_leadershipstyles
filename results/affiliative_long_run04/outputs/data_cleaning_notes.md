# Data Cleaning & Preparation Notes

## Initial Data Assessment
- **Dataset shape:** 150,465 rows × 41 columns
- **Missing values:** 0% across all columns
- **Duplicate rows:** 0
- **Data quality:** Pristine (no quality issues found)

## Temperature Range Analysis
- **Minimum observed:** -29.80 deg C
- **Maximum observed:** 79.30 deg C
- **Physically impossible values (< -90 or > 70 deg C):** 1
- **Decision:** No outliers removed; data is within realistic global ranges

## Feature Engineering Decisions

### Columns Dropped (17 total)
Rationale for exclusion:

**Leakage (derived from target):**
- `feels_like_celsius` - Calculated from temperature and other weather factors
- `feels_like_fahrenheit` - Same as above, different unit
- *Reasoning:* Including these would create circular dependencies in the model

**Redundant columns (unit conversions of same measure):**
- `temperature_fahrenheit` - Duplicate of temperature_celsius
- `wind_mph` - Duplicate of wind_kph
- `pressure_in` - Duplicate of pressure_mb
- `precip_in` - Duplicate of precip_mm
- `visibility_miles` - Duplicate of visibility_km
- `gust_mph` - Duplicate of gust_kph
- *Reasoning:* Multiple measurements of same quantity; no new information

**Identifiers/metadata (not predictive):**
- `country` - Geographic label
- `location_name` - Geographic label
- `timezone` - Time information
- `last_updated_epoch` - Time identifier
- `last_updated` - Time identifier
- `sunrise` - Not useful for single-point prediction
- `sunset` - Not useful for single-point prediction
- `moonrise` - Not useful for single-point prediction
- `moonset` - Not useful for single-point prediction
- *Reasoning:* These identify observations but don't predict temperature

### Columns Retained (98 features after encoding)
All remaining numeric columns were retained as they represent actual weather conditions:
- **Wind:** wind_kph, wind_degree
- **Pressure:** pressure_mb
- **Precipitation:** precip_mm
- **Humidity:** humidity
- **Cloud cover:** cloud
- **Visibility:** visibility_km
- **UV Index:** uv_index
- **Air quality:** 6 pollutants + 2 indices
- **Geographic:** latitude, longitude
- **Moon phase:** moon_illumination

### Categorical Encoding
**Columns one-hot encoded:**
- `condition_text` - Weather conditions (sunny, rainy, cloudy, etc.)
- `wind_direction` - Cardinal/intercardinal directions (N, S, E, W, NE, etc.)
- `moon_phase` - Lunar phase descriptors

**Method:** pandas get_dummies() with drop_first=True to avoid multicollinearity

## Final Dataset
- **Rows:** 150,465
- **Features:** 98
- **Target:** temperature_celsius
- **No missing values:** All rows retained
- **Encoding:** One-hot encoding for 3 categorical columns

## Modeling Setup
- **Train/Test Split:** 80/20 (120,372 train / 30,093 test)
- **Random seed:** 42 (reproducible splits across models)
- **No scaling applied:** Random Forest is scale-invariant; Ridge benefits from scaling but dataset ranges are reasonable
