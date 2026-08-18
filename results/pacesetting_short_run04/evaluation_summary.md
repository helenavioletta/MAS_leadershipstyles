# Control Agent Evaluation — pacesetting_short_run04

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
Initial shape: (150465, 41)
After dropping nulls: (150465, 3)

⚠️ FLAG: 1 rows with temp > 60°C
       location_name       country  temperature_celsius
137276          Suva  Fiji Islands                 79.3

Unique countries BEFORE normalization: 211

=== COUNTRY MAPPING TABLE ===
Source → Canonical Name:
  'Bélgica' → 'Belgium'
  'Estonie' → 'Estonia'
  'Inde' → 'India'
  'Jemen' → 'Yemen'
  'Komoren' → 'Comoros'
  'Kyrghyzstan' → 'Kyrgyzstan'
  'Lao People's Democratic Republic' → 'Laos'
  'Letonia' → 'Latvia'
  'Malásia' → 'Malaysia'
  'Marrocos' → 'Morocco'
  'Mexique' → 'Mexico'
  'Polônia' → 'Poland'
  'Saint-Vincent-et-les-Grenadines' → 'Saint Vincent and the Grenadines'
  'Saudi Arabien' → 'Saudi Arabia'
  'Südkorea' → 'South Korea'
  'Turkménistan' → 'Turkmenistan'
  'Türkiye' → 'Turkey'
  'USA United States of America' → 'United States of America'
  'Гватемала' → 'Guatemala'
  'Польша' → 'Poland'
  'Турция' → 'Turkey'
  'كولومبيا' → 'Colombia'
  '火鸡' → 'Turkey'

Unique countries AFTER normalization: 191
Countries consolidated: 20

Unique cities: 268

TOP 10 HOTTEST CITIES — AVERAGE
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

TOP 10 HOTTEST CITIES — SINGLE HIGHEST
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

TOP 10 HOTTEST COUNTRIES — AVERAGE
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

[EXPLICIT CHECK] Turkmenistan after consolidation:
  Average: 22.8 deg C
  Single Max: 42.5 deg C

TOP 10 HOTTEST COUNTRIES — SINGLE HIGHEST
1. Fiji Islands: 79.3 deg C
2. Kuwait: 49.2 deg C
3. Iraq: 49.1 deg C
4. Djibouti: 47.1 deg C
5. United Arab Emirates: 46.4 deg C
6. Oman: 46.3 deg C
7. Saudi Arabia: 46.3 deg C
8. Qatar: 46.3 deg C
9. Bahrain: 45.3 deg C
10. Pakistan: 45.0 deg C

Saved: top10_cities_avg.png
Saved: top10_cities_max.png
Saved: top10_countries_avg.png
Saved: top10_countries_max.png

All deliverables complete.
```

## Final Code (last successful execution)

```python
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# Load dataset
df = pd.read_csv('/Users/hellligkeit/Documents/FS/Masterthesis/MAS/data/global_weather.csv')

# Validate required columns
required_cols = ['location_name', 'country', 'temperature_celsius']
for col in required_cols:
    if col not in df.columns:
        raise ValueError(f"Column '{col}' not found in dataset")

# Drop rows with nulls in required columns
print("Initial shape:", df.shape)
df_clean = df[required_cols].dropna()
print("After dropping nulls:", df_clean.shape)
print()

# Normalize location_name and country (strip whitespace)
df_clean['location_name'] = df_clean['location_name'].str.strip()
df_clean['country'] = df_clean['country'].str.strip()

# Check for extreme temperatures (flag, don't drop)
extreme_hot = df_clean[df_clean['temperature_celsius'] > 60]
extreme_cold = df_clean[df_clean['temperature_celsius'] < -60]
if len(extreme_hot) > 0:
    print(f"⚠️ FLAG: {len(extreme_hot)} rows with temp > 60°C")
    print(extreme_hot[['location_name', 'country', 'temperature_celsius']].to_string())
    print()

# Print all unique country values BEFORE normalization
print(f"Unique countries BEFORE normalization: {df_clean['country'].nunique()}")
unique_countries_before = sorted(df_clean['country'].unique())

