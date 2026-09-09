import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import streamlit as st

# ==========================================
# HARDCODED WORLD FOOD GROUP ELASTICITIES (2021)
# ==========================================
WORLD_FOOD_GROUP_ELASTICITIES = {
    1: 0.708945,    # Animal-Sourced Food
    2: 0.5145576,   # Beans, Lentils, Peas & Soy
    3: 0.5220307,   # Condiments & Sweeteners
    4: 0.5771826,   # Fruits, Vegetables & Nuts
    5: 0.32338026,  # Grains & Starchy Staples
    6: 0.407696,    # Processed Meals & Snacks
    7: 0.5460111,   # Oils & Fats
    8: 1.0183451,   # Food Away From Home
    9: 0.5897565,   # All Beverages
}

# ==========================================
# 1. PAGE CONFIGURATION & GLOBAL COLOR MAPS
# ==========================================
st.set_page_config(
    page_title="Food Demand Growth Simulator", page_icon="🌾", layout="wide"
)

# Tab 3: Food Subgroups (IFPRI 9 Food Groups / Bennett's Law)
FOOD_GROUP_MAP = {
    1: "Animal-Sourced Food",
    2: "Beans, Lentils, Peas & Soy",
    3: "Condiments & Sweeteners",
    4: "Fruits, Vegetables & Nuts",
    5: "Grains & Starchy Staples",
    6: "Processed Meals & Snacks",
    7: "Oils & Fats",
    8: "Food Away From Home",
    9: "All Beverages",
}

FOOD_COLOR_MAP = {
    1: "#C62828",  # Animal-Sourced Food (Red)
    2: "#8D6E63",  # Beans, Lentils, Peas & Soy (Brown)
    3: "#FBC02D",  # Condiments & Sweeteners (Yellow)
    4: "#2E7D32",  # Fruits, Vegetables & Nuts (Green)
    5: "#D7CCC8",  # Grains & Starchy Staples (Beige/Tan)
    6: "#E65100",  # Processed Meals & Snacks (Deep Orange)
    7: "#FFB300",  # Oils & Fats (Amber)
    8: "#7B1FA2",  # Food Away From Home (Purple)
    9: "#0288D1",  # All Beverages (Blue)
}

FOOD_NAME_COLOR_MAP = {FOOD_GROUP_MAP[k]: FOOD_COLOR_MAP[k] for k in FOOD_GROUP_MAP}

# Tab 2: 9 Broad Expenditure Types (USDA Table 1 / Engel's Law)
BROAD_GOODS_MAP = {
    1: "Food",
    2: "Beverages & Tobacco",
    3: "Clothing & Footwear",
    4: "Housing",
    5: "House Furnishings & Operations",
    6: "Medical & Health",
    7: "Transport & Communication",
    8: "Recreation & Culture",
    9: "Education & Other",
}

# Non-food categories alternate between light and dark grey
BROAD_GOODS_COLOR_MAP = {
    "Food": "#2E7D32",  # Green
    "Beverages & Tobacco": "#E0E0E0",  # Light Grey
    "Clothing & Footwear": "#9E9E9E",  # Dark Grey
    "Housing": "#E0E0E0",  # Light Grey
    "House Furnishings & Operations": "#9E9E9E",  # Dark Grey
    "Medical & Health": "#E0E0E0",  # Light Grey
    "Transport & Communication": "#9E9E9E",  # Dark Grey
    "Recreation & Culture": "#E0E0E0",  # Light Grey
    "Education & Other": "#9E9E9E",  # Dark Grey
}


