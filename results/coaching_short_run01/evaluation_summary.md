# Control Agent Evaluation — coaching_short_run01

## Task Specification

> Using the Global Weather Repository CSV, produce:
> 1. Two ranked bar charts of the **top 10 hottest cities**, one by average and one by single hottest measurement temperature (celsius)
> 2. Two ranked bar charts of the **top 10 hottest countries**, one by average and one by single hottest measurement temperature (celsius)
> 3. **Print the top 10 lists to the console** before plotting: for each of the 4 charts, print the ranked names and their temperature values (e.g., "1. Paris: 25.2 deg C")
> 4. A **100-word summary** for a non-technical audience explaining the rankings and any notable patterns
>
> Column reference: cities are in `location_name`, countries in `country`, temperature in `temperature_celsius`.

## Console Output (from last successful code execution)

```text
Data Quality: 150465 rows loaded → 0 nulls dropped, 1 duplicates dropped
Anomaly exclusion: 1 anomalous reading(s) excluded (Suva, 79.3°C, >18 std dev from location mean — likely sensor/data error)
Final: 150463 rows for analysis

=== COUNTRY NAME CONSOLIDATION ===
Bélgica → Belgium: 1 row(s) consolidated
Estonie → Estonia: 1 row(s) consolidated
Inde → India: 1 row(s) consolidated
Jemen → Yemen: 1 row(s) consolidated
Komoren → Comoros: 1 row(s) consolidated
Letonia → Latvia: 1 row(s) consolidated
Malásia → Malaysia: 1 row(s) consolidated
Marrocos → Morocco: 1 row(s) consolidated
Mexique → Mexico: 1 row(s) consolidated
Polônia → Poland: 1 row(s) consolidated
Saint-Vincent-et-les-Grenadines → Saint Vincent and the Grenadines: 1 row(s) consolidated
Saudi Arabien → Saudi Arabia: 1 row(s) consolidated
Südkorea → South Korea: 1 row(s) consolidated
Turkménistan → Turkmenistan: 1 row(s) consolidated
USA United States of America → United States of America: 3 row(s) consolidated
Гватемала → Guatemala: 1 row(s) consolidated
Польша → Poland: 1 row(s) consolidated
Турция → Turkey: 1 row(s) consolidated
كولومبيا → Colombia: 1 row(s) consolidated
火鸡 → Turkey: 1 row(s) consolidated

=== Top 10 Hottest Cities (Average Temperature) ===
1. Ar Riyadh: 45.0 deg C
2. Kuwait: 44.4 deg C
3. Morocco City: 40.3 deg C
4. Krasnyy Turkmenistan: 37.8 deg C
5. Yanngwa: 33.2 deg C
6. Doha: 32.4 deg C
7. Abu Dhabi: 32.3 deg C
8. Phnom Penh: 32.1 deg C
9. Bangkok: 32.0 deg C
10. Muscat: 31.8 deg C

=== Top 10 Hottest Cities (Single Hottest Measurement) ===
1. Kuwait City: 49.2 deg C
2. Baghdad: 49.1 deg C
3. Djibouti: 47.1 deg C
4. Abu Dhabi: 46.4 deg C
5. Doha: 46.3 deg C
6. Muscat: 46.3 deg C
7. Riyadh: 46.3 deg C
8. Manama: 45.3 deg C
9. Ar Riyadh: 45.0 deg C
10. Islamabad: 45.0 deg C

=== Top 10 Hottest Countries (Average Temperature) ===
1. Qatar: 32.4 deg C
2. United Arab Emirates: 32.3 deg C
3. Cambodia: 32.1 deg C
4. Oman: 31.8 deg C
5. Djibouti: 31.4 deg C
6. Bangladesh: 31.3 deg C
7. Thailand: 31.2 deg C
8. Kuwait: 31.0 deg C
9. Myanmar: 30.9 deg C
10. Saudi Arabia: 30.7 deg C

=== Top 10 Hottest Countries (Single Hottest Measurement) ===
1. Kuwait: 49.2 deg C
2. Iraq: 49.1 deg C
3. Djibouti: 47.1 deg C
4. United Arab Emirates: 46.4 deg C
5. Qatar: 46.3 deg C
6. Oman: 46.3 deg C
7. Saudi Arabia: 46.3 deg C
8. Bahrain: 45.3 deg C
9. Chad: 45.0 deg C
10. Pakistan: 45.0 deg C

Saved: top10_cities_avg_temp.png
Saved: top10_cities_max_temp.png
Saved: top10_countries_avg_temp.png
Saved: top10_countries_max_temp.png

✓ All 4 charts regenerated from corrected data and saved.
```