# COMPREHENSIVE COUNTRY NORMALIZATION MAPPING
# Map all language variants and transliterations to canonical English names
country_mapping = {
    # Spanish/Portuguese variants
    'Bélgica': 'Belgium',
    'Marrocos': 'Morocco',
    'Polônia': 'Poland',
    'Malásia': 'Malaysia',
    'Mexique': 'Mexico',
    'Estonie': 'Estonia',
    'Inde': 'India',
    'Jemen': 'Yemen',
    'Komoren': 'Comoros',
    
    # German variants
    'Südkorea': 'South Korea',
    'Saudi Arabien': 'Saudi Arabia',
    'Turkménistan': 'Turkmenistan',
    'Türkiye': 'Turkey',
    
    # French variants
    'Saint-Vincent-et-les-Grenadines': 'Saint Vincent and the Grenadines',
    'Lao People\'s Democratic Republic': 'Laos',
    
    # Cyrillic variants
    'Турция': 'Turkey',
    'Гватемала': 'Guatemala',
    'Польша': 'Poland',
    
    # Arabic variant
    'كولومبيا': 'Colombia',
    
    # Chinese variant (火鸡 = Turkey in Chinese)
    '火鸡': 'Turkey',
    
    # Duplicate/variant names
    'USA United States of America': 'United States of America',
    'Kyrghyzstan': 'Kyrgyzstan',
    'Letonia': 'Latvia',
}

print("\n=== COUNTRY MAPPING TABLE ===")
print("Source → Canonical Name:")
for source, target in sorted(country_mapping.items()):
    print(f"  '{source}' → '{target}'")
print()

# Apply mapping
df_clean['country'] = df_clean['country'].map(lambda x: country_mapping.get(x, x))

print(f"Unique countries AFTER normalization: {df_clean['country'].nunique()}")
delta = len(unique_countries_before) - df_clean['country'].nunique()
print(f"Countries consolidated: {delta}")
print()

print(f"Unique cities: {df_clean['location_name'].nunique()}")
print()

# --- CITIES: AVERAGE TEMPERATURE ---
cities_avg = df_clean.groupby('location_name')['temperature_celsius'].mean().sort_values(ascending=False)
if len(cities_avg) < 10:
    print(f"⚠️ WARNING: Only {len(cities_avg)} unique cities (< 10)")
else:
    cities_avg = cities_avg.head(10)

print("TOP 10 HOTTEST CITIES — AVERAGE")
for i, (city, temp) in enumerate(cities_avg.items(), 1):
    print(f"{i}. {city}: {temp:.1f} deg C")
print()

# --- CITIES: SINGLE HIGHEST ---
cities_max = df_clean.groupby('location_name')['temperature_celsius'].max().sort_values(ascending=False)
if len(cities_max) < 10:
    print(f"⚠️ WARNING: Only {len(cities_max)} unique cities (< 10)")
else:
    cities_max = cities_max.head(10)

print("TOP 10 HOTTEST CITIES — SINGLE HIGHEST")
for i, (city, temp) in enumerate(cities_max.items(), 1):
    print(f"{i}. {city}: {temp:.1f} deg C")
print()

# --- COUNTRIES: AVERAGE TEMPERATURE ---
countries_avg = df_clean.groupby('country')['temperature_celsius'].mean().sort_values(ascending=False)
if len(countries_avg) < 10:
    print(f"⚠️ WARNING: Only {len(countries_avg)} unique countries (< 10)")
else:
    countries_avg = countries_avg.head(10)

print("TOP 10 HOTTEST COUNTRIES — AVERAGE")
for i, (country, temp) in enumerate(countries_avg.items(), 1):
    print(f"{i}. {country}: {temp:.1f} deg C")
print()

# Check Turkmenistan explicitly
turkmenistan_avg = df_clean[df_clean['country'] == 'Turkmenistan']['temperature_celsius'].mean()
turkmenistan_max = df_clean[df_clean['country'] == 'Turkmenistan']['temperature_celsius'].max()
print(f"[EXPLICIT CHECK] Turkmenistan after consolidation:")
print(f"  Average: {turkmenistan_avg:.1f} deg C")
print(f"  Single Max: {turkmenistan_max:.1f} deg C")
print()

# --- COUNTRIES: SINGLE HIGHEST ---
countries_max = df_clean.groupby('country')['temperature_celsius'].max().sort_values(ascending=False)
if len(countries_max) < 10:
    print(f"⚠️ WARNING: Only {len(countries_max)} unique countries (< 10)")
else:
    countries_max = countries_max.head(10)

print("TOP 10 HOTTEST COUNTRIES — SINGLE HIGHEST")
for i, (country, temp) in enumerate(countries_max.items(), 1):
    print(f"{i}. {country}: {temp:.1f} deg C")
print()

# --- GENERATE CHARTS ---
def make_horizontal_bar(data, title, filename):
    """Create horizontal bar chart with value labels, hottest at top."""
    fig, ax = plt.subplots(figsize=(10, 6))
    names = list(data.index)
    temps = list(data.values)
    
    # Reverse to show hottest at top
    names = names[::-1]
    temps = temps[::-1]
    
    bars = ax.barh(names, temps, color='#FF6B6B')
    ax.set_xlabel('Temperature (°C)', fontsize=12, fontweight='bold')
    ax.set_title(title, fontsize=13, fontweight='bold')
    
    # Add value labels on bars
    for i, (name, temp) in enumerate(zip(names, temps)):
        ax.text(temp + 0.5, i, f'{temp:.1f}°C', va='center', fontsize=10)
    
    ax.set_xlim(0, max(temps) * 1.1)
    plt.tight_layout()
    plt.savefig(filename, dpi=100, bbox_inches='tight')
    plt.close()
    return filename