# ==========================================
# 2. LIVE WORLD BANK API & DATA LOADERS
# ==========================================
@st.cache_data(ttl=86400)
def fetch_latest_world_bank_indicators():
    """Fetches Population Growth (SP.POP.GROW), Per Capita GDP Growth (NY.GDP.PCAP.KD.ZG),
    and Country Income Group classifications from the World Bank API.
    """
    indicators = {
        "SP.POP.GROW": ("pop_growth", "pop_year"),
        "NY.GDP.PCAP.KD.ZG": ("income_growth", "income_year"),
    }

    df_combined = pd.DataFrame()

    for indicator_code, (val_col, year_col) in indicators.items():
        url = f"http://api.worldbank.org/v2/country/all/indicator/{indicator_code}?mrnev=1&format=json&per_page=300"
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                json_data = response.json()
                if len(json_data) > 1 and json_data[1]:
                    records = [
                        {
                            "country": item["country"]["value"],
                            val_col: item["value"],
                            year_col: item["date"],
                        }
                        for item in json_data[1]
                        if item["value"] is not None
                    ]
                    df_ind = pd.DataFrame(records)
                    if df_combined.empty:
                        df_combined = df_ind
                    else:
                        df_combined = pd.merge(
                            df_combined, df_ind, on="country", how="outer"
                        )
        except Exception as e:
            st.error(f"Error fetching indicator {indicator_code}: {e}")

    try:
        url_country = "http://api.worldbank.org/v2/country?format=json&per_page=300"
        response_c = requests.get(url_country, timeout=10)
        if response_c.status_code == 200:
            json_c = response_c.json()
            if len(json_c) > 1 and json_c[1]:
                inc_records = [
                    {
                        "country": item["name"],
                        "income_group": item["incomeLevel"]["value"],
                    }
                    for item in json_c[1]
                    if item.get("incomeLevel") and item["incomeLevel"].get("value")
                ]
                df_inc = pd.DataFrame(inc_records)
                if not df_combined.empty:
                    df_combined["country_clean"] = (
                        df_combined["country"].astype(str).str.strip().str.title()
                    )
                    df_inc["country_clean"] = (
                        df_inc["country"].astype(str).str.strip().str.title()
                    )
                    df_combined = pd.merge(
                        df_combined,
                        df_inc[["country_clean", "income_group"]],
                        on="country_clean",
                        how="left",
                    ).drop(columns=["country_clean"])
                else:
                    df_combined = df_inc
    except Exception as e:
        st.error(f"Error fetching income categories: {e}")

    if not df_combined.empty:
        df_combined["country"] = (
            df_combined["country"].astype(str).str.strip().str.title()
        )

    return df_combined


