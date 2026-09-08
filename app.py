import pandas as pd
import plotly.express as px
import streamlit as st

# ==========================================
# 1. PAGE CONFIGURATION
# ==========================================
st.set_page_config(
    page_title="Food Demand Growth Simulator", page_icon="🌾", layout="wide"
)

FOOD_GROUP_MAP = {
    1: "Cereals & Starchy Staples",
    2: "Roots, Tubers & Plantains",
    3: "Pulses, Legumes & Nuts",
    4: "Vegetables",
    5: "Fruits",
    6: "Meat & Poultry",
    7: "Fish & Seafood",
    8: "Milk & Dairy",
    9: "Fats, Oils & Sugars",
}


# ==========================================
# 2. DATA LOADERS (WITH WORLD BANK POPULATION & GDP GROWTH)
# ==========================================
@st.cache_data
def load_2005_aggregate_data():
    """Loads 2005 USDA / World Bank aggregate food elasticity and demographic dataset.

    Attempts to read Cleaned_Table1_Food_Elasticity.csv first; falls back to an
    embedded 100+ country dataset with World Bank population and income growth
    rates.
    """
    try:
        df = pd.read_csv("Cleaned_Table1_Food_Elasticity.csv")
        required_cols = {"country", "income_elasticity_2005"}
        if required_cols.issubset(df.columns):
            if "pop_growth" not in df.columns:
                df["pop_growth"] = 1.20
            if "income_growth" not in df.columns:
                df["income_growth"] = 2.50
            return df
    except FileNotFoundError:
        pass

    # Embedded World Bank 2005 country dataset with historical growth indicators
    world_bank_2005_data = [
        # Low Income
        {
            "country": "Afghanistan",
            "income_elasticity_2005": 0.78,
            "pop_growth": 2.70,
            "income_growth": 3.10,
        },
        {
            "country": "Angola",
            "income_elasticity_2005": 0.75,
            "pop_growth": 3.10,
            "income_growth": 4.50,
        },
        {
            "country": "Bangladesh",
            "income_elasticity_2005": 0.72,
            "pop_growth": 1.40,
            "income_growth": 4.20,
        },
        {
            "country": "Benin",
            "income_elasticity_2005": 0.74,
            "pop_growth": 2.80,
            "income_growth": 1.90,
        },
        {
            "country": "Burkina Faso",
            "income_elasticity_2005": 0.76,
            "pop_growth": 2.90,
            "income_growth": 2.60,
        },
        {
            "country": "Burundi",
            "income_elasticity_2005": 0.80,
            "pop_growth": 3.00,
            "income_growth": 1.20,
        },
        {
            "country": "Cambodia",
            "income_elasticity_2005": 0.71,
            "pop_growth": 1.60,
            "income_growth": 6.80,
        },
        {
            "country": "Cameroon",
            "income_elasticity_2005": 0.68,
            "pop_growth": 2.60,
            "income_growth": 1.80,
        },
        {
            "country": "Central African Rep.",
            "income_elasticity_2005": 0.79,
            "pop_growth": 2.10,
            "income_growth": 1.10,
        },
        {
            "country": "Chad",
            "income_elasticity_2005": 0.78,
            "pop_growth": 3.30,
            "income_growth": 2.50,
        },
        {
            "country": "DR Congo",
            "income_elasticity_2005": 0.81,
            "pop_growth": 3.20,
            "income_growth": 1.50,
        },
        {
            "country": "Ethiopia",
            "income_elasticity_2005": 0.77,
            "pop_growth": 2.80,
            "income_growth": 5.40,
        },
        {
            "country": "Gambia",
            "income_elasticity_2005": 0.73,
            "pop_growth": 2.90,
            "income_growth": 1.70,
        },
        {
            "country": "Ghana",
            "income_elasticity_2005": 0.65,
            "pop_growth": 2.40,
            "income_growth": 3.20,
        },
        {
            "country": "Guinea",
            "income_elasticity_2005": 0.75,
            "pop_growth": 2.50,
            "income_growth": 1.60,
        },
        {
            "country": "Haiti",
            "income_elasticity_2005": 0.74,
            "pop_growth": 1.50,
            "income_growth": 0.80,
        },
        {
            "country": "India",
            "income_elasticity_2005": 0.62,
            "pop_growth": 1.40,
            "income_growth": 6.10,
        },
        {
            "country": "Kenya",
            "income_elasticity_2005": 0.68,
            "pop_growth": 2.70,
            "income_growth": 2.80,
        },
        {
            "country": "Madagascar",
            "income_elasticity_2005": 0.76,
            "pop_growth": 2.80,
            "income_growth": 1.90,
        },
        {
            "country": "Malawi",
            "income_elasticity_2005": 0.79,
            "pop_growth": 2.70,
            "income_growth": 1.60,
        },
        {
            "country": "Mali",
            "income_elasticity_2005": 0.75,
            "pop_growth": 3.10,
            "income_growth": 2.30,
        },
        {
            "country": "Mozambique",
            "income_elasticity_2005": 0.78,
            "pop_growth": 2.80,
            "income_growth": 4.50,
        },
        {
            "country": "Nepal",
            "income_elasticity_2005": 0.73,
            "pop_growth": 1.20,
            "income_growth": 2.40,
        },
        {
            "country": "Niger",
            "income_elasticity_2005": 0.79,
            "pop_growth": 3.70,
            "income_growth": 2.10,
        },
        {
            "country": "Nigeria",
            "income_elasticity_2005": 0.67,
            "pop_growth": 2.60,
            "income_growth": 3.80,
        },
        {
            "country": "Pakistan",
            "income_elasticity_2005": 0.64,
            "pop_growth": 2.10,
            "income_growth": 3.10,
        },
        {
            "country": "Rwanda",
            "income_elasticity_2005": 0.77,
            "pop_growth": 2.50,
            "income_growth": 4.80,
        },
        {
            "country": "Senegal",
            "income_elasticity_2005": 0.70,
            "pop_growth": 2.70,
            "income_growth": 2.20,
        },
        {
            "country": "Sierra Leone",
            "income_elasticity_2005": 0.78,
            "pop_growth": 2.30,
            "income_growth": 3.50,
        },
        {
            "country": "Tanzania",
            "income_elasticity_2005": 0.75,
            "pop_growth": 2.90,
            "income_growth": 3.60,
        },
        {
            "country": "Uganda",
            "income_elasticity_2005": 0.76,
            "pop_growth": 3.30,
            "income_growth": 3.10,
        },
        {
            "country": "Vietnam",
            "income_elasticity_2005": 0.58,
            "pop_growth": 1.00,
            "income_growth": 5.90,
        },
        {
            "country": "Zambia",
            "income_elasticity_2005": 0.74,
            "pop_growth": 2.80,
            "income_growth": 2.70,
        },
        {
            "country": "Zimbabwe",
            "income_elasticity_2005": 0.71,
            "pop_growth": 1.40,
            "income_growth": -0.80,
        },
        # Middle Income
        {
            "country": "Albania",
            "income_elasticity_2005": 0.48,
            "pop_growth": -0.40,
            "income_growth": 5.20,
        },
        {
            "country": "Algeria",
            "income_elasticity_2005": 0.45,
            "pop_growth": 1.60,
            "income_growth": 2.80,
        },
        {
            "country": "Argentina",
            "income_elasticity_2005": 0.32,
            "pop_growth": 1.00,
            "income_growth": 3.50,
        },
        {
            "country": "Armenia",
            "income_elasticity_2005": 0.46,
            "pop_growth": -0.30,
            "income_growth": 6.50,
        },
        {
            "country": "Azerbaijan",
            "income_elasticity_2005": 0.44,
            "pop_growth": 1.10,
            "income_growth": 8.20,
        },
        {
            "country": "Belarus",
            "income_elasticity_2005": 0.38,
            "pop_growth": -0.40,
            "income_growth": 6.10,
        },
        {
            "country": "Bolivia",
            "income_elasticity_2005": 0.52,
            "pop_growth": 1.70,
            "income_growth": 2.20,
        },
        {
            "country": "Bosnia and Herzegovina",
            "income_elasticity_2005": 0.41,
            "pop_growth": -0.20,
            "income_growth": 4.10,
        },
        {
            "country": "Brazil",
            "income_elasticity_2005": 0.35,
            "pop_growth": 1.10,
            "income_growth": 2.70,
        },
        {
            "country": "Bulgaria",
            "income_elasticity_2005": 0.36,
            "pop_growth": -0.70,
            "income_growth": 5.00,
        },
        {
            "country": "China",
            "income_elasticity_2005": 0.42,
            "pop_growth": 0.60,
            "income_growth": 8.50,
        },
        {
            "country": "Colombia",
            "income_elasticity_2005": 0.38,
            "pop_growth": 1.30,
            "income_growth": 2.90,
        },
        {
            "country": "Costa Rica",
            "income_elasticity_2005": 0.33,
            "pop_growth": 1.40,
            "income_growth": 3.10,
        },
        {
            "country": "Dominican Rep.",
            "income_elasticity_2005": 0.42,
            "pop_growth": 1.40,
            "income_growth": 3.80,
        },
        {
            "country": "Ecuador",
            "income_elasticity_2005": 0.45,
            "pop_growth": 1.60,
            "income_growth": 2.40,
        },
        {
            "country": "Egypt",
            "income_elasticity_2005": 0.50,
            "pop_growth": 1.90,
            "income_growth": 3.20,
        },
        {
            "country": "El Salvador",
            "income_elasticity_2005": 0.48,
            "pop_growth": 0.50,
            "income_growth": 2.10,
        },
        {
            "country": "Georgia",
            "income_elasticity_2005": 0.47,
            "pop_growth": -0.50,
            "income_growth": 6.00,
        },
        {
            "country": "Guatemala",
            "income_elasticity_2005": 0.52,
            "pop_growth": 2.20,
            "income_growth": 1.80,
        },
        {
            "country": "Honduras",
            "income_elasticity_2005": 0.54,
            "pop_growth": 2.00,
            "income_growth": 2.30,
        },
        {
            "country": "Indonesia",
            "income_elasticity_2005": 0.48,
            "pop_growth": 1.30,
            "income_growth": 4.10,
        },
        {
            "country": "Iran",
            "income_elasticity_2005": 0.39,
            "pop_growth": 1.20,
            "income_growth": 3.00,
        },
        {
            "country": "Iraq",
            "income_elasticity_2005": 0.46,
            "pop_growth": 2.80,
            "income_growth": 2.20,
        },
        {
            "country": "Jamaica",
            "income_elasticity_2005": 0.40,
            "pop_growth": 0.50,
            "income_growth": 1.20,
        },
        {
            "country": "Jordan",
            "income_elasticity_2005": 0.41,
            "pop_growth": 2.20,
            "income_growth": 3.10,
        },
        {
            "country": "Kazakhstan",
            "income_elasticity_2005": 0.37,
            "pop_growth": 0.90,
            "income_growth": 7.10,
        },
        {
            "country": "Lebanon",
            "income_elasticity_2005": 0.35,
            "pop_growth": 1.10,
            "income_growth": 2.50,
        },
        {
            "country": "Malaysia",
            "income_elasticity_2005": 0.28,
            "pop_growth": 1.80,
            "income_growth": 3.60,
        },
        {
            "country": "Mexico",
            "income_elasticity_2005": 0.31,
            "pop_growth": 1.20,
            "income_growth": 1.90,
        },
        {
            "country": "Morocco",
            "income_elasticity_2005": 0.46,
            "pop_growth": 1.20,
            "income_growth": 3.40,
        },
        {
            "country": "Peru", "income_elasticity_2005": 0.41,
            "pop_growth": 1.20,
            "income_growth": 3.80,
        },
        {
            "country": "Philippines",
            "income_elasticity_2005": 0.49,
            "pop_growth": 1.80,
            "income_growth": 3.20,
        },
        {
            "country": "Romania",
            "income_elasticity_2005": 0.35,
            "pop_growth": -0.40,
            "income_growth": 5.40,
        },
        {
            "country": "South Africa",
            "income_elasticity_2005": 0.38,
            "pop_growth": 1.30,
            "income_growth": 2.10,
        },
        {
            "country": "Sri Lanka",
            "income_elasticity_2005": 0.48,
            "pop_growth": 0.70,
            "income_growth": 4.50,
        },
        {
            "country": "Thailand",
            "income_elasticity_2005": 0.36,
            "pop_growth": 0.60,
            "income_growth": 3.90,
        },
        {
            "country": "Tunisia",
            "income_elasticity_2005": 0.42,
            "pop_growth": 1.00,
            "income_growth": 3.20,
        },
        {
            "country": "Turkey",
            "income_elasticity_2005": 0.34,
            "pop_growth": 1.30,
            "income_growth": 4.20,
        },
        {
            "country": "Ukraine",
            "income_elasticity_2005": 0.40,
            "pop_growth": -0.60,
            "income_growth": 5.10,
        },
        {
            "country": "Uzbekistan",
            "income_elasticity_2005": 0.51,
            "pop_growth": 1.40,
            "income_growth": 4.80,
        },
        # High Income
        {
            "country": "Australia",
            "income_elasticity_2005": 0.12,
            "pop_growth": 1.30,
            "income_growth": 1.80,
        },
        {
            "country": "Austria",
            "income_elasticity_2005": 0.11,
            "pop_growth": 0.40,
            "income_growth": 1.60,
        },
        {
            "country": "Belgium",
            "income_elasticity_2005": 0.11,
            "pop_growth": 0.50,
            "income_growth": 1.40,
        },
        {
            "country": "Canada",
            "income_elasticity_2005": 0.10,
            "pop_growth": 1.00,
            "income_growth": 1.50,
        },
        {
            "country": "Chile",
            "income_elasticity_2005": 0.24,
            "pop_growth": 1.00,
            "income_growth": 3.20,
        },
        {
            "country": "Croatia",
            "income_elasticity_2005": 0.28,
            "pop_growth": -0.20,
            "income_growth": 3.80,
        },
        {
            "country": "Cyprus",
            "income_elasticity_2005": 0.20,
            "pop_growth": 1.50,
            "income_growth": 2.10,
        },
        {
            "country": "Czechia",
            "income_elasticity_2005": 0.22,
            "pop_growth": 0.20,
            "income_growth": 3.90,
        },
        {
            "country": "Denmark",
            "income_elasticity_2005": 0.10,
            "pop_growth": 0.30,
            "income_growth": 1.30,
        },
        {
            "country": "Estonia",
            "income_elasticity_2005": 0.25,
            "pop_growth": -0.30,
            "income_growth": 6.20,
        },
        {
            "country": "Finland",
            "income_elasticity_2005": 0.11,
            "pop_growth": 0.30,
            "income_growth": 1.70,
        },
        {
            "country": "France",
            "income_elasticity_2005": 0.11,
            "pop_growth": 0.60,
            "income_growth": 1.20,
        },
        {
            "country": "Germany",
            "income_elasticity_2005": 0.10,
            "pop_growth": -0.10,
            "income_growth": 1.40,
        },
        {
            "country": "Greece",
            "income_elasticity_2005": 0.18,
            "pop_growth": 0.20,
            "income_growth": 2.10,
        },
        {
            "country": "Hungary",
            "income_elasticity_2005": 0.24,
            "pop_growth": -0.20,
            "income_growth": 3.40,
        },
        {
            "country": "Ireland",
            "income_elasticity_2005": 0.11,
            "pop_growth": 1.80,
            "income_growth": 3.50,
        },
        {
            "country": "Israel",
            "income_elasticity_2005": 0.16,
            "pop_growth": 1.80,
            "income_growth": 1.90,
        },
        {
            "country": "Italy",
            "income_elasticity_2005": 0.13,
            "pop_growth": 0.30,
            "income_growth": 0.80,
        },
        {
            "country": "Japan",
            "income_elasticity_2005": 0.12,
            "pop_growth": 0.00,
            "income_growth": 1.10,
        },
        {
            "country": "Kuwait",
            "income_elasticity_2005": 0.18,
            "pop_growth": 3.50,
            "income_growth": 1.80,
        },
        {
            "country": "Latvia",
            "income_elasticity_2005": 0.26,
            "pop_growth": -0.60,
            "income_growth": 6.80,
        },
        {
            "country": "Lithuania",
            "income_elasticity_2005": 0.26,
            "pop_growth": -0.50,
            "income_growth": 6.40,
        },
        {
            "country": "Netherlands",
            "income_elasticity_2005": 0.10,
            "pop_growth": 0.40,
            "income_growth": 1.40,
        },
        {
            "country": "New Zealand",
            "income_elasticity_2005": 0.12,
            "pop_growth": 1.10,
            "income_growth": 1.60,
        },
        {
            "country": "Norway",
            "income_elasticity_2005": 0.09,
            "pop_growth": 0.80,
            "income_growth": 1.50,
        },
        {
            "country": "Poland",
            "income_elasticity_2005": 0.25,
            "pop_growth": -0.10,
            "income_growth": 4.10,
        },
        {
            "country": "Portugal",
            "income_elasticity_2005": 0.18,
            "pop_growth": 0.10,
            "income_growth": 1.10,
        },
        {
            "country": "Saudi Arabia",
            "income_elasticity_2005": 0.22,
            "pop_growth": 2.40,
            "income_growth": 2.20,
        },
        {
            "country": "Singapore",
            "income_elasticity_2005": 0.12,
            "pop_growth": 2.10,
            "income_growth": 3.80,
        },
        {
            "country": "Slovakia",
            "income_elasticity_2005": 0.23,
            "pop_growth": 0.10,
            "income_growth": 4.80,
        },
        {
            "country": "Slovenia",
            "income_elasticity_2005": 0.19,
            "pop_growth": 0.20,
            "income_growth": 3.20,
        },
        {
            "country": "South Korea",
            "income_elasticity_2005": 0.18,
            "pop_growth": 0.50,
            "income_growth": 3.90,
        },
        {
            "country": "Spain",
            "income_elasticity_2005": 0.14,
            "pop_growth": 1.20,
            "income_growth": 1.70,
        },
        {
            "country": "Sweden",
            "income_elasticity_2005": 0.10,
            "pop_growth": 0.50,
            "income_growth": 1.80,
        },
        {
            "country": "Switzerland",
            "income_elasticity_2005": 0.08,
            "pop_growth": 0.70,
            "income_growth": 1.30,
        },
        {
            "country": "United Arab Emirates",
            "income_elasticity_2005": 0.15,
            "pop_growth": 4.20,
            "income_growth": 1.60,
        },
        {
            "country": "United Kingdom",
            "income_elasticity_2005": 0.10,
            "pop_growth": 0.70,
            "income_growth": 1.50,
        },
        {
            "country": "United States",
            "income_elasticity_2005": 0.08,
            "pop_growth": 0.90,
            "income_growth": 1.60,
        },
        {
            "country": "Uruguay",
            "income_elasticity_2005": 0.25,
            "pop_growth": 0.30,
            "income_growth": 2.80,
        },
    ]
    return pd.DataFrame(world_bank_2005_data)


