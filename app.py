import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import streamlit as st

# ==========================================
# 1. PAGE CONFIGURATION & GLOBAL COLOR MAPS
# ==========================================
st.set_page_config(
    page_title="Food Demand Growth Simulator", page_icon="🌾", layout="wide"
)

# Tab 3: Food Subgroups (Bennett's Law) - CORRECTED IFPRI MAPPING
FOOD_GROUP_MAP = {
    1: "Grains & Cereals",
    2: "Roots & Tubers",
    3: "Beans, Nuts & Seeds",
    4: "Milk & Dairy",
    5: "Meat & Poultry",
    6: "Fish & Seafood",
    7: "Eggs",
    8: "Fruits & Vegetables",
    9: "Fats & Oils",
}

FOOD_COLOR_MAP = {
    1: "#D7CCC8",  # Grains & Cereals
    2: "#BCAAA4",  # Roots & Tubers
    3: "#8D6E63",  # Beans, Nuts & Seeds
    4: "#64B5F6",  # Milk & Dairy
    5: "#C62828",  # Meat & Poultry
    6: "#0288D1",  # Fish & Seafood
    7: "#FFF176",  # Eggs
    8: "#2E7D32",  # Fruits & Vegetables
    9: "#FBC02D",  # Fats & Oils
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

BROAD_GOODS_COLOR_MAP = {
    "Food": "#2E7D32",                      
    "Beverages & Tobacco": "#8D6E63",       
    "Clothing & Footwear": "#E64A19",        
    "Housing": "#1976D2",                    
    "House Furnishings & Operations": "#009688", 
    "Medical & Health": "#D32F2F",          
    "Transport & Communication": "#7B1FA2", 
    "Recreation & Culture": "#FBC02D",      
    "Education & Other": "#455A64",         
}


# ==========================================
# 2. LIVE WORLD BANK API & DATA LOADERS
# ==========================================
@st.cache_data(ttl=86400)
def fetch_latest_world_bank_indicators():
    """Fetches the most recent non-empty Population Growth and Per Capita GDP Growth."""
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

    if not df_combined.empty:
        df_combined["country"] = (
            df_combined["country"].astype(str).str.strip().str.title()
        )

    return df_combined


@st.cache_data
def load_usda_elasticities():
    """Loads overall food income elasticities directly from Cleaned_Table1_Food_Elasticity.xlsx."""
    usda_base = [
        {"country": "United States", "income_elasticity_2005": 0.346},
        {"country": "China", "income_elasticity_2005": 0.42},
        {"country": "India", "income_elasticity_2005": 0.62},
        {"country": "Nigeria", "income_elasticity_2005": 0.67},
        {"country": "United Kingdom", "income_elasticity_2005": 0.10},
    ]
    df_base = pd.DataFrame(usda_base)
    df_base["country"] = df_base["country"].astype(str).str.strip().str.title()

    try:
        df = pd.read_excel("Cleaned_Table1_Food_Elasticity.xlsx")
        df.columns = [str(c).strip().lower() for c in df.columns]

        country_col = next((c for c in df.columns if "country" in c or "name" in c), df.columns[0])
        elasticity_col = next((c for c in df.columns if "elasticity" in c or "income" in c or "ey" in c or "food" in c), df.columns[1])

        df_cleaned = df.rename(columns={country_col: "country", elasticity_col: "income_elasticity_2005"})
        df_cleaned["country"] = df_cleaned["country"].astype(str).str.strip().str.title()
        df_cleaned["income_elasticity_2005"] = pd.to_numeric(df_cleaned["income_elasticity_2005"], errors="coerce")
        df_excel = df_cleaned[["country", "income_elasticity_2005"]].dropna()

        merged_usda = pd.merge(df_base, df_excel, on="country", how="outer", suffixes=("_base", "_excel"))
        merged_usda["income_elasticity_2005"] = merged_usda["income_elasticity_2005_excel"].fillna(merged_usda["income_elasticity_2005_base"])
        df_result = merged_usda[["country", "income_elasticity_2005"]].dropna()

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
        return merged

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
            records.append({
                "country": country,
                "good_type": good_name,
                "income_elasticity": round(elasticity, 3),
                "base_budget_share": round(initial_share, 2),
            })
    return pd.DataFrame(records)


@st.cache_data
def load_ifpri_data(df_merged):
    """Loads food subgroup income elasticities from IFPRI.xlsx (Specification 6)."""
    group_multipliers = {
        1: 0.40, 2: 0.30, 3: 0.50, 4: 1.10, 5: 1.30, 6: 1.20, 7: 1.00, 8: 1.15, 9: 0.80,
    }
    fallback_records = []
    for _, row in df_merged.iterrows():
        country = row["country"]
        base_e = float(row.get("income_elasticity_2005", 0.45))
        for fg_id, mult in group_multipliers.items():
            sub_e = round(max(0.01, base_e * mult), 2)
            fallback_records.append({"country": country, "food_group": fg_id, "income_elasticity": sub_e})
    df_fallback = pd.DataFrame(fallback_records)

    try:
        # Load directly from the new file
        df_ifpri_raw = pd.read_excel("IFPRI.xlsx")

        df_ifpri_raw.columns = [str(c).strip().lower() for c in df_ifpri_raw.columns]

        if "estimate_2021" in df_ifpri_raw.columns:
            df_ifpri_raw = df_ifpri_raw.rename(columns={"estimate_2021": "income_elasticity"})

        if "specification" in df_ifpri_raw.columns:
            df_ifpri_raw = df_ifpri_raw[df_ifpri_raw["specification"] == 6]

        # Explicitly label Region 0 as "World Average"
        if "region" in df_ifpri_raw.columns:
            df_ifpri_raw.loc[df_ifpri_raw["region"] == 0, "country"] = "World Average"

        if all(col in df_ifpri_raw.columns for col in ["country", "food_group", "income_elasticity"]):
            df_ifpri_raw["country"] = df_ifpri_raw["country"].astype(str).str.strip().str.title()
            
            # Ensure "World Average" retains its proper casing after the .title() cast
            df_ifpri_raw["country"] = df_ifpri_raw["country"].replace({"World Average": "World Average"})
            
            df_ifpri_raw["food_group"] = pd.to_numeric(df_ifpri_raw["food_group"], errors="coerce")
            df_ifpri_raw["income_elasticity"] = pd.to_numeric(df_ifpri_raw["income_elasticity"], errors="coerce")

            merged = pd.merge(
                df_fallback,
                df_ifpri_raw.dropna(subset=["country", "food_group", "income_elasticity"]),
                on=["country", "food_group"],
                how="outer", # Changed to outer so World Average isn't dropped if not in fallback
                suffixes=("_fallback", "_real")
            )
            merged["income_elasticity"] = merged["income_elasticity_real"].fillna(merged["income_elasticity_fallback"])
            return merged[["country", "food_group", "income_elasticity"]].dropna()
    except Exception as e:
        print(f"Failed to load or parse IFPRI.xlsx: {e}")
        pass

    return df_fallback


def build_bennett_trapezoid_figure(country_df, country_name):
    """Builds a stacked trapezoid diagram depicting changing food demand as income grows."""
    y_levels = np.linspace(0, 100, 50)
    baseline_shares = {1: 30.0, 2: 10.0, 3: 8.0, 4: 10.0, 5: 10.0, 6: 5.0, 7: 4.0, 8: 15.0, 9: 8.0}

    country_df_sorted = country_df.sort_values(by="income_elasticity", ascending=False).copy()
    available_groups = country_df_sorted["food_group"].tolist()

    quantities = {}
    for _, row in country_df_sorted.iterrows():
        g_id = int(row["food_group"])
        e_y = float(row["income_elasticity"])
        base = baseline_shares.get(g_id, 8.0)
        quantities[g_id] = [max(0.1, base * (1.0 + e_y * (y / 100.0))) for y in y_levels]

    bottom_total = sum([quantities[g][0] for g in available_groups])
    top_total = sum([quantities[g][-1] for g in available_groups])
    left_slant = (top_total - bottom_total) / 2.0

    cum_x = np.zeros((len(available_groups) + 1, len(y_levels)))
    cum_x[0] = -left_slant * (y_levels / 100.0)

    for idx, g in enumerate(available_groups):
        cum_x[idx + 1] = cum_x[idx] + np.array(quantities[g])

    fig = go.Figure()
    for idx, g in enumerate(available_groups):
        g_name = FOOD_GROUP_MAP.get(g, f"Group {g}")
        e_val = country_df_sorted.loc[country_df_sorted["food_group"] == g, "income_elasticity"].values[0]

        x_poly = np.concatenate([cum_x[idx], cum_x[idx + 1][::-1]])
        y_poly = np.concatenate([y_levels, y_levels[::-1]])

        fig.add_trace(
            go.Scatter(
                x=x_poly, y=y_poly, fill="toself", fillcolor=FOOD_COLOR_MAP.get(g, "#9E9E9E"),
                line=dict(color="#1A1A1A", width=1.2), name=f"{g_name} (e = {e_val:.2f})",
                hovertemplate=f"<b>{g_name}</b><br>Elasticity: {e_val:.2f}<br>Income Increase: %{{y:.0f}}%<extra></extra>",
            )
        )

    fig.update_layout(
        title=f"Dietary Transition Trapezoid for {country_name} (Current Income → +100% Income Increase)",
        xaxis=dict(title="<b>Quantity of Food Consumed (Volume / Share)</b>", showticklabels=False, zeroline=False),
        yaxis=dict(
            title="<b>Income Level</b>", tickmode="array", tickvals=[0, 25, 50, 75, 100],
            ticktext=["Current Income", "+25%", "+50%", "+75%", "+100% Income"], range=[0, 100],
        ),
        height=540, showlegend=True, legend=dict(orientation="h", yanchor="bottom", y=-0.38, xanchor="center", x=0.5),
        margin=dict(l=40, r=40, t=50, b=90),
    )
    return fig


# Styling Functions for Tab 3 Dataframe
def highlight_inferior(val):
    """Highlights negative numerical values (inferior goods) in red."""
    if isinstance(val, (int, float)) and val < 0:
        return "color: #D32F2F; font-weight: bold; background-color: #FFEBEE;"
    return ""

def highlight_food_category(col):
    """Matches the background color of the food category column to the charts."""
    styles = []
    for val in col:
        bg_color = FOOD_NAME_COLOR_MAP.get(val, "#FFFFFF")
        text_color = "#FFFFFF" if bg_color in ["#2E7D32", "#C62828", "#0288D1"] else "#000000"
        styles.append(f"background-color: {bg_color}; color: {text_color}; text-align: center !important;")
    return styles


# Load Datasets
df_2005 = load_merged_data()
df_broad_goods = load_table1_broad_categories(df_2005)
df_ifpri = load_ifpri_data(df_2005)

# ==========================================
# 3. APP HEADER & NAVIGATION
# ==========================================
st.title("🌾 Food Demand Growth Simulator")
st.markdown("Explore how population dynamics and economic growth shape global aggregate food demand and structural dietary transitions.")

tab1, tab2, tab3 = st.tabs(["Growth in Food Demand", "Engel's Law: 9 Expenditure Types", "Bennett's Law: Food Subgroups"])

# ==========================================
# TAB 1: AGGREGATE MODEL
# ==========================================
with tab1:
    st.header("Aggregate Food Demand Growth")
    countries_2005 = sorted(df_2005["country"].unique())
    default_index = countries_2005.index("United States") if "United States" in countries_2005 else 0

    selected_country_2005 = st.selectbox("Select Country:", countries_2005, index=default_index, key="country_2005")

    country_row = df_2005[df_2005["country"] == selected_country_2005].iloc[0]
    e_y_2005, pop_growth_recent, income_growth_recent = float(country_row["income_elasticity_2005"]), float(country_row["pop_growth"]), float(country_row["income_growth"])
    pop_year, income_year = str(country_row.get("pop_year", "Recent")), str(country_row.get("income_year", "Recent"))

    pop_contrib, inc_contrib = pop_growth_recent, e_y_2005 * income_growth_recent
    total_growth = pop_contrib + inc_contrib

    st.markdown("---")
    m1, m2, m3 = st.columns(3)
    m1.metric(f"Pop. Growth ({pop_year})", f"{pop_growth_recent:+.2f}%")
    m2.metric(f"GDP/Cap Growth ({income_year})", f"{income_growth_recent:+.2f}%")
    m3.metric("Income Elasticity of Food Demand", f"{e_y_2005:.3f}")

    st.markdown("---")
    st.metric(label=f"Projected Annual Food Demand Growth for {selected_country_2005}", value=f"{total_growth:+.2f}%")

# ==========================================
# TAB 2: ENGEL'S LAW (9 BROAD EXPENDITURE TYPES)
# ==========================================
with tab2:
    st.header("Income Elasticity across 9 Consumption Good Types (Engel's Law)")
    countries_tab2 = sorted(df_broad_goods["country"].unique())
    default_tab2_idx = countries_tab2.index("United States") if "United States" in countries_tab2 else 0

    selected_country_tab2 = st.selectbox("Select Country / Region:", countries_tab2, index=default_tab2_idx, key="country_tab2_broad")

    country_broad_df = df_broad_goods[df_broad_goods["country"] == selected_country_tab2].copy()
    country_broad_df["doubled_expenditure"] = country_broad_df["base_budget_share"] * (1.0 + country_broad_df["income_elasticity"])
    country_broad_df["doubled_budget_share"] = (country_broad_df["doubled_expenditure"] / country_broad_df["doubled_expenditure"].sum()) * 100.0

    def classify_good(e): return "Inferior Good" if e < 0 else ("Luxury Good" if e > 1 else "Normal Good")
    country_broad_df["good_classification"] = country_broad_df["income_elasticity"].apply(classify_good)

    food_row = country_broad_df[country_broad_df["good_type"] == "Food"].iloc[0]
    
    st.markdown("---")
    m_col1, m_col2, m_col3 = st.columns(3)
    m_col1.metric("Food Income Elasticity", f"{food_row['income_elasticity']:.3f}")
    m_col2.metric("Current Food Budget Share", f"{food_row['base_budget_share']:.1f}%")
    m_col3.metric("Food Share if Income Doubles (+100%)", f"{food_row['doubled_budget_share']:.1f}%", delta=f"-{food_row['base_budget_share'] - food_row['doubled_budget_share']:.1f}% points")

# ==========================================
# TAB 3: BENNETT'S LAW: FOOD SUBGROUPS
# ==========================================
with tab3:
    st.header("Commodity-Specific Demand Growth (Bennett's Law)")
    countries_ifpri = sorted(df_ifpri["country"].unique())
    default_tab3_index = countries_ifpri.index("United States") if "United States" in countries_ifpri else 0

    ctrl_col1, ctrl_col2, ctrl_col3 = st.columns(3)
    with ctrl_col1:
        selected_country_ifpri = st.selectbox("Select Country / Region:", countries_ifpri, index=default_tab3_index, key="country_ifpri")

    wb_match = df_2005[df_2005["country"] == selected_country_ifpri]
    group_pop_growth = float(wb_match.iloc[0]["pop_growth"]) if not wb_match.empty else 1.20
    wb_income_growth = float(wb_match.iloc[0]["income_growth"]) if not wb_match.empty else 2.50

    with ctrl_col2:
        st.metric("Pop. Growth", f"{group_pop_growth:+.2f}%")
    with ctrl_col3:
        group_income_growth = st.number_input("Annual Income Growth (%)", value=wb_income_growth, step=0.10, format="%.2f", key=f"group_inc_{selected_country_ifpri}")

    country_ifpri_df = df_ifpri[df_ifpri["country"] == selected_country_ifpri].copy()
    country_ifpri_df["food_group_name"] = country_ifpri_df["food_group"].map(FOOD_GROUP_MAP)
    country_ifpri_df["annual_demand_growth"] = group_pop_growth + (country_ifpri_df["income_elasticity"] * group_income_growth)

    st.plotly_chart(build_bennett_trapezoid_figure(country_ifpri_df, selected_country_ifpri), use_container_width=True)

    st.markdown("---")
    st.subheader("Income Elasticities")

    display_df = (
        country_ifpri_df.sort_values("income_elasticity", ascending=False)[["food_group_name", "income_elasticity", "annual_demand_growth"]]
        .rename(columns={"food_group_name": "Food Category", "income_elasticity": "Income Elasticity", "annual_demand_growth": "Total Growth (%)"})
    )

    styled_df = (
        display_df.style.set_properties(**{"text-align": "center"})
        .apply(highlight_food_category, subset=["Food Category"])
        .map(highlight_inferior, subset=["Income Elasticity"])
        .format({"Income Elasticity": "{:.3f}", "Total Growth (%)": "{:+.2f}%"})
    )

    st.dataframe(
        styled_df, hide_index=True, use_container_width=False,
        column_config={
            "Food Category": st.column_config.TextColumn(alignment="center", width=220),
            "Income Elasticity": st.column_config.NumberColumn(alignment="center", width=180),
            "Total Growth (%)": st.column_config.TextColumn(alignment="center", width=140),
        },
    )