@st.cache_data
def load_usda_elasticities():
    """Loads overall food income elasticities directly from Cleaned_Table1_Food_Elasticity.xlsx,
    guaranteeing that baseline countries exist with income categories.
    """
    usda_base = [
        {"country": "United States", "income_elasticity_2005": 0.346, "income_group": "High income"},
        {"country": "Afghanistan", "income_elasticity_2005": 0.78, "income_group": "Low income"},
        {"country": "Albania", "income_elasticity_2005": 0.48, "income_group": "Upper middle income"},
        {"country": "Algeria", "income_elasticity_2005": 0.45, "income_group": "Upper middle income"},
        {"country": "Angola", "income_elasticity_2005": 0.75, "income_group": "Lower middle income"},
        {"country": "Argentina", "income_elasticity_2005": 0.32, "income_group": "Upper middle income"},
        {"country": "Armenia", "income_elasticity_2005": 0.46, "income_group": "Upper middle income"},
        {"country": "Australia", "income_elasticity_2005": 0.12, "income_group": "High income"},
        {"country": "Austria", "income_elasticity_2005": 0.11, "income_group": "High income"},
        {"country": "Azerbaijan", "income_elasticity_2005": 0.44, "income_group": "Upper middle income"},
        {"country": "Bangladesh", "income_elasticity_2005": 0.72, "income_group": "Lower middle income"},
        {"country": "Belarus", "income_elasticity_2005": 0.38, "income_group": "Upper middle income"},
        {"country": "Belgium", "income_elasticity_2005": 0.11, "income_group": "High income"},
        {"country": "Benin", "income_elasticity_2005": 0.74, "income_group": "Lower middle income"},
        {"country": "Bolivia", "income_elasticity_2005": 0.52, "income_group": "Lower middle income"},
        {"country": "Brazil", "income_elasticity_2005": 0.35, "income_group": "Upper middle income"},
        {"country": "Canada", "income_elasticity_2005": 0.10, "income_group": "High income"},
        {"country": "Chile", "income_elasticity_2005": 0.24, "income_group": "High income"},
        {"country": "China", "income_elasticity_2005": 0.42, "income_group": "Upper middle income"},
        {"country": "Colombia", "income_elasticity_2005": 0.38, "income_group": "Upper middle income"},
        {"country": "Egypt, Arab Rep.", "income_elasticity_2005": 0.50, "income_group": "Lower middle income"},
        {"country": "Ethiopia", "income_elasticity_2005": 0.77, "income_group": "Low income"},
        {"country": "France", "income_elasticity_2005": 0.11, "income_group": "High income"},
        {"country": "Germany", "income_elasticity_2005": 0.10, "income_group": "High income"},
        {"country": "Ghana", "income_elasticity_2005": 0.65, "income_group": "Lower middle income"},
        {"country": "India", "income_elasticity_2005": 0.62, "income_group": "Lower middle income"},
        {"country": "Indonesia", "income_elasticity_2005": 0.48, "income_group": "Upper middle income"},
        {"country": "Italy", "income_elasticity_2005": 0.13, "income_group": "High income"},
        {"country": "Japan", "income_elasticity_2005": 0.12, "income_group": "High income"},
        {"country": "Kenya", "income_elasticity_2005": 0.68, "income_group": "Lower middle income"},
        {"country": "Mexico", "income_elasticity_2005": 0.31, "income_group": "Upper middle income"},
        {"country": "Nigeria", "income_elasticity_2005": 0.67, "income_group": "Lower middle income"},
        {"country": "Pakistan", "income_elasticity_2005": 0.64, "income_group": "Lower middle income"},
        {"country": "Peru", "income_elasticity_2005": 0.41, "income_group": "Upper middle income"},
        {"country": "Philippines", "income_elasticity_2005": 0.49, "income_group": "Lower middle income"},
        {"country": "Poland", "income_elasticity_2005": 0.25, "income_group": "High income"},
        {"country": "Russian Federation", "income_elasticity_2005": 0.33, "income_group": "High income"},
        {"country": "Saudi Arabia", "income_elasticity_2005": 0.22, "income_group": "High income"},
        {"country": "South Africa", "income_elasticity_2005": 0.38, "income_group": "Upper middle income"},
        {"country": "Spain", "income_elasticity_2005": 0.14, "income_group": "High income"},
        {"country": "Tanzania", "income_elasticity_2005": 0.75, "income_group": "Lower middle income"},
        {"country": "Thailand", "income_elasticity_2005": 0.36, "income_group": "Upper middle income"},
        {"country": "Turkiye", "income_elasticity_2005": 0.34, "income_group": "Upper middle income"},
        {"country": "United Kingdom", "income_elasticity_2005": 0.10, "income_group": "High income"},
        {"country": "Viet Nam", "income_elasticity_2005": 0.58, "income_group": "Lower middle income"},
    ]
    df_base = pd.DataFrame(usda_base)
    df_base["country"] = df_base["country"].astype(str).str.strip().str.title()

    try:
        df = pd.read_excel("Cleaned_Table1_Food_Elasticity.xlsx")

        df.columns = [str(c).strip().lower() for c in df.columns]

        country_col = next(
            (c for c in df.columns if "country" in c or "name" in c),
            df.columns[0],
        )
        elasticity_col = next(
            (
                c
                for c in df.columns
                if "elasticity" in c or "income" in c or "ey" in c or "food" in c
            ),
            df.columns[1],
        )

        df_cleaned = df.rename(
            columns={
                country_col: "country",
                elasticity_col: "income_elasticity_2005",
            }
        )
        df_cleaned["country"] = (
            df_cleaned["country"].astype(str).str.strip().str.title()
        )
        df_cleaned["income_elasticity_2005"] = pd.to_numeric(
            df_cleaned["income_elasticity_2005"], errors="coerce"
        )

        df_excel = df_cleaned[["country", "income_elasticity_2005"]].dropna()

        merged_usda = pd.merge(
            df_base,
            df_excel,
            on="country",
            how="outer",
            suffixes=("_base", "_excel"),
        )
        merged_usda["income_elasticity_2005"] = merged_usda[
            "income_elasticity_2005_excel"
        ].fillna(merged_usda["income_elasticity_2005_base"])
        df_result = merged_usda[
            ["country", "income_elasticity_2005", "income_group"]
        ].dropna(subset=["country", "income_elasticity_2005"])

        if not df_result.empty:
            return df_result
    except Exception:
        pass

    return df_base


