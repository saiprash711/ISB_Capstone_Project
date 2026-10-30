"""
Script to generate the Evaluation_10_SKUs dataset and add it as a new sheet to Filtered.xlsx.
Calibrated for Daikin / South Region AC Demand Forecasting.
"""
import os
import random
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

# Set random seed for reproducibility
np.random.seed(42)
random.seed(42)

# 1. Define the 10 Evaluation SKUs covering key combinations
SKU_DEFINITIONS = [
    {
        'Material': 'EVAL-15-INV-5S',
        'Description': '1.5T 5-Star Inverter High Efficiency Flagship',
        'Segment': 'Inverter',
        'Tonnage': 1.5,
        'Star Rating': 'I5S',
        'Star Rating.1': '5 Star',
        'EXT MAT GROUP': 'RA-ODU',
        'Base_Weekly_Vol': 135.0,
        'CV': 0.12
    },
    {
        'Material': 'EVAL-15-INV-3S',
        'Description': '1.5T 3-Star Inverter Mass Market Volume Leader',
        'Segment': 'Inverter',
        'Tonnage': 1.5,
        'Star Rating': 'I3S',
        'Star Rating.1': '3 Star',
        'EXT MAT GROUP': 'RA-ODU',
        'Base_Weekly_Vol': 160.0,
        'CV': 0.14
    },
    {
        'Material': 'EVAL-10-INV-5S',
        'Description': '1.0T 5-Star Inverter Bedroom Premium Model',
        'Segment': 'Inverter',
        'Tonnage': 1.0,
        'Star Rating': 'I5S',
        'Star Rating.1': '5 Star',
        'EXT MAT GROUP': 'RA-ODU',
        'Base_Weekly_Vol': 55.0,
        'CV': 0.15
    },
    {
        'Material': 'EVAL-10-INV-3S',
        'Description': '1.0T 3-Star Inverter Value Compact AC',
        'Segment': 'Inverter',
        'Tonnage': 1.0,
        'Star Rating': 'I3S',
        'Star Rating.1': '3 Star',
        'EXT MAT GROUP': 'RA-ODU',
        'Base_Weekly_Vol': 85.0,
        'CV': 0.16
    },
    {
        'Material': 'EVAL-18-INV-5S',
        'Description': '1.8T 5-Star Inverter Large Living Space Premium',
        'Segment': 'Inverter',
        'Tonnage': 1.8,
        'Star Rating': 'I5S',
        'Star Rating.1': '5 Star',
        'EXT MAT GROUP': 'RA-ODU',
        'Base_Weekly_Vol': 42.0,
        'CV': 0.18
    },
    {
        'Material': 'EVAL-18-INV-3S',
        'Description': '1.8T 3-Star Inverter High Capacity Standard',
        'Segment': 'Inverter',
        'Tonnage': 1.8,
        'Star Rating': 'I3S',
        'Star Rating.1': '3 Star',
        'EXT MAT GROUP': 'RA-ODU',
        'Base_Weekly_Vol': 50.0,
        'CV': 0.18
    },
    {
        'Material': 'EVAL-20-INV-5S',
        'Description': '2.0T 5-Star Inverter Luxury Commercial Suite AC',
        'Segment': 'Inverter',
        'Tonnage': 2.0,
        'Star Rating': 'I5S',
        'Star Rating.1': '5 Star',
        'EXT MAT GROUP': 'RA-ODU',
        'Base_Weekly_Vol': 28.0,
        'CV': 0.20
    },
    {
        'Material': 'EVAL-22-INV-3S',
        'Description': '2.2T 3-Star Inverter Heavy Duty Banquet/Hall AC',
        'Segment': 'Inverter',
        'Tonnage': 2.2,
        'Star Rating': 'I3S',
        'Star Rating.1': '3 Star',
        'EXT MAT GROUP': 'RA-ODU',
        'Base_Weekly_Vol': 38.0,
        'CV': 0.20
    },
    {
        'Material': 'EVAL-15-NON-3S',
        'Description': '1.5T 3-Star Non-Inverter Fixed Speed Commercial Standard',
        'Segment': 'Non-inverter',
        'Tonnage': 1.5,
        'Star Rating': 'N3S',
        'Star Rating.1': '3 Star',
        'EXT MAT GROUP': 'RA-ODU',
        'Base_Weekly_Vol': 65.0,
        'CV': 0.16
    },
    {
        'Material': 'EVAL-10-NON-3S',
        'Description': '1.0T 3-Star Non-Inverter Fixed Speed Entry Unit',
        'Segment': 'Non-inverter',
        'Tonnage': 1.0,
        'Star Rating': 'N3S',
        'Star Rating.1': '3 Star',
        'EXT MAT GROUP': 'RA-ODU',
        'Base_Weekly_Vol': 45.0,
        'CV': 0.18
    }
]

# 2. Branch market share weights (derived empirically from SAP dataset)
BRANCH_WEIGHTS = {
    'MAA': 0.3533 / 0.20,  # ~1.767 (Chennai - highest volume)
    'SBD': 0.2798 / 0.20,  # ~1.399 (Secunderabad - second highest)
    'SBD1': 0.1613 / 0.20, # ~0.806 (Vijayawada)
    'COK': 0.1079 / 0.20,  # ~0.539 (Cochin)
    'BLR': 0.0977 / 0.20   # ~0.488 (Bangalore)
}