# Re-generate cities data for charts (fresh groupby)
cities_avg_chart = df_clean.groupby('location_name')['temperature_celsius'].mean().sort_values(ascending=False).head(10)
cities_max_chart = df_clean.groupby('location_name')['temperature_celsius'].max().sort_values(ascending=False).head(10)
countries_avg_chart = df_clean.groupby('country')['temperature_celsius'].mean().sort_values(ascending=False).head(10)
countries_max_chart = df_clean.groupby('country')['temperature_celsius'].max().sort_values(ascending=False).head(10)

# Chart 1: Cities by Average
file1 = make_horizontal_bar(cities_avg_chart, 'Top 10 Hottest Cities — Average Temperature', 'top10_cities_avg.png')
print(f"Saved: {file1}")

# Chart 2: Cities by Max
file2 = make_horizontal_bar(cities_max_chart, 'Top 10 Hottest Cities — Single Highest Temperature', 'top10_cities_max.png')
print(f"Saved: {file2}")

# Chart 3: Countries by Average
file3 = make_horizontal_bar(countries_avg_chart, 'Top 10 Hottest Countries — Average Temperature', 'top10_countries_avg.png')
print(f"Saved: {file3}")

# Chart 4: Countries by Max
file4 = make_horizontal_bar(countries_max_chart, 'Top 10 Hottest Countries — Single Highest Temperature', 'top10_countries_max.png')
print(f"Saved: {file4}")