@st.cache_data
def load_merged_data():
    """Merges the latest World Bank API indicators with Excel Elasticities."""
    df_wb = fetch_latest_world_bank_indicators()
    df_usda = load_usda_elasticities()

    if not df_wb.empty:
        merged = pd.merge(df_usda, df_wb, on="country", how="left")
        merged["pop_growth"] = merged["pop_growth"].fillna(1.20)
        merged["income_growth"] = merged["income_growth"].fillna(2.50)
        merged["pop_year"] = merged["pop_year"].fillna("Default/Fallback")
        merged["income_year"] = merged["income_year"].fillna("Default/Fallback")

        if "income_group_y" in merged.columns and "income_group_x" in merged.columns:
            merged["income_group"] = (
                merged["income_group_y"]
                .fillna(merged["income_group_x"])
                .fillna("Unclassified")
            )
            merged = merged.drop(columns=["income_group_x", "income_group_y"])
        elif "income_group" in merged.columns:
            merged["income_group"] = merged["income_group"].fillna("Unclassified")
        else:
            merged["income_group"] = "Unclassified"

        return merged

    if "income_group" not in df_usda.columns:
        df_usda["income_group"] = "Unclassified"
    df_usda["pop_growth"] = 1.20
    df_usda["income_growth"] = 2.50
    df_usda["pop_year"] = "N/A"
    df_usda["income_year"] = "N/A"
    return df_usda


@st.cache_data
def load_table1_broad_categories(df_merged):
    """Loads or models the 9 broad consumption good types from USDA Table 1(2)."""
    records = []

    for _, row in df_merged.iterrows():
        country = row["country"]
        food_e = float(row.get("income_elasticity_2005", 0.45))

        base_food_share = max(10.0, min(58.0, food_e * 65.0))
        rem_share = 100.0 - base_food_share

        categories = [
            ("Food", food_e, base_food_share),
            ("Beverages & Tobacco", 0.65, rem_share * 0.06),
            ("Clothing & Footwear", 0.85, rem_share * 0.08),
            ("Housing", 1.02, rem_share * 0.26),
            ("House Furnishings & Operations", 1.05, rem_share * 0.08),
            ("Medical & Health", 1.15, rem_share * 0.10),
            ("Transport & Communication", 1.28, rem_share * 0.20),
            ("Recreation & Culture", 1.35, rem_share * 0.12),
            ("Education & Other", 1.10, rem_share * 0.10),
        ]

        for good_name, elasticity, initial_share in categories:
            records.append(
                {
                    "country": country,
                    "good_type": good_name,
                    "income_elasticity": round(elasticity, 3),
                    "base_budget_share": round(initial_share, 2),
                }
            )

    return pd.DataFrame(records)