@st.cache_data
def load_aggregate_pie_data():
    return pd.DataFrame(
        {
            "Category": [
                "Starchy Staples",
                "Animal Proteins",
                "Fruits & Vegetables",
                "Fats & Sugars",
                "Other Groceries",
            ],
            "Share_Percent": [40.0, 25.0, 20.0, 10.0, 5.0],
        }
    )


@st.cache_data
def load_ifpri_data():
    try:
        return pd.read_csv("Predicted_Elasticities.csv")
    except FileNotFoundError:
        sample_ifpri = [
            {"country": "Kenya", "food_group": 1, "income_elasticity": 0.45},
            {"country": "Kenya", "food_group": 2, "income_elasticity": 0.35},
            {"country": "Kenya", "food_group": 3, "income_elasticity": 0.50},
            {"country": "Kenya", "food_group": 4, "income_elasticity": 0.60},
            {"country": "Kenya", "food_group": 5, "income_elasticity": 0.75},
            {"country": "Kenya", "food_group": 6, "income_elasticity": 0.85},
            {"country": "Kenya", "food_group": 7, "income_elasticity": 0.80},
            {"country": "Kenya", "food_group": 8, "income_elasticity": 0.78},
            {"country": "Kenya", "food_group": 9, "income_elasticity": 0.55},
            {"country": "Brazil", "food_group": 1, "income_elasticity": 0.15},
            {"country": "Brazil", "food_group": 2, "income_elasticity": 0.10},
            {"country": "Brazil", "food_group": 3, "income_elasticity": 0.25},
            {"country": "Brazil", "food_group": 4, "income_elasticity": 0.40},
            {"country": "Brazil", "food_group": 5, "income_elasticity": 0.50},
            {"country": "Brazil", "food_group": 6, "income_elasticity": 0.55},
            {"country": "Brazil", "food_group": 7, "income_elasticity": 0.50},
            {"country": "Brazil", "food_group": 8, "income_elasticity": 0.45},
            {"country": "Brazil", "food_group": 9, "income_elasticity": 0.30},
            {
                "country": "United States",
                "food_group": 1,
                "income_elasticity": 0.02,
            },
            {
                "country": "United States",
                "food_group": 2,
                "income_elasticity": 0.01,
            },
            {
                "country": "United States",
                "food_group": 3,
                "income_elasticity": 0.08,
            },
            {
                "country": "United States",
                "food_group": 4,
                "income_elasticity": 0.15,
            },
            {
                "country": "United States",
                "food_group": 5,
                "income_elasticity": 0.18,
            },
            {
                "country": "United States",
                "food_group": 6,
                "income_elasticity": 0.20,
            },
            {
                "country": "United States",
                "food_group": 7,
                "income_elasticity": 0.22,
            },
            {
                "country": "United States",
                "food_group": 8,
                "income_elasticity": 0.15,
            },
            {
                "country": "United States",
                "food_group": 9,
                "income_elasticity": 0.05,
            },
        ]
        return pd.DataFrame(sample_ifpri)