## Final Code (last successful execution)

```python
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# Load dataset
df = pd.read_csv('/Users/hellligkeit/Documents/FS/Masterthesis/MAS/data/global_weather.csv')

# Data quality checks
initial_rows = len(df)
df_clean = df.dropna(subset=['temperature_celsius', 'location_name', 'country'])
nulls_dropped = initial_rows - len(df_clean)
df_clean = df_clean.drop_duplicates(subset=['country', 'location_name', 'temperature_celsius', 'last_updated'])
duplicates_dropped = len(df) - nulls_dropped - len(df_clean)

# Exclude Suva's anomalous reading (79.3°C, >18 std dev from location mean)
suva_before = len(df_clean[df_clean['location_name'] == 'Suva'])
df_clean = df_clean[~((df_clean['location_name'] == 'Suva') & (df_clean['temperature_celsius'] > 50))]
suva_excluded = suva_before - len(df_clean[df_clean['location_name'] == 'Suva'])

final_rows = len(df_clean)

print(f"Data Quality: {initial_rows} rows loaded → {nulls_dropped} nulls dropped, {duplicates_dropped} duplicates dropped")
print(f"Anomaly exclusion: {suva_excluded} anomalous reading(s) excluded (Suva, 79.3°C, >18 std dev from location mean — likely sensor/data error)")
print(f"Final: {final_rows} rows for analysis\n")

# Country name consolidation mapping (variants → canonical English names)
country_mapping = {
    'Bélgica': 'Belgium',
    'Estonie': 'Estonia',
    'Inde': 'India',
    'Jemen': 'Yemen',
    'Komoren': 'Comoros',
    'Letonia': 'Latvia',
    'Malásia': 'Malaysia',
    'Marrocos': 'Morocco',
    'Mexique': 'Mexico',
    'Polônia': 'Poland',
    'Saint-Vincent-et-les-Grenadines': 'Saint Vincent and the Grenadines',
    'Saudi Arabien': 'Saudi Arabia',
    'Südkorea': 'South Korea',
    'Turkménistan': 'Turkmenistan',
    'USA United States of America': 'United States of America',
    'Гватемала': 'Guatemala',
    'Польша': 'Poland',
    'Турция': 'Turkey',
    'كولومبيا': 'Colombia',
    '火鸡': 'Turkey'
}

# Apply consolidation mapping
df_clean['country'] = df_clean['country'].replace(country_mapping)

# Report consolidation changes
print("=== COUNTRY NAME CONSOLIDATION ===")
for variant, canonical in country_mapping.items():
    variant_count = len(df[df['country'] == variant])
    if variant_count > 0:
        print(f"{variant} → {canonical}: {variant_count} row(s) consolidated")
print()

# ===== CITIES: AVERAGE TEMPERATURE =====
cities_avg = df_clean.groupby('location_name')['temperature_celsius'].mean().sort_values(ascending=False).head(10)
print("=== Top 10 Hottest Cities (Average Temperature) ===")
for rank, (city, temp) in enumerate(cities_avg.items(), 1):
    print(f"{rank}. {city}: {temp:.1f} deg C")

# ===== CITIES: MAXIMUM TEMPERATURE (Suva excluded) =====
cities_max = df_clean.groupby('location_name')['temperature_celsius'].max().sort_values(ascending=False).head(10)
print("\n=== Top 10 Hottest Cities (Single Hottest Measurement) ===")
for rank, (city, temp) in enumerate(cities_max.items(), 1):
    print(f"{rank}. {city}: {temp:.1f} deg C")

# ===== COUNTRIES: AVERAGE TEMPERATURE =====
countries_avg = df_clean.groupby('country')['temperature_celsius'].mean().sort_values(ascending=False).head(10)
print("\n=== Top 10 Hottest Countries (Average Temperature) ===")
for rank, (country, temp) in enumerate(countries_avg.items(), 1):
    print(f"{rank}. {country}: {temp:.1f} deg C")

# ===== COUNTRIES: MAXIMUM TEMPERATURE (Suva/Fiji Islands excluded) =====
countries_max = df_clean.groupby('country')['temperature_celsius'].max().sort_values(ascending=False).head(10)
print("\n=== Top 10 Hottest Countries (Single Hottest Measurement) ===")
for rank, (country, temp) in enumerate(countries_max.items(), 1):
    print(f"{rank}. {country}: {temp:.1f} deg C")

# ===== CHARTS =====
# Chart 1: Cities Average
fig, ax = plt.subplots(figsize=(10, 6))
ax.barh(range(len(cities_avg)), cities_avg.values, color='coral')
ax.set_yticks(range(len(cities_avg)))
ax.set_yticklabels(cities_avg.index)
ax.invert_yaxis()
ax.set_xlabel('Average Temperature (°C)', fontsize=11)
ax.set_title('Top 10 Hottest Cities — Average Temperature (°C)', fontsize=12, fontweight='bold')
ax.grid(axis='x', alpha=0.3)
for i, v in enumerate(cities_avg.values):
    ax.text(v + 0.2, i, f'{v:.1f}', va='center', fontsize=9)
plt.tight_layout()
plt.savefig('top10_cities_avg_temp.png', dpi=300, bbox_inches='tight')
plt.close()

# Chart 2: Cities Max
fig, ax = plt.subplots(figsize=(10, 6))
ax.barh(range(len(cities_max)), cities_max.values, color='orangered')
ax.set_yticks(range(len(cities_max)))
ax.set_yticklabels(cities_max.index)
ax.invert_yaxis()
ax.set_xlabel('Maximum Temperature (°C)', fontsize=11)
ax.set_title('Top 10 Hottest Cities — Single Hottest Measurement (°C)', fontsize=12, fontweight='bold')
ax.grid(axis='x', alpha=0.3)
for i, v in enumerate(cities_max.values):
    ax.text(v + 0.2, i, f'{v:.1f}', va='center', fontsize=9)
plt.tight_layout()
plt.savefig('top10_cities_max_temp.png', dpi=300, bbox_inches='tight')
plt.close()

# Chart 3: Countries Average
fig, ax = plt.subplots(figsize=(10, 6))
ax.barh(range(len(countries_avg)), countries_avg.values, color='lightcoral')
ax.set_yticks(range(len(countries_avg)))
ax.set_yticklabels(countries_avg.index)
ax.invert_yaxis()
ax.set_xlabel('Average Temperature (°C)', fontsize=11)
ax.set_title('Top 10 Hottest Countries — Average Temperature (°C)', fontsize=12, fontweight='bold')
ax.grid(axis='x', alpha=0.3)
for i, v in enumerate(countries_avg.values):
    ax.text(v + 0.2, i, f'{v:.1f}', va='center', fontsize=9)
plt.tight_layout()
plt.savefig('top10_countries_avg_temp.png', dpi=300, bbox_inches='tight')
plt.close()

# Chart 4: Countries Max
fig, ax = plt.subplots(figsize=(10, 6))
ax.barh(range(len(countries_max)), countries_max.values, color='darkred')
ax.set_yticks(range(len(countries_max)))
ax.set_yticklabels(countries_max.index)
ax.invert_yaxis()
ax.set_xlabel('Maximum Temperature (°C)', fontsize=11)
ax.set_title('Top 10 Hottest Countries — Single Hottest Measurement (°C)', fontsize=12, fontweight='bold')
ax.grid(axis='x', alpha=0.3)
for i, v in enumerate(countries_max.values):
    ax.text(v + 0.2, i, f'{v:.1f}', va='center', fontsize=9)
plt.tight_layout()
plt.savefig('top10_countries_max_temp.png', dpi=300, bbox_inches='tight')
plt.close()

print("\nSaved: top10_cities_avg_temp.png")
print("Saved: top10_cities_max_temp.png")
print("Saved: top10_countries_avg_temp.png")
print("Saved: top10_countries_max_temp.png")
print("\n✓ All 4 charts regenerated from corrected data and saved.")
```