print()
print("All deliverables complete.")
```

## Written Report / Summary

Cities and countries rank hottest by two measures: typical average temperature and single highest recorded. By average, Middle Eastern nations dominate—Qatar (32.4°C), UAE (32.3°C), Oman (31.8°C)—alongside Asian nations including Cambodia, Bangladesh, and Thailand (31–32°C). Top cities follow the same pattern: Ar Riyadh (45.0°C) and Kuwait (44.4°C) lead globally.

Single highest temperatures tell a different story. Extreme spikes occur irregularly and unevenly. Suva, Fiji reached 79.3°C, likely a data error. More credible extremes appear in Kuwait City (49.2°C) and Iraq (49.1°C), regions already hot by average. This contrast reveals that sustained heat and occasional extremes are separate phenomena.

## Files Produced

- top10_cities_avg.png
- top10_cities_max.png
- top10_countries_avg.png
- top10_countries_max.png

## Evaluation Results

**Valid:** Yes
**Overall Quality:** 2.5
**Quality Mean:** 2.75
**Trap Catch Rate:** 0.5

### Trap Detection

| Trap | Status | Evidence |
|------|--------|----------|
| city_name_duplicates | missed | No city-level normalization/mapping was applied; the printed 'TOP 10 HOTTEST CITIES — AVERAGE' list still shows 'Ar Riyadh: 45.0' (#1) and 'Kuwait: 44.4' (#2) as separate entries from 'Riyadh' and 'Kuwait City', and the report even cites them as legitimate top cities. |
| country_name_duplicates | caught | Mapping table explicitly converts 'Saudi Arabien'→'Saudi Arabia', 'Marrocos'→'Morocco', 'Turkménistan'→'Turkmenistan', 'Турция'→'Turkey'; none of these raw variants appear in the final printed top 10 countries by average, and the explicit Turkmenistan check confirms the merged average (22.8°C) is no longer inflated. |
| outlier_79c | partial | Code flags it (`⚠️ FLAG: 1 rows with temp > 60°C ... Suva ... 79.3`) but never removes/caps it — it still appears as #1 in both 'TOP 10 HOTTEST CITIES — SINGLE HIGHEST' (Suva: 79.3) and 'TOP 10 HOTTEST COUNTRIES — SINGLE HIGHEST' (Fiji Islands: 79.3), and the corresponding chart is generated from this uncorrected data. |

### Quality Scores

| Dimension | Score | Justification |
|-----------|-------|---------------|
| Accuracy | 2 | Country-level normalization was handled rigorously and verified, but two of three known traps (the 79.3°C outlier and duplicate city names) were left uncorrected in the actual rankings/charts, meaning half the deliverables (cities avg, cities max, countries max) are built on demonstrably corrupted top-10 entries despite being flagged in code. |
| Completeness | 4 | All 4 required charts were saved (top10_cities_avg.png, top10_cities_max.png, top10_countries_avg.png, top10_countries_max.png), all 4 top-10 lists were printed to console with proper formatting ('1. Paris: 25.2 deg C' style), and a ~130-word summary was produced — slightly over the 100-word target but present and complete. |
| Cohesion | 3 | The report numbers (Qatar 32.4°C, Ar Riyadh 45.0°C, Suva 79.3°C, Kuwait City 49.2°C, Iraq 49.1°C) match exactly what was printed and plotted, showing good integration between code and narrative, but the report uncritically presents known-flawed entries (Ar Riyadh, Kuwait duplicates) as legitimate results without caveat, undermining the coherence of the narrative's claims. |
| Quality | 2 | While country normalization was thorough and well-documented (mapping table, explicit verification), the failure to actually remove the impossible 79.3°C Suva reading or to deduplicate city names means two of the four charts are dominated by data artifacts rather than genuine climate signal, which is a significant methodological gap that a non-technical reader would not detect from the report alone. |

### Summary

The team did excellent, well-documented work normalizing multilingual country names, correctly resolving the country-duplicate trap, but failed to actually remove the flagged 79.3°C outlier (only 'flagged' in text and code comments) and never addressed duplicate city names, leaving two of the four required charts distorted by known bad data. The deliverable is complete and internally consistent between code and report, but the underlying rankings for cities (avg/max) and country max are compromised by unresolved traps.

### Raw Judge Response

```json
{
  "traps": {
    "outlier_79c": {
      "status": "partial",
      "evidence": "Code flags it (`⚠️ FLAG: 1 rows with temp > 60°C ... Suva ... 79.3`) but never removes/caps it — it still appears as #1 in both 'TOP 10 HOTTEST CITIES — SINGLE HIGHEST' (Suva: 79.3) and 'TOP 10 HOTTEST COUNTRIES — SINGLE HIGHEST' (Fiji Islands: 79.3), and the corresponding chart is generated from this uncorrected data."
    },
    "country_name_duplicates": {
      "status": "caught",
      "evidence": "Mapping table explicitly converts 'Saudi Arabien'→'Saudi Arabia', 'Marrocos'→'Morocco', 'Turkménistan'→'Turkmenistan', 'Турция'→'Turkey'; none of these raw variants appear in the final printed top 10 countries by average, and the explicit Turkmenistan check confirms the merged average (22.8°C) is no longer inflated."
    },
    "city_name_duplicates": {
      "status": "missed",
      "evidence": "No city-level normalization/mapping was applied; the printed 'TOP 10 HOTTEST CITIES — AVERAGE' list still shows 'Ar Riyadh: 45.0' (#1) and 'Kuwait: 44.4' (#2) as separate entries from 'Riyadh' and 'Kuwait City', and the report even cites them as legitimate top cities."
    }
  },
  "scores": {
    "accuracy": {
      "score": 2,
      "justification": "Country-level normalization was handled rigorously and verified, but two of three known traps (the 79.3°C outlier and duplicate city names) were left uncorrected in the actual rankings/charts, meaning half the deliverables (cities avg, cities max, countries max) are built on demonstrably corrupted top-10 entries despite being flagged in code."
    },
    "completeness": {
      "score": 4,
      "justification": "All 4 required charts were saved (top10_cities_avg.png, top10_cities_max.png, top10_countries_avg.png, top10_countries_max.png), all 4 top-10 lists were printed to console with proper formatting ('1. Paris: 25.2 deg C' style), and a ~130-word summary was produced — slightly over the 100-word target but present and complete."
    },
    "cohesion": {
      "score": 3,
      "justification": "The report numbers (Qatar 32.4°C, Ar Riyadh 45.0°C, Suva 79.3°C, Kuwait City 49.2°C, Iraq 49.1°C) match exactly what was printed and plotted, showing good integration between code and narrative, but the report uncritically presents known-flawed entries (Ar Riyadh, Kuwait duplicates) as legitimate results without caveat, undermining the coherence of the narrative's claims."
    },
    "quality": {
      "score": 2,
      "justification": "While country normalization was thorough and well-documented (mapping table, explicit verification), the failure to actually remove the impossible 79.3°C Suva reading or to deduplicate city names means two of the four charts are dominated by data artifacts rather than genuine climate signal, which is a significant methodological gap that a non-technical reader would not detect from the report alone."
    }
  },
  "overall_quality": 2.5,
  "summary": "The team did excellent, well-documented work normalizing multilingual country names, correctly resolving the country-duplicate trap, but failed to actually remove the flagged 79.3°C outlier (only 'flagged' in text and code comments) and never addressed duplicate city names, leaving two of the four required charts distorted by known bad data. The deliverable is complete and internally consistent between code and report, but the underlying rankings for cities (avg/max) and country max are compromised by unresolved traps."
}
```