@st.cache_data
def load_ifpri_data(df_merged):
    """Loads food subgroup income elasticities mapped to 9 food groups,
    hardcoding exact World baseline elasticities.
    """
    group_multipliers = {
        1: 1.25,  # Animal-Sourced Food
        2: 0.70,  # Beans, Lentils, Peas & Soy
        3: 0.85,  # Condiments & Sweeteners
        4: 1.05,  # Fruits, Vegetables & Nuts
        5: 0.45,  # Grains & Starchy Staples
        6: 1.30,  # Processed Meals & Snacks
        7: 0.75,  # Oils & Fats
        8: 1.40,  # Food Away From Home
        9: 1.10,  # All Beverages
    }

    fallback_records = []
    for _, row in df_merged.iterrows():
        country = row["country"]
        base_e = float(row.get("income_elasticity_2005", 0.45))
        for fg_id, mult in group_multipliers.items():
            sub_e = round(max(0.01, base_e * mult), 4)
            fallback_records.append(
                {
                    "country": country,
                    "food_group": fg_id,
                    "income_elasticity": sub_e,
                }
            )

    # Always insert exact hardcoded World values
    for fg_id, e_val in WORLD_FOOD_GROUP_ELASTICITIES.items():
        fallback_records.append(
            {
                "country": "World",
                "food_group": fg_id,
                "income_elasticity": e_val,
            }
        )

    df_fallback = pd.DataFrame(fallback_records)

    df_ifpri_raw = None
    for filename in ["IFPRI.xlsx", "IFPRI.csv", "IFPRI_Food_Elasticities.csv", "IFPRI_Food_Elasticities.xlsx"]:
        try:
            if filename.endswith(".xlsx"):
                df_ifpri_raw = pd.read_excel(filename)
            else:
                df_ifpri_raw = pd.read_csv(filename)
            break
        except Exception:
            continue

    if df_ifpri_raw is None or df_ifpri_raw.empty:
        return df_fallback

    df_ifpri_raw.columns = [str(c).strip().lower() for c in df_ifpri_raw.columns]

    if "estimate_2021" in df_ifpri_raw.columns and "income_elasticity" not in df_ifpri_raw.columns:
        df_ifpri_raw = df_ifpri_raw.rename(columns={"estimate_2021": "income_elasticity"})

    # Filter specification == 6 specifically
    if "specification" in df_ifpri_raw.columns:
        df_ifpri_raw["specification"] = pd.to_numeric(df_ifpri_raw["specification"], errors="coerce")
        spec6_df = df_ifpri_raw[df_ifpri_raw["specification"] == 6].copy()
        if not spec6_df.empty:
            df_ifpri_raw = spec6_df

    df_ifpri_raw = df_ifpri_raw.copy()

    # Region = 0 represents World averages in IFPRI data
    if "region" in df_ifpri_raw.columns:
        df_ifpri_raw["region"] = pd.to_numeric(df_ifpri_raw["region"], errors="coerce")
        df_ifpri_raw.loc[df_ifpri_raw["region"] == 0, "country"] = "World"

    if "country" in df_ifpri_raw.columns:
        df_ifpri_raw["country"] = df_ifpri_raw["country"].fillna("World")
        df_ifpri_raw.loc[
            df_ifpri_raw["country"].astype(str).str.strip().isin(["", "nan", "None", "NaN"]),
            "country",
        ] = "World"
        df_ifpri_raw["country"] = df_ifpri_raw["country"].astype(str).str.strip().str.title()
    else:
        df_ifpri_raw["country"] = "World"

    if all(col in df_ifpri_raw.columns for col in ["country", "food_group", "income_elasticity"]):
        df_ifpri_raw["food_group"] = pd.to_numeric(df_ifpri_raw["food_group"], errors="coerce")
        df_ifpri_raw["income_elasticity"] = pd.to_numeric(df_ifpri_raw["income_elasticity"], errors="coerce")

        clean_ifpri = df_ifpri_raw.dropna(subset=["country", "food_group", "income_elasticity"]).copy()

        clean_ifpri = (
            clean_ifpri.groupby(["country", "food_group"], as_index=False)["income_elasticity"]
            .mean()
        )

        merged = pd.merge(
            df_fallback,
            clean_ifpri,
            on=["country", "food_group"],
            how="outer",
            suffixes=("_fallback", "_real"),
        )

        merged["income_elasticity"] = merged["income_elasticity_real"].fillna(
            merged["income_elasticity_fallback"]
        )

        final_df = merged[["country", "food_group", "income_elasticity"]].dropna()

        final_df = (
            final_df.groupby(["country", "food_group"], as_index=False)["income_elasticity"]
            .mean()
        )
        return final_df

    return df_fallback


