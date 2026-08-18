# Control Agent Evaluation — coaching_short_run02

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
=== DATA LOAD & QUALITY CHECK ===
Dataset shape: (150465, 41)
Key columns present: True
Temperature dtype: float64
Nulls in key columns:
  country: 0
  location_name: 0
  temperature_celsius: 0

Rows dropped due to nulls: 0
Final working dataset: 150465 rows

=== COUNTRY NAME VARIANT DETECTION ===
Distinct countries before normalization: 211

Searching for language variants in raw data:
Variant groups found:
  India: ['Inde', 'India']
  Morocco: ['Morocco']
  Saudi Arabia: ['Saudi Arabia', 'Saudi Arabien']
  Turkey: ['Turkey', 'Turkmenistan', 'Turkménistan']

=== VERIFICATION OF EACH MAPPING ===
Saudi Arabien        → Saudi Arabia         | Rows affected:     1 | Remaining: 0
Marrocos             → Morocco              | Rows affected:     1 | Remaining: 0
Turkménistan         → Turkmenistan         | Rows affected:     1 | Remaining: 0
Türkiye              → Turkey               | Rows affected:     0 | Remaining: 0
Турция               → Turkey               | Rows affected:     1 | Remaining: 0
Inde                 → India                | Rows affected:     1 | Remaining: 0

Distinct countries after normalization: 206

Post-normalization check for 'Inde' and 'India':
  'Inde' rows: 0
  'India' rows: 772

======================================================================
TOP 10 HOTTEST CITIES (by AVERAGE temperature):
======================================================================
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

======================================================================
TOP 10 HOTTEST CITIES (by SINGLE HOTTEST MEASUREMENT):
======================================================================
1. Suva: 79.3 deg C
2. Kuwait City: 49.2 deg C
3. Baghdad: 49.1 deg C
4. Djibouti: 47.1 deg C
5. Abu Dhabi: 46.4 deg C
6. Doha: 46.3 deg C
7. Riyadh: 46.3 deg C
8. Muscat: 46.3 deg C
9. Manama: 45.3 deg C
10. Islamabad: 45.0 deg C

======================================================================
TOP 10 HOTTEST COUNTRIES (by AVERAGE temperature):
======================================================================
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

======================================================================
TOP 10 HOTTEST COUNTRIES (by SINGLE HOTTEST MEASUREMENT):
======================================================================
1. Fiji Islands: 79.3 deg C
2. Kuwait: 49.2 deg C
3. Iraq: 49.1 deg C
4. Djibouti: 47.1 deg C
5. United Arab Emirates: 46.4 deg C
6. Saudi Arabia: 46.3 deg C
7. Oman: 46.3 deg C
8. Qatar: 46.3 deg C
9. Bahrain: 45.3 deg C
10. Chad: 45.0 deg C

======================================================================
CHARTS SAVED
======================================================================
✓ top10_cities_avg_temp.png
✓ top10_cities_max_temp.png
✓ top10_countries_avg_temp.png
✓ top10_countries_max_temp.png

======================================================================
CONFIRMATION BLOCK
======================================================================
Total rows in dataset: 150465
Rows dropped due to nulls: 0
Rows used in analysis: 150465

Country name variants normalized: 6 mappings applied

Top entry from each list:
  Cities (avg): Ar Riyadh — 45.0°C
  Cities (max): Suva — 79.3°C
  Countries (avg): Qatar — 32.4°C
  Countries (max): Fiji Islands — 79.3°C

Charts saved:
  ✓ top10_cities_avg_temp.png
  ✓ top10_cities_max_temp.png
  ✓ top10_countries_avg_temp.png
  ✓ top10_countries_max_temp.png
======================================================================
```

## Final Code (last successful execution)

```python
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# Load the CSV
df = pd.read_csv('/Users/hellligkeit/Documents/FS/Masterthesis/MAS/data/global_weather.csv')

# Data quality check
print("=== DATA LOAD & QUALITY CHECK ===")
print(f"Dataset shape: {df.shape}")
print(f"Key columns present: {set(['country', 'location_name', 'temperature_celsius']).issubset(set(df.columns))}")
print(f"Temperature dtype: {df['temperature_celsius'].dtype}")
print(f"Nulls in key columns:")
print(f"  country: {df['country'].isnull().sum()}")
print(f"  location_name: {df['location_name'].isnull().sum()}")
print(f"  temperature_celsius: {df['temperature_celsius'].isnull().sum()}")

# Drop rows with nulls in key columns
df_clean = df[['country', 'location_name', 'temperature_celsius']].dropna()
rows_dropped = len(df) - len(df_clean)
print(f"\nRows dropped due to nulls: {rows_dropped}")
print(f"Final working dataset: {len(df_clean)} rows")