## Written Report / Summary

(your report here)

## Files Produced

- top10_cities_avg_temp.png
- top10_cities_max_temp.png
- top10_countries_avg_temp.png
- top10_countries_max_temp.png

## Evaluation Results

**Valid:** Yes
**Overall Quality:** 2.0
**Quality Mean:** 2.0
**Trap Catch Rate:** 0.667

### Trap Detection

| Trap | Status | Evidence |
|------|--------|----------|
| city_name_duplicates | missed | Printed top 10 hottest cities by average still shows '1. Ar Riyadh: 45.0 deg C' and '2. Kuwait: 44.4 deg C' — the single-observation duplicates of Riyadh and Kuwait City were never merged or removed. |
| country_name_duplicates | caught | country_mapping dict maps 'Saudi Arabien'→'Saudi Arabia', 'Marrocos'→'Morocco', 'Turkménistan'→'Turkmenistan', 'Турция'→'Turkey'; none of these variant names appear in the printed top 10 hottest countries by average list. |
| outlier_79c | caught | "Anomaly exclusion: 1 anomalous reading(s) excluded (Suva, 79.3°C, >18 std dev from location mean — likely sensor/data error)" and Suva does not appear in the printed max-city list. |

### Quality Scores

| Dimension | Score | Justification |
|-----------|-------|---------------|
| Accuracy | 3 | The team correctly identified and removed the Suva 79.3°C outlier and merged non-English country name variants (fixing the country-average trap), but failed to catch the analogous city-name duplicate issue, leaving 'Ar Riyadh' and 'Kuwait' as the top 2 hottest cities by average — a clear artifact of single-observation entries that undermines that specific chart's validity. |
| Completeness | 2 | All 4 required charts were saved and all 4 top-10 lists were printed to console as required, but the written 100-word non-technical summary — an explicitly required deliverable — is entirely absent from the submission (placeholder text only). |
| Cohesion | 1 | There is no written report connecting the code outputs to a narrative; the report section contains only a placeholder, making it impossible to assess how (or whether) the team intended to explain results to a non-technical audience. |
| Quality | 2 | The data cleaning methodology (outlier removal, country name consolidation) shows real effort and reasonable judgment, but the missed city-duplicate trap and the complete absence of the required summary substantially reduce the overall quality and usability of the deliverable. |