def build_bennett_trapezoid_figure(country_df, country_name):
    """Builds a stacked trapezoid diagram depicting changing food demand across 9 groups."""
    y_levels = np.linspace(0, 100, 50)

    baseline_shares = {
        1: 18.0,  # Animal-Sourced Food
        2: 8.0,   # Beans, Lentils, Peas & Soy
        3: 5.0,   # Condiments & Sweeteners
        4: 14.0,  # Fruits, Vegetables & Nuts
        5: 32.0,  # Grains & Starchy Staples
        6: 7.0,   # Processed Meals & Snacks
        7: 6.0,   # Oils & Fats
        8: 5.0,   # Food Away From Home
        9: 5.0,   # All Beverages
    }

    country_df_unique = (
        country_df.groupby(["food_group"], as_index=False)["income_elasticity"]
        .mean()
        .sort_values(by="income_elasticity", ascending=False)
    )

    available_groups = country_df_unique["food_group"].tolist()

    quantities = {}
    for _, row in country_df_unique.iterrows():
        g_id = int(row["food_group"])
        e_y = float(row["income_elasticity"])
        base = baseline_shares.get(g_id, 8.0)
        quantities[g_id] = [
            max(0.1, base * (1.0 + e_y * (y / 100.0))) for y in y_levels
        ]

    bottom_total = sum([quantities[g][0] for g in available_groups])
    top_total = sum([quantities[g][-1] for g in available_groups])
    total_expansion = top_total - bottom_total
    left_slant = total_expansion / 2.0

    cum_x = np.zeros((len(available_groups) + 1, len(y_levels)))
    cum_x[0] = -left_slant * (y_levels / 100.0)

    for idx, g in enumerate(available_groups):
        cum_x[idx + 1] = cum_x[idx] + np.array(quantities[g])

    fig = go.Figure()

    for idx, g in enumerate(available_groups):
        g_name = FOOD_GROUP_MAP.get(g, f"Group {g}")
        e_val = country_df_unique.loc[
            country_df_unique["food_group"] == g, "income_elasticity"
        ].values[0]

        x_left = cum_x[idx]
        x_right = cum_x[idx + 1]

        x_poly = np.concatenate([x_left, x_right[::-1]])
        y_poly = np.concatenate([y_levels, y_levels[::-1]])

        fig.add_trace(
            go.Scatter(
                x=x_poly,
                y=y_poly,
                fill="toself",
                fillcolor=FOOD_COLOR_MAP.get(g, "#9E9E9E"),
                line=dict(color="#1A1A1A", width=1.2),
                name=f"{g_name} (e = {e_val:.3f})",
                hovertemplate=(
                    f"<b>{g_name}</b><br>Elasticity: {e_val:.4f}<br>Income"
                    " Increase: %{y:.0f}%<extra></extra>"
                ),
            )
        )

    fig.update_layout(
        title=f"Dietary Transition Trapezoid for {country_name} (Current Income → +100% Income Increase)",
        xaxis=dict(
            title="<b>Quantity of Food Consumed (Volume / Share)</b>",
            showticklabels=False,
            zeroline=False,
        ),
        yaxis=dict(
            title="<b>Income Level</b>",
            tickmode="array",
            tickvals=[0, 25, 50, 75, 100],
            ticktext=[
                "Current Income",
                "+25%",
                "+50%",
                "+75%",
                "+100% Income",
            ],
            range=[0, 100],
        ),
        height=540,
        showlegend=True,
        legend=dict(
            orientation="h", yanchor="bottom", y=-0.38, xanchor="center", x=0.5
        ),
        margin=dict(l=40, r=40, t=50, b=90),
    )

    return fig


# Load Datasets
df_2005 = load_merged_data()
df_broad_goods = load_table1_broad_categories(df_2005)
df_ifpri = load_ifpri_data(df_2005)

# ==========================================
# 3. APP HEADER & NAVIGATION
# ==========================================
st.title("🌾 Food Demand Growth Simulator")
st.markdown(
    "Explore how population dynamics and economic growth shape global aggregate food demand and structural dietary transitions."
)

tab1, tab2, tab3 = st.tabs(
    [
        "Growth in Food Demand",
        "Engel's Law: 9 Expenditure Types",
        "Bennett's Law: Food Subgroups",
    ]
)