# Investigate country name variants
print("\n=== COUNTRY NAME VARIANT DETECTION ===")
print(f"Distinct countries before normalization: {df_clean['country'].nunique()}")

# Scan for problematic variants
unique_countries = sorted(df_clean['country'].unique())
print("\nSearching for language variants in raw data:")
variants_found = {}
for country in unique_countries:
    lower = country.lower().strip()
    if 'saudi' in lower:
        variants_found.setdefault('Saudi Arabia', []).append(country)
    elif 'moroc' in lower:
        variants_found.setdefault('Morocco', []).append(country)
    elif 'turk' in lower:
        variants_found.setdefault('Turkey', []).append(country)
    elif 'inde' in lower or 'india' in lower:
        variants_found.setdefault('India', []).append(country)
    elif 'turkmen' in lower:
        variants_found.setdefault('Turkmenistan', []).append(country)

print("Variant groups found:")
for key, variants in sorted(variants_found.items()):
    print(f"  {key}: {variants}")

# Build complete normalization map
normalization_map = {
    'Saudi Arabien': 'Saudi Arabia',
    'Marrocos': 'Morocco',
    'Turkménistan': 'Turkmenistan',
    'Türkiye': 'Turkey',
    'Турция': 'Turkey',
    'Inde': 'India',
}

# Apply normalization and verify each mapping
print(f"\n=== VERIFICATION OF EACH MAPPING ===")
df_clean['country_normalized'] = df_clean['country'].copy()

for old_name, new_name in normalization_map.items():
    before = (df_clean['country_normalized'] == old_name).sum()
    df_clean.loc[df_clean['country_normalized'] == old_name, 'country_normalized'] = new_name
    after = (df_clean['country_normalized'] == old_name).sum()
    print(f"{old_name:20} → {new_name:20} | Rows affected: {before:5} | Remaining: {after}")

print(f"\nDistinct countries after normalization: {df_clean['country_normalized'].nunique()}")

# Verify Inde and India are now consolidated
print(f"\nPost-normalization check for 'Inde' and 'India':")
inde_count = (df_clean['country_normalized'] == 'Inde').sum()
india_count = (df_clean['country_normalized'] == 'India').sum()
print(f"  'Inde' rows: {inde_count}")
print(f"  'India' rows: {india_count}")

# Compute four aggregations with normalized country
city_avg = df_clean.groupby('location_name')['temperature_celsius'].mean().sort_values(ascending=False).head(10)
city_max = df_clean.groupby('location_name')['temperature_celsius'].max().sort_values(ascending=False).head(10)
country_avg = df_clean.groupby('country_normalized')['temperature_celsius'].mean().sort_values(ascending=False).head(10)
country_max = df_clean.groupby('country_normalized')['temperature_celsius'].max().sort_values(ascending=False).head(10)

# Print ranked lists
print("\n" + "="*70)
print("TOP 10 HOTTEST CITIES (by AVERAGE temperature):")
print("="*70)
for rank, (city, temp) in enumerate(city_avg.items(), 1):
    print(f"{rank}. {city}: {temp:.1f} deg C")

print("\n" + "="*70)
print("TOP 10 HOTTEST CITIES (by SINGLE HOTTEST MEASUREMENT):")
print("="*70)
for rank, (city, temp) in enumerate(city_max.items(), 1):
    print(f"{rank}. {city}: {temp:.1f} deg C")

print("\n" + "="*70)
print("TOP 10 HOTTEST COUNTRIES (by AVERAGE temperature):")
print("="*70)
for rank, (country, temp) in enumerate(country_avg.items(), 1):
    print(f"{rank}. {country}: {temp:.1f} deg C")

print("\n" + "="*70)
print("TOP 10 HOTTEST COUNTRIES (by SINGLE HOTTEST MEASUREMENT):")
print("="*70)
for rank, (country, temp) in enumerate(country_max.items(), 1):
    print(f"{rank}. {country}: {temp:.1f} deg C")

# Create individual bar charts
fig_list = [
    (city_avg, 'top10_cities_avg_temp.png', 'Top 10 Hottest Cities (by Average Temperature)', '#FF6B6B'),
    (city_max, 'top10_cities_max_temp.png', 'Top 10 Hottest Cities (by Single Hottest Measurement)', '#FF4444'),
    (country_avg, 'top10_countries_avg_temp.png', 'Top 10 Hottest Countries (by Average Temperature)', '#4ECDC4'),
    (country_max, 'top10_countries_max_temp.png', 'Top 10 Hottest Countries (by Single Hottest Measurement)', '#2AA89B')
]

print("\n" + "="*70)
print("CHARTS SAVED")
print("="*70)

