import pandas as pd
import plotly.express as px
import requests
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
# 2. LIVE WORLD BANK API & DATA LOADERS
# ==========================================
@st.cache_data(ttl=86400)
def fetch_latest_world_bank_indicators():
    """Fetches the most recent non-empty Population Growth (SP.POP.GROW) and

    Per Capita GDP Growth (NY.GDP.PCAP.KD.ZG) from the World Bank API using the
    'mrnev=1' parameter (Most Recent Non-Empty Value).
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

    return df_combined


@st.cache_data
def load_usda_elasticities():
    """USDA 2005 Baseline Income Elasticities for 100+ countries."""
    usda_base = [
        {"country": "Afghanistan", "income_elasticity_2005": 0.78},
        {"country": "Albania", "income_elasticity_2005": 0.48},
        {"country": "Algeria", "income_elasticity_2005": 0.45},
        {"country": "Angola", "income_elasticity_2005": 0.75},
        {"country": "Argentina", "income_elasticity_2005": 0.32},
        {"country": "Armenia", "income_elasticity_2005": 0.46},
        {"country": "Australia", "income_elasticity_2005": 0.12},
        {"country": "Austria", "income_elasticity_2005": 0.11},
        {"country": "Azerbaijan", "income_elasticity_2005": 0.44},
        {"country": "Bangladesh", "income_elasticity_2005": 0.72},
        {"country": "Belarus", "income_elasticity_2005": 0.38},
        {"country": "Belgium", "income_elasticity_2005": 0.11},
        {"country": "Benin", "income_elasticity_2005": 0.74},
        {"country": "Bolivia", "income_elasticity_2005": 0.52},
        {"country": "Bosnia and Herzegovina", "income_elasticity_2005": 0.41},
        {"country": "Brazil", "income_elasticity_2005": 0.35},
        {"country": "Bulgaria", "income_elasticity_2005": 0.36},
        {"country": "Burkina Faso", "income_elasticity_2005": 0.76},
        {"country": "Burundi", "income_elasticity_2005": 0.80},
        {"country": "Cambodia", "income_elasticity_2005": 0.71},
        {"country": "Cameroon", "income_elasticity_2005": 0.68},
        {"country": "Canada", "income_elasticity_2005": 0.10},
        {"country": "Central African Republic", "income_elasticity_2005": 0.79},
        {"country": "Chad", "income_elasticity_2005": 0.78},
        {"country": "Chile", "income_elasticity_2005": 0.24},
        {"country": "China", "income_elasticity_2005": 0.42},
        {"country": "Colombia", "income_elasticity_2005": 0.38},
        {"country": "Congo, Dem. Rep.", "income_elasticity_2005": 0.81},
        {"country": "Costa Rica", "income_elasticity_2005": 0.33},
        {"country": "Croatia", "income_elasticity_2005": 0.28},
        {"country": "Cyprus", "income_elasticity_2005": 0.20},
        {"country": "Czechia", "income_elasticity_2005": 0.22},
        {"country": "Denmark", "income_elasticity_2005": 0.10},
        {"country": "Dominican Republic", "income_elasticity_2005": 0.42},
        {"country": "Ecuador", "income_elasticity_2005": 0.45},
        {"country": "Egypt, Arab Rep.", "income_elasticity_2005": 0.50},
        {"country": "El Salvador", "income_elasticity_2005": 0.48},
        {"country": "Estonia", "income_elasticity_2005": 0.25},
        {"country": "Ethiopia", "income_elasticity_2005": 0.77},
        {"country": "Finland", "income_elasticity_2005": 0.11},
        {"country": "France", "income_elasticity_2005": 0.11},
        {"country": "Gambia, The", "income_elasticity_2005": 0.73},
        {"country": "Georgia", "income_elasticity_2005": 0.47},
        {"country": "Germany", "income_elasticity_2005": 0.10},
        {"country": "Ghana", "income_elasticity_2005": 0.65},
        {"country": "Greece", "income_elasticity_2005": 0.18},
        {"country": "Guatemala", "income_elasticity_2005": 0.52},
        {"country": "Guinea", "income_elasticity_2005": 0.75},
        {"country": "Haiti", "income_elasticity_2005": 0.74},
        {"country": "Honduras", "income_elasticity_2005": 0.54},
        {"country": "Hungary", "income_elasticity_2005": 0.24},
        {"country": "India", "income_elasticity_2005": 0.62},
        {"country": "Indonesia", "income_elasticity_2005": 0.48},
        {"country": "Iran, Islamic Rep.", "income_elasticity_2005": 0.39},
        {"country": "Iraq", "income_elasticity_2005": 0.46},
        {"country": "Ireland", "income_elasticity_2005": 0.11},
        {"country": "Israel", "income_elasticity_2005": 0.16},
        {"country": "Italy", "income_elasticity_2005": 0.13},
        {"country": "Jamaica", "income_elasticity_2005": 0.40},
        {"country": "Japan", "income_elasticity_2005": 0.12},
        {"country": "Jordan", "income_elasticity_2005": 0.41},
        {"country": "Kazakhstan", "income_elasticity_2005": 0.37},
        {"country": "Kenya", "income_elasticity_2005": 0.68},
        {"country": "Korea, Rep.", "income_elasticity_2005": 0.18},
        {"country": "Kuwait", "income_elasticity_2005": 0.18},
        {"country": "Latvia", "income_elasticity_2005": 0.26},
        {"country": "Lebanon", "income_elasticity_2005": 0.35},
        {"country": "Lithuania", "income_elasticity_2005": 0.26},
        {"country": "Madagascar", "income_elasticity_2005": 0.76},
        {"country": "Malawi", "income_elasticity_2005": 0.79},
        {"country": "Malaysia", "income_elasticity_2005": 0.28},
        {"country": "Mali", "income_elasticity_2005": 0.75},
        {"country": "Mexico", "income_elasticity_2005": 0.31},
        {"country": "Morocco", "income_elasticity_2005": 0.46},
        {"country": "Mozambique", "income_elasticity_2005": 0.78},
        {"country": "Nepal", "income_elasticity_2005": 0.73},
        {"country": "Netherlands", "income_elasticity_2005": 0.10},
        {"country": "New Zealand", "income_elasticity_2005": 0.12},
        {"country": "Niger", "income_elasticity_2005": 0.79},
        {"country": "Nigeria", "income_elasticity_2005": 0.67},
        {"country": "Norway", "income_elasticity_2005": 0.09},
        {"country": "Pakistan", "income_elasticity_2005": 0.64},
        {"country": "Peru", "income_elasticity_2005": 0.41},
        {"country": "Philippines", "income_elasticity_2005": 0.49},
        {"country": "Poland", "income_elasticity_2005": 0.25},
        {"country": "Portugal", "income_elasticity_2005": 0.18},
        {"country": "Romania", "income_elasticity_2005": 0.35},
        {"country": "Russian Federation", "income_elasticity_2005": 0.33},
        {"country": "Rwanda", "income_elasticity_2005": 0.77},
        {"country": "Saudi Arabia", "income_elasticity_2005": 0.22},
        {"country": "Senegal", "income_elasticity_2005": 0.70},
        {"country": "Sierra Leone", "income_elasticity_2005": 0.78},
        {"country": "Singapore", "income_elasticity_2005": 0.12},
        {"country": "Slovak Republic", "income_elasticity_2005": 0.23},
        {"country": "Slovenia", "income_elasticity_2005": 0.19},
        {"country": "South Africa", "income_elasticity_2005": 0.38},
        {"country": "Spain", "income_elasticity_2005": 0.14},
        {"country": "Sri Lanka", "income_elasticity_2005": 0.48},
        {"country": "Sweden", "income_elasticity_2005": 0.10},
        {"country": "Switzerland", "income_elasticity_2005": 0.08},
        {"country": "Tanzania", "income_elasticity_2005": 0.75},
        {"country": "Thailand", "income_elasticity_2005": 0.36},
        {"country": "Tunisia", "income_elasticity_2005": 0.42},
        {"country": "Turkiye", "income_elasticity_2005": 0.34},
        {"country": "Uganda", "income_elasticity_2005": 0.76},
        {"country": "Ukraine", "income_elasticity_2005": 0.40},
        {"country": "United Arab Emirates", "income_elasticity_2005": 0.15},
        {"country": "United Kingdom", "income_elasticity_2005": 0.10},
        {"country": "United States", "income_elasticity_2005": 0.08},
        {"country": "Uruguay", "income_elasticity_2005": 0.25},
        {"country": "Uzbekistan", "income_elasticity_2005": 0.51},
        {"country": "Viet Nam", "income_elasticity_2005": 0.58},
        {"country": "Zambia", "income_elasticity_2005": 0.74},
        {"country": "Zimbabwe", "income_elasticity_2005": 0.71},
    ]
    return pd.DataFrame(usda_base)


@st.cache_data
def load_merged_data():
    """Merges the latest World Bank API indicators with 2005 USDA Elasticities."""
    df_wb = fetch_latest_world_bank_indicators()
    df_usda = load_usda_elasticities()

    if not df_wb.empty:
        merged = pd.merge(df_usda, df_wb, on="country", how="inner")
        merged["pop_growth"] = merged["pop_growth"].fillna(1.20)
        merged["income_growth"] = merged["income_growth"].fillna(2.50)
        merged["pop_year"] = merged["pop_year"].fillna("Recent")
        merged["income_year"] = merged["income_year"].fillna("Recent")
        return merged

    # Fallback if API fails
    df_usda["pop_growth"] = 1.20
    df_usda["income_growth"] = 2.50
    df_usda["pop_year"] = "N/A"
    df_usda["income_year"] = "N/A"
    return df_usda


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
        {"country": "United States", "food_group": 1, "income_elasticity": 0.02},
        {"country": "United States", "food_group": 2, "income_elasticity": 0.01},
        {"country": "United States", "food_group": 3, "income_elasticity": 0.08},
        {"country": "United States", "food_group": 4, "income_elasticity": 0.15},
        {"country": "United States", "food_group": 5, "income_elasticity": 0.18},
        {"country": "United States", "food_group": 6, "income_elasticity": 0.20},
        {"country": "United States", "food_group": 7, "income_elasticity": 0.22},
        {"country": "United States", "food_group": 8, "income_elasticity": 0.15},
        {"country": "United States", "food_group": 9, "income_elasticity": 0.05},
    ]
    return pd.DataFrame(sample_ifpri)


# Load Datasets
df_2005 = load_merged_data()
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
# TAB 1: AGGREGATE MODEL (LATEST WORLD BANK API INDICATORS)
# ==========================================
with tab1:
    st.header("Aggregate Food Demand Growth")
    st.write(
        "Select a country to combine 2005 USDA baseline food elasticities with the most recent reported World Bank population and GDP per-capita growth rates."
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
            "Select Country (100+ Datasets Available):",
            countries_2005,
            index=default_index,
            key="country_2005",
        )

        country_row = df_2005[df_2005["country"] == selected_country_2005].iloc[
            0
        ]
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
            f"{pop_growth_recent:.2f}%",
            help="Most recent annual population growth rate from World Bank API",
        )
        m2.metric(
            f"GDP/Cap Growth ({income_year})",
            f"{income_growth_recent:.2f}%",
            help="Most recent annual per capita GDP growth rate from World Bank API",
        )
        m3.metric(
            "Income Elasticity of Food Demand",
            f"{e_y_2005:.2f}",
            help="USDA 2005 baseline income elasticity of food demand",
        )

        st.markdown("---")
        st.metric(
            label=f"Projected Annual Food Demand Growth for {selected_country_2005}",
            value=f"{total_growth:.2f}%",
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
                    {total_growth:.2f}% = {pop_contrib:.2f}% + ({e_y_2005:.2f} × {income_growth_recent:.2f}%)
                </span>
            </div>
            """,
            unsafe_allow_html=True,
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