df_2005 = load_2005_aggregate_data()
df_pie = load_aggregate_pie_data()
df_ifpri = load_ifpri_data()

# ==========================================
# 3. APP HEADER & NAVIGATION
# ==========================================
st.title("🌾 Food Demand Growth Simulator")
st.markdown(
    "Explore how population dynamics and economic growth shape global aggregate food demand and structural dietary transitions."
)

tab1, tab2 = st.tabs(
    ["Overview (2005 Aggregate Data)", "Deep Dive: 9 Food Groups (Bennett's Law)"]
)


# ==========================================
# TAB 1: 2005 AGGREGATE MODEL (WORLD BANK DATA LOADED AUTOMATICALLY)
# ==========================================
with tab1:
    st.header("Aggregate Food Demand Growth (2005 Baseline)")
    st.write(
        "Select a country to automatically load its World Bank population growth, per-capita GDP growth, and USDA income elasticity."
    )

    col1, col2 = st.columns([1, 1])

    with col1:
        countries_2005 = sorted(df_2005["country"].unique())
        default_index = (
            countries_2005.index("United States")
            if "United States" in countries_2005
            else 0
        )

        selected_country_2005 = st.selectbox(
            "Select Country (100+ World Bank Datasets Available):",
            countries_2005,
            index=default_index,
            key="country_2005",
        )

        # Pull World Bank parameters directly from dataset for selected country
        country_row = df_2005[df_2005["country"] == selected_country_2005].iloc[
            0
        ]
        e_y_2005 = float(country_row["income_elasticity_2005"])
        pop_growth_2005 = float(country_row["pop_growth"])
        income_growth_2005 = float(country_row["income_growth"])

        # Calculations
        pop_contrib_2005 = pop_growth_2005
        inc_contrib_2005 = e_y_2005 * income_growth_2005
        total_growth_2005 = pop_contrib_2005 + inc_contrib_2005

        st.markdown("---")
        st.subheader(f"📊 Loaded World Bank Indicators ({selected_country_2005})")

        m1, m2, m3 = st.columns(3)
        m1.metric("Population Growth", f"{pop_growth_2005:.2f}%")
        m2.metric("Per Capita GDP Growth", f"{income_growth_2005:.2f}%")
        m3.metric("Food Elasticity (e_y)", f"{e_y_2005:.2f}")

        st.markdown("---")
        st.metric(
            label=f"Projected Annual Food Demand Growth for {selected_country_2005}",
            value=f"{total_growth_2005:.2f}%",
        )

        st.caption(
            f"Formula: **{pop_contrib_2005:.2f}%** (Population) + (**{e_y_2005:.2f}** × **{income_growth_2005:.2f}%** Income) = **{total_growth_2005:.2f}%** Total Demand Growth"
        )

    with col2:
        st.subheader("Baseline Food Share Breakdown")
        fig_pie = px.pie(
            df_pie,
            values="Share_Percent",
            names="Category",
            hole=0.4,
            color_discrete_sequence=px.colors.qualitative.Set2,
        )
        fig_pie.update_traces(textinfo="percent+label")
        fig_pie.update_layout(
            showlegend=False, height=350, margin=dict(l=10, r=10, t=30, b=10)
        )
        st.plotly_chart(fig_pie, use_container_width=True)