### Summary

The team executed solid data-cleaning steps for two of the three known traps (outlier removal and country-name consolidation) and delivered all 4 charts plus console-printed rankings, but missed the city-name duplicate trap (Ar Riyadh/Kuwait skewing the average-city ranking) and failed to produce the required 100-word summary, leaving the deliverable incomplete and disjointed.

### Raw Judge Response

```json
{
  "traps": {
    "outlier_79c": {
      "status": "caught",
      "evidence": "\"Anomaly exclusion: 1 anomalous reading(s) excluded (Suva, 79.3°C, >18 std dev from location mean — likely sensor/data error)\" and Suva does not appear in the printed max-city list."
    },
    "country_name_duplicates": {
      "status": "caught",
      "evidence": "country_mapping dict maps 'Saudi Arabien'→'Saudi Arabia', 'Marrocos'→'Morocco', 'Turkménistan'→'Turkmenistan', 'Турция'→'Turkey'; none of these variant names appear in the printed top 10 hottest countries by average list."
    },
    "city_name_duplicates": {
      "status": "missed",
      "evidence": "Printed top 10 hottest cities by average still shows '1. Ar Riyadh: 45.0 deg C' and '2. Kuwait: 44.4 deg C' — the single-observation duplicates of Riyadh and Kuwait City were never merged or removed."
    }
  },
  "scores": {
    "accuracy": {
      "score": 3,
      "justification": "The team correctly identified and removed the Suva 79.3°C outlier and merged non-English country name variants (fixing the country-average trap), but failed to catch the analogous city-name duplicate issue, leaving 'Ar Riyadh' and 'Kuwait' as the top 2 hottest cities by average — a clear artifact of single-observation entries that undermines that specific chart's validity."
    },
    "completeness": {
      "score": 2,
      "justification": "All 4 required charts were saved and all 4 top-10 lists were printed to console as required, but the written 100-word non-technical summary — an explicitly required deliverable — is entirely absent from the submission (placeholder text only)."
    },
    "cohesion": {
      "score": 1,
      "justification": "There is no written report connecting the code outputs to a narrative; the report section contains only a placeholder, making it impossible to assess how (or whether) the team intended to explain results to a non-technical audience."
    },
    "quality": {
      "score": 2,
      "justification": "The data cleaning methodology (outlier removal, country name consolidation) shows real effort and reasonable judgment, but the missed city-duplicate trap and the complete absence of the required summary substantially reduce the overall quality and usability of the deliverable."
    }
  },
  "overall_quality": 2.0,
  "summary": "The team executed solid data-cleaning steps for two of the three known traps (outlier removal and country-name consolidation) and delivered all 4 charts plus console-printed rankings, but missed the city-name duplicate trap (Ar Riyadh/Kuwait skewing the average-city ranking) and failed to produce the required 100-word summary, leaving the deliverable incomplete and disjointed."
}
```