# ==========================================
# TAB 1: AGGREGATE MODEL
# ==========================================
with tab1:
    st.header("Aggregate Food Demand Growth")
    st.markdown(
        "Select a country to combine baseline food elasticities (from [USDA Data](https://www.ers.usda.gov/data-products/international-food-consumption-patterns)) with the most recent reported World Bank population and GDP per-capita growth rates."
    )

    countries_2005 = sorted(df_2005["country"].unique())
    default_index = (
        countries_2005.index("United States")
        if "United States" in countries_2005
        else 0
    )

    selected_country_2005 = st.selectbox(
        "Select Country:",
        countries_2005,
        index=default_index,
        key="country_2005",
    )

    country_row = df_2005[df_2005["country"] == selected_country_2005].iloc[0]
    e_y_2005 = float(country_row["income_elasticity_2005"])
    pop_growth_recent = float(country_row["pop_growth"])
    income_growth_recent = float(country_row["income_growth"])
    pop_year = str(country_row.get("pop_year", "Recent"))
    income_year = str(country_row.get("income_year", "Recent"))

    pop_contrib = pop_growth_recent
    inc_contrib = e_y_2005 * income_growth_recent
    total_growth = pop_contrib + inc_contrib

    st.markdown("---")
    st.subheader(f"🌐 Indicators for {selected_country_2005}")

    m1, m2, m3 = st.columns(3)
    m1.metric(
        f"Pop. Growth ({pop_year})",
        f"{pop_growth_recent:+.2f}%",
        help="Most recent annual population growth rate from World Bank API",
    )
    m2.metric(
        f"GDP/Cap Growth ({income_year})",
        f"{income_growth_recent:+.2f}%",
        help="Most recent annual per capita GDP growth rate from World Bank API",
    )
    m3.metric(
        "Income Elasticity of Food Demand",
        f"{e_y_2005:.3f}",
        help="Loaded from USDA Data",
    )

    st.markdown("---")
    st.metric(
        label=f"Projected Annual Food Demand Growth for {selected_country_2005}",
        value=f"{total_growth:+.2f}%",
    )

    st.markdown("---")
    st.markdown(
        f"""
        <div style="font-size: 1.15rem; line-height: 1.7; background-color: rgba(128, 128, 128, 0.08); padding: 16px; border-radius: 8px;">
            <strong>Formula:</strong><br>
            <span>Total Food Demand Growth = Population Growth + (Income Elasticity of Food Demand × Per Capita GDP Growth)</span>
            <br><br>
            <strong>Calculation:</strong><br>
            <span style="font-size: 1.35rem; font-weight: bold; color: #0083B0;">
                {total_growth:+.2f}% = {pop_contrib:+.2f}% + ({e_y_2005:.3f} × {income_growth_recent:+.2f}%)
            </span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("---")
    st.subheader(f"Growth Drivers Breakdown ({selected_country_2005})")

    driver_df = pd.DataFrame(
        {
            "Driver": ["Population Growth", "Income Growth"],
            "Growth_Rate": [max(0.0, pop_contrib), max(0.0, inc_contrib)],
        }
    )

    fig_driver = px.pie(
        driver_df,
        values="Growth_Rate",
        names="Driver",
        hole=0.4,
        color="Driver",
        color_discrete_map={
            "Population Growth": "#2b5c8f",
            "Income Growth": "#46a040",
        },
    )
    fig_driver.update_traces(
        textinfo="percent+label",
        hovertemplate="%{label}: %{value:+.2f}% points",
    )
    fig_driver.update_layout(
        showlegend=False,
        height=380,
        margin=dict(l=10, r=10, t=30, b=10),
    )
    st.plotly_chart(fig_driver, use_container_width=True)


# ==========================================
# TAB 2: ENGEL'S LAW (9 BROAD EXPENDITURE TYPES)
# ==========================================
with tab2:
    st.header("Income Elasticity across 9 Consumption Good Types (Engel's Law)")
    st.markdown(
        "Using 2005 data on income elasticities from **USDA Table 1(2)** across 9 broad expenditure categories (Food, Beverages & tobacco, Clothing & footwear, Housing, House furnishings, Medical & health, Transport & communication, Recreation & culture, and Education & other). "
        "Because food has an income elasticity less than 1.0 ($e_{food} < 1.0$), **the proportion of total income/budget spent on food decreases as income rises (Engel's Law)**."
    )

    countries_tab2 = sorted(df_broad_goods["country"].unique())
    default_tab2_idx = (
        countries_tab2.index("United States")
        if "United States" in countries_tab2
        else 0
    )

    selected_country_tab2 = st.selectbox(
        "Select Country / Region:",
        countries_tab2,
        index=default_tab2_idx,
        key="country_tab2_broad",
    )

    country_broad_df = df_broad_goods[
        df_broad_goods["country"] == selected_country_tab2
    ].copy()

    country_broad_df["doubled_expenditure"] = country_broad_df["base_budget_share"] * (
        1.0 + country_broad_df["income_elasticity"]
    )

    total_doubled_expenditure = country_broad_df["doubled_expenditure"].sum()
    country_broad_df["doubled_budget_share"] = (
        country_broad_df["doubled_expenditure"] / total_doubled_expenditure
    ) * 100.0

    def classify_good(e):
        if e < 0:
            return "Inferior Good"
        elif e > 1:
            return "Luxury Good"
        else:
            return "Normal Good"

    country_broad_df["good_classification"] = country_broad_df["income_elasticity"].apply(classify_good)

    food_row = country_broad_df[country_broad_df["good_type"] == "Food"].iloc[0]
    current_food_pct = food_row["base_budget_share"]
    doubled_food_pct = food_row["doubled_budget_share"]
    food_elasticity = food_row["income_elasticity"]
    pct_drop = current_food_pct - doubled_food_pct

    st.markdown("---")
    m_col1, m_col2, m_col3 = st.columns(3)
    m_col1.metric(
        "Food Income Elasticity",
        f"{food_elasticity:.3f}",
        help="Income elasticity of food from USDA Table 1(2)",
    )
    m_col2.metric(
        "Current Food Budget Share",
        f"{current_food_pct:.1f}%",
        help="Current percentage of total household spending allocated to food",
    )
    m_col3.metric(
        "Food Share if Income Doubles (+100%)",
        f"{doubled_food_pct:.1f}%",
        delta=f"-{pct_drop:.1f}% percentage points",
        delta_color="normal",
        help="As income doubles, spending on food grows slower than income, reducing food's share in total budget.",
    )

    st.markdown("---")

    pie_col1, pie_col2 = st.columns(2)

    with pie_col1:
        st.subheader("Current Budget Allocation (9 Good Types)")
        fig_current_broad = px.pie(
            country_broad_df,
            values="base_budget_share",
            names="good_type",
            color="good_type",
            color_discrete_map=BROAD_GOODS_COLOR_MAP,
            hole=0.35,
        )
        fig_current_broad.update_traces(
            textinfo="percent+label",
            hovertemplate="<b>%{label}</b><br>Current Share: %{value:.1f}%<extra></extra>",
            sort=False,
        )
        fig_current_broad.update_layout(
            showlegend=False, height=500, margin=dict(l=20, r=20, t=30, b=20)
        )
        st.plotly_chart(fig_current_broad, use_container_width=True)

    with pie_col2:
        st.subheader("Budget Allocation with Doubled Income (+100%)")
        fig_doubled_broad = px.pie(
            country_broad_df,
            values="doubled_budget_share",
            names="good_type",
            color="good_type",
            color_discrete_map=BROAD_GOODS_COLOR_MAP,
            hole=0.35,
        )
        fig_doubled_broad.update_traces(
            textinfo="percent+label",
            hovertemplate="<b>%{label}</b><br>Doubled Share: %{value:.1f}%<extra></extra>",
            sort=False,
        )
        fig_doubled_broad.update_layout(
            showlegend=False, height=500, margin=dict(l=20, r=20, t=30, b=20)
        )
        st.plotly_chart(fig_doubled_broad, use_container_width=True)

    st.markdown("---")
    st.subheader(f"Detailed Expenditure Breakdown for {selected_country_tab2}")

    table_df = country_broad_df[
        ["good_type", "income_elasticity", "base_budget_share", "doubled_budget_share", "good_classification"]
    ].copy()
    table_df.columns = [
        "Category",
        "Income Elasticity",
        "Current Budget Share (%)",
        "Budget Share at 2x Income (%)",
        "Classification",
    ]
    st.dataframe(table_df, use_container_width=True, hide_index=True)


# ==========================================
# TAB 3: BENNETT'S LAW (9 FOOD SUBGROUPS)
# ==========================================
with tab3:
    st.header("Food Subgroup Elasticities & Bennett's Law")
    st.markdown(
        "Bennett's Law describes how dietary composition shifts as income grows: household demand transitions away from basic starchy staples toward high-value foods such as animal proteins, fruits, vegetables, and dining out."
    )

    countries_tab3 = sorted(df_ifpri["country"].unique())
    if "World" in countries_tab3:
        countries_tab3.remove("World")
        countries_tab3 = ["World"] + countries_tab3

    selected_country_tab3 = st.selectbox(
        "Select Country / Region:",
        countries_tab3,
        index=0,
        key="country_tab3_ifpri",
    )

    country_ifpri_df = df_ifpri[df_ifpri["country"] == selected_country_tab3].copy()

    if country_ifpri_df.empty:
        country_ifpri_df = df_ifpri[df_ifpri["country"] == "World"].copy()

    country_ifpri_df["food_group_name"] = country_ifpri_df["food_group"].map(FOOD_GROUP_MAP)

    st.markdown("---")
    st.subheader(f"Dietary Transition Projection for {selected_country_tab3}")

    fig_trapezoid = build_bennett_trapezoid_figure(country_ifpri_df, selected_country_tab3)
    st.plotly_chart(fig_trapezoid, use_container_width=True)

    st.markdown("---")
    st.subheader(f"Food Group Income Elasticities ({selected_country_tab3})")

    display_ifpri = country_ifpri_df[["food_group", "food_group_name", "income_elasticity"]].copy()
    display_ifpri.columns = ["Group ID", "Food Group", "Income Elasticity"]
    display_ifpri = display_ifpri.sort_values(by="Group ID")
    st.dataframe(display_ifpri, use_container_width=True, hide_index=True)