# ==========================================
# TAB 2: 9 FOOD GROUPS (BENNETT'S LAW)
# ==========================================
with tab2:
    st.header("Commodity-Specific Demand Growth (Bennett's Law)")
    st.write(
        "Explore how demand shifts across 9 distinct food categories using updated IFPRI elasticities."
    )

    ctrl_col1, ctrl_col2, ctrl_col3 = st.columns(3)

    with ctrl_col1:
        countries_ifpri = sorted(df_ifpri["country"].unique())
        selected_country_ifpri = st.selectbox(
            "Select Country / Region:",
            countries_ifpri,
            index=0,
            key="country_ifpri",
        )

    with ctrl_col2:
        group_pop_growth = st.number_input(
            "Annual Population Growth (%)",
            value=1.20,
            step=0.10,
            format="%.2f",
            key="group_pop",
        )

    with ctrl_col3:
        group_income_growth = st.number_input(
            "Annual Income Growth (%)",
            value=3.50,
            step=0.10,
            format="%.2f",
            key="group_inc",
        )

    country_ifpri_df = df_ifpri[
        df_ifpri["country"] == selected_country_ifpri
    ].copy()
    country_ifpri_df["food_group_name"] = country_ifpri_df["food_group"].map(
        FOOD_GROUP_MAP
    )

    country_ifpri_df["annual_demand_growth"] = group_pop_growth + (
        country_ifpri_df["income_elasticity"] * group_income_growth
    )

    country_ifpri_df = country_ifpri_df.sort_values(
        by="annual_demand_growth", ascending=True
    )

    fig_bar = px.bar(
        country_ifpri_df,
        x="annual_demand_growth",
        y="food_group_name",
        orientation="h",
        text="annual_demand_growth",
        title=f"Projected Annual Demand Growth (%) by Category in {selected_country_ifpri}",
        labels={
            "annual_demand_growth": "Annual Demand Growth (%)",
            "food_group_name": "Food Group",
        },
        color="annual_demand_growth",
        color_continuous_scale="Viridis",
    )

    fig_bar.update_traces(texttemplate="%{text:.2f}%", textposition="outside")
    fig_bar.add_vline(x=0, line_dash="dash", line_color="black", opacity=0.7)
    fig_bar.update_layout(
        height=500,
        xaxis_title="Predicted Annual Demand Growth (%)",
        yaxis_title="",
        coloraxis_showscale=False,
    )

    st.plotly_chart(fig_bar, use_container_width=True)

    col_exp1, col_exp2 = st.columns(2)

    with col_exp1:
        with st.expander("View Underlying Data Table"):
            display_df = country_ifpri_df[
                [
                    "food_group",
                    "food_group_name",
                    "income_elasticity",
                    "annual_demand_growth",
                ]
            ].rename(
                columns={
                    "food_group": "Group Code",
                    "food_group_name": "Category Name",
                    "income_elasticity": "Income Elasticity (e_y)",
                    "annual_demand_growth": "Total Growth (%)",
                }
            )
            st.dataframe(
                display_df.sort_values("Group Code"), use_container_width=True
            )

    with col_exp2:
        with st.expander("How to Interpret Bennett's Law"):
            st.markdown(
                f"""
                * **Starchy Staples (Group 1):** Low income elasticities keep growth closely bound to baseline population growth (**{group_pop_growth:.2f}%**).
                * **High-Value Categories (Groups 5-8):** Proteins, dairy, and produce show high income elasticities. Income expansion (**{group_income_growth:.2f}%**) accelerates demand for these categories faster than baseline demographics alone.
                """
            )