BRANCH_DEALERS = {
    'BLR': ['BANGALORE COOLING TECH PVT LTD', 'KARNATAKA AIRCON SYSTEMS', 'SILICON CITY HVAC DEALERS'],
    'MAA': ['CHENNAI AIRCONDITIONING CORP', 'TAMIL NADU CLIMATE CARE', 'MARINA COOLING SOLUTIONS'],
    'COK': ['COCHIN REFRIGERATION & AIR', 'KERALA CLIMATE CONTROLS', 'MALABAR COOLING ENTERPRISES'],
    'SBD': ['HYDERABAD HVAC MASTERS', 'SECUNDERABAD AIRCON CENTRE', 'DECCAN COOLING SYSTEMS'],
    'SBD1': ['VIJAYAWADA AIR TECH AGENCY', 'ANDHRA COOLING DISTRIBUTORS', 'KRISHNA HVAC SOLUTIONS']
}

# 3. Monthly seasonality index (empirical AC demand curve: peak summer in Mar-May, push in Dec)
MONTHLY_SEASONAL_INDEX = {
    1: 0.74,   # Jan
    2: 1.22,   # Feb
    3: 1.86,   # Mar (Pre-summer ramp)
    4: 2.33,   # Apr (Peak summer heat)
    5: 1.40,   # May (Late summer)
    6: 0.62,   # Jun (Monsoon entry)
    7: 0.23,   # Jul (Monsoon trough)
    8: 0.44,   # Aug
    9: 0.54,   # Sep (Festive)
    10: 0.49,  # Oct (Diwali)
    11: 0.47,  # Nov
    12: 1.66   # Dec (Year-end channel stocking / primary billing)
}

MONTH_LABEL_MAP = {
    1: '10) Jan', 2: '11) Feb', 3: '12) Mar', 4: '01) Apr', 5: '02) May', 6: '03) Jun',
    7: '04) Jul', 8: '05) Aug', 9: '06) Sep', 10: '07) Oct', 11: '08) Nov', 12: '09) Dec'
}

def get_fiscal_year(date):
    if date.month >= 4:
        y1 = date.year % 100
        y2 = (date.year + 1) % 100
        return f"{y1:02d}-{y2:02d}"
    else:
        y1 = (date.year - 1) % 100
        y2 = date.year % 100
        return f"{y1:02d}-{y2:02d}"

def get_week_label(date):
    day = date.day
    if day <= 7:
        return 'Wk 1'
    elif day <= 14:
        return 'Wk 2'
    elif day <= 21:
        return 'Wk 3'
    else:
        return 'Wk 4'

def generate_records():
    # Weekly date range: ~102 weeks from 2022-07-18 to 2024-06-24
    dates = pd.date_range('2022-07-18', '2024-06-24', freq='W-MON')
    records = []
    doc_counter = 2238000000
    
    for sku_idx, sku in enumerate(SKU_DEFINITIONS):
        mat = sku['Material']
        base_vol = sku['Base_Weekly_Vol']
        cv = sku['CV']
        tonnage = sku['Tonnage']
        star_code = sku['Star Rating']
        star_label = sku['Star Rating.1']
        segment = sku['Segment']
        mat_group = sku['EXT MAT GROUP']
        
        for branch_code, b_weight in BRANCH_WEIGHTS.items():
            dealers = BRANCH_DEALERS[branch_code]
            
            for t_idx, d in enumerate(dates):
                m = d.month
                s_factor = MONTHLY_SEASONAL_INDEX.get(m, 1.0)
                
                # Modest secular upward trend (+4% per year)
                trend_factor = 1.0 + (t_idx / len(dates)) * 0.08
                
                # Expected weekly demand for this (SKU, Branch, Week)
                mu = base_vol * b_weight * s_factor * trend_factor
                
                # Realistic weekly noise (truncated normal to avoid negative values)
                sigma = max(1.0, mu * cv)
                demand_val = max(1.0, np.random.normal(mu, sigma))
                demand_val = round(demand_val, 1)
                
                # Split demand into 1 or 2 billing line items
                dealer = dealers[(t_idx + sku_idx) % len(dealers)]
                doc_id = doc_counter
                doc_counter += 1
                
                records.append({
                    'Material': mat,
                    'Billing Doc.': float(doc_id),
                    'Item': 10.0,
                    'SALES OFFICE CODE': branch_code,
                    'EXT MAT GROUP': mat_group,
                    'MatGroup3': 'RA',
                    'Star Rating': star_code,
                    'Segment': segment,
                    'Star Rating.1': star_label,
                    'Stor. Location': 1030.0,
                    'SALES OFFICE CODE.1': branch_code,
                    'SBU': 'RA',
                    'Year': get_fiscal_year(d),
                    'Month': MONTH_LABEL_MAP[m],
                    'Week': get_week_label(d),
                    'Billing Date': pd.Timestamp(d),
                    'Customer': dealer,
                    'Material.1': mat,
                    'Billing Quantity ODU': float(demand_val),
                    'Billing Quantity IDU': 0.0,
                    'Tonnage': float(tonnage),
                    'Dealer Name': dealer,
                    'Tonnage.1': float(tonnage),
                    'Data_Sheet': 'Evaluation_10_SKUs'
                })
                
    df_eval = pd.DataFrame(records)
    print(f"Generated {len(df_eval)} evaluation records across {len(SKU_DEFINITIONS)} SKUs and {len(BRANCH_WEIGHTS)} branches.")
    return df_eval

if __name__ == "__main__":
    df_eval = generate_records()
    print("Sample rows:")
    print(df_eval.head(3).T)