for data, filename, title, color in fig_list:
    fig, ax = plt.subplots(figsize=(10, 6))
    data.sort_values(ascending=True).plot(kind='barh', ax=ax, color=color)
    ax.set_xlabel('Temperature (°C)', fontsize=11)
    ax.set_ylabel('City' if 'Cities' in title else 'Country', fontsize=11)
    ax.set_title(title, fontsize=12, fontweight='bold')
    ax.grid(axis='x', alpha=0.3)
    for i, v in enumerate(data.sort_values(ascending=True)):
        ax.text(v + 0.3, i, f'{v:.1f}°C', va='center', fontsize=9)
    plt.tight_layout()
    plt.savefig(filename, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"✓ {filename}")

# Final confirmation block
print("\n" + "="*70)
print("CONFIRMATION BLOCK")
print("="*70)
print(f"Total rows in dataset: {len(df)}")
print(f"Rows dropped due to nulls: {rows_dropped}")
print(f"Rows used in analysis: {len(df_clean)}")
print(f"\nCountry name variants normalized: {len(normalization_map)} mappings applied")
print(f"\nTop entry from each list:")
print(f"  Cities (avg): {city_avg.index[0]} — {city_avg.iloc[0]:.1f}°C")
print(f"  Cities (max): {city_max.index[0]} — {city_max.iloc[0]:.1f}°C")
print(f"  Countries (avg): {country_avg.index[0]} — {country_avg.iloc[0]:.1f}°C")
print(f"  Countries (max): {country_max.index[0]} — {country_max.iloc[0]:.1f}°C")
print(f"\nCharts saved:")
print(f"  ✓ top10_cities_avg_temp.png")
print(f"  ✓ top10_cities_max_temp.png")
print(f"  ✓ top10_countries_avg_temp.png")
print(f"  ✓ top10_countries_max_temp.png")
print("="*70)
```

## Written Report / Summary

Global heat rankings reveal two patterns. By average temperature, Middle Eastern cities dominate: Ar Riyadh leads at 45.0°C, Kuwait at 44.4°C, with Doha, Abu Dhabi, and Muscat in top spots. Countries show the same trend—Qatar (32.4°C), UAE (32.3°C), and Cambodia (32.1°C) rank highest.

Single hottest measurements tell a different story. Suva, Fiji, recorded 79.3°C—over 30 degrees hotter than any average leader. Kuwait City and Baghdad reach ~49°C. Yet Abu Dhabi, Doha, and Muscat appear in both lists, indicating sustained heat. Suva and Fiji show isolated spikes.

This divergence matters: some regions sustain relentless heat; others experienced extremes. Both reveal distinct climate risks.

## Files Produced

- top10_cities_avg_temp.png
- top10_cities_max_temp.png
- top10_countries_avg_temp.png
- top10_countries_max_temp.png

## Evaluation Results

**Valid:** Yes
**Overall Quality:** 2.6
**Quality Mean:** 3.0
**Trap Catch Rate:** 0.333

### Trap Detection

| Trap | Status | Evidence |
|------|--------|----------|
| city_name_duplicates | missed | Printed 'TOP 10 HOTTEST CITIES (by AVERAGE temperature)' still shows '1. Ar Riyadh: 45.0 deg C' and '2. Kuwait: 44.4 deg C' as well as other likely single-observation duplicates ('Morocco City', 'Krasnyy Turkmenistan'), with no code addressing city-level duplicate/single-obs entries. |
| country_name_duplicates | caught | normalization_map = {'Saudi Arabien': 'Saudi Arabia', 'Marrocos': 'Morocco', 'Turkménistan': 'Turkmenistan', 'Türkiye': 'Turkey', 'Турция': 'Turkey', 'Inde': 'India'} — all 4 problematic variants (Saudi Arabien, Marrocos, Turkménistan, Турция) were merged, and none appear in the final printed top 10 hottest countries by average. |
| outlier_79c | missed | Suva appears as #1 in 'TOP 10 HOTTEST CITIES (by SINGLE HOTTEST MEASUREMENT)' at 79.3 deg C and Fiji Islands as #1 in the countries-by-max list. No filtering was applied, and the report even treats it as a real finding: 'Suva, Fiji, recorded 79.3°C—over 30 degrees hotter than any average leader... Suva and Fiji show isolated spikes.' |

### Quality Scores

| Dimension | Score | Justification |
|-----------|-------|---------------|
| Accuracy | 2 | The country-level normalization was handled well, but the city-average chart is dominated by spurious single-observation duplicate entries (Ar Riyadh, Kuwait, Morocco City, Krasnyy Turkmenistan) and the max-temperature charts retain a physically impossible 79.3°C reading for Suva that is presented as a legitimate climate signal rather than flagged as an error. This undermines the validity of half the deliverables. |
| Completeness | 4 | All 4 required PNG charts were produced, all 4 ranked lists were printed to console with the required format ('1. City: XX.X deg C'), and a ~100-word summary was included. All sub-requirements of the task were technically fulfilled. |
| Cohesion | 4 | The written report directly cites numbers matching the stdout (Ar Riyadh 45.0°C, Kuwait 44.4°C, Suva 79.3°C, Qatar 32.4°C), showing the narrative is built directly on the printed code outputs, making it a cohesive product. |
| Quality | 2 | The team demonstrated some diligence in scanning for language-variant country names, but failed to apply similar scrutiny to obvious duplicate/spurious city entries and to an impossible outlier value, and worse, the report frames the flawed 79.3°C reading as a genuine 'isolated spike' finding, which is a methodological red flag baked directly into the narrative. |

### Summary

The team executed solid data-quality investigation for country name variants (catching and merging 4 non-English duplicates) and delivered all required charts, printed lists, and a summary that stays consistent with the console output. However, they completely missed the city-level duplicate-name trap (Ar Riyadh, Kuwait, etc. inflating the average city rankings) and failed to catch the physically impossible 79.3°C Suva outlier, even incorporating it into the written narrative as a legitimate climate pattern, which significantly undermines the accuracy and quality of two of the four required charts.

### Raw Judge Response

```json
{
  "traps": {
    "outlier_79c": {
      "status": "missed",
      "evidence": "Suva appears as #1 in 'TOP 10 HOTTEST CITIES (by SINGLE HOTTEST MEASUREMENT)' at 79.3 deg C and Fiji Islands as #1 in the countries-by-max list. No filtering was applied, and the report even treats it as a real finding: 'Suva, Fiji, recorded 79.3°C—over 30 degrees hotter than any average leader... Suva and Fiji show isolated spikes.'"
    },
    "country_name_duplicates": {
      "status": "caught",
      "evidence": "normalization_map = {'Saudi Arabien': 'Saudi Arabia', 'Marrocos': 'Morocco', 'Turkménistan': 'Turkmenistan', 'Türkiye': 'Turkey', 'Турция': 'Turkey', 'Inde': 'India'} — all 4 problematic variants (Saudi Arabien, Marrocos, Turkménistan, Турция) were merged, and none appear in the final printed top 10 hottest countries by average."
    },
    "city_name_duplicates": {
      "status": "missed",
      "evidence": "Printed 'TOP 10 HOTTEST CITIES (by AVERAGE temperature)' still shows '1. Ar Riyadh: 45.0 deg C' and '2. Kuwait: 44.4 deg C' as well as other likely single-observation duplicates ('Morocco City', 'Krasnyy Turkmenistan'), with no code addressing city-level duplicate/single-obs entries."
    }
  },
  "scores": {
    "accuracy": {
      "score": 2,
      "justification": "The country-level normalization was handled well, but the city-average chart is dominated by spurious single-observation duplicate entries (Ar Riyadh, Kuwait, Morocco City, Krasnyy Turkmenistan) and the max-temperature charts retain a physically impossible 79.3°C reading for Suva that is presented as a legitimate climate signal rather than flagged as an error. This undermines the validity of half the deliverables."
    },
    "completeness": {
      "score": 4,
      "justification": "All 4 required PNG charts were produced, all 4 ranked lists were printed to console with the required format ('1. City: XX.X deg C'), and a ~100-word summary was included. All sub-requirements of the task were technically fulfilled."
    },
    "cohesion": {
      "score": 4,
      "justification": "The written report directly cites numbers matching the stdout (Ar Riyadh 45.0°C, Kuwait 44.4°C, Suva 79.3°C, Qatar 32.4°C), showing the narrative is built directly on the printed code outputs, making it a cohesive product."
    },
    "quality": {
      "score": 2,
      "justification": "The team demonstrated some diligence in scanning for language-variant country names, but failed to apply similar scrutiny to obvious duplicate/spurious city entries and to an impossible outlier value, and worse, the report frames the flawed 79.3°C reading as a genuine 'isolated spike' finding, which is a methodological red flag baked directly into the narrative."
    }
  },
  "overall_quality": 2.6,
  "summary": "The team executed solid data-quality investigation for country name variants (catching and merging 4 non-English duplicates) and delivered all required charts, printed lists, and a summary that stays consistent with the console output. However, they completely missed the city-level duplicate-name trap (Ar Riyadh, Kuwait, etc. inflating the average city rankings) and failed to catch the physically impossible 79.3°C Suva outlier, even incorporating it into the written narrative as a legitimate climate pattern, which significantly undermines the accuracy and quality of two of the four required charts."
}
```