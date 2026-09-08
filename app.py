import pandas as pd
import plotly.express as px
import streamlit as st

# ==========================================
# 1. PAGE CONFIGURATION
# ==========================================
st.set_page_config(
    page_title="Food Demand Growth Simulator", page_icon="🌾", layout="wide"
)

# IFPRI FDME 9-category food group mapping
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
# 2. DATA LOADERS (WITH MOCK FALLBACKS)
# ==========================================
@st.cache_data
def load_2005_aggregate_data():
    """Loads original 2005 cross-country aggregate income elasticity dataset."""
    try:
        return pd.read_csv("Cleaned_Table1_Food_Elasticity.csv")
    except FileNotFoundError:
        sample_2005 = [
            {"country": "Kenya", "income_elasticity_2005": 0.65},
            {"country": "Brazil", "income_elasticity_2005": 0.35},
            {"country": "United States", "income_elasticity_2005": 0.15},
        ]
        return pd.DataFrame(sample_2005)


@st.cache_data
def load_aggregate_pie_data():
    """Loads baseline expenditure breakdown for pie chart display."""
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
    """Loads IFPRI Predicted Elasticities dataset (Food Groups 1-9)."""
    try:
        return pd.read_csv("Predicted_Elasticities.csv")
    except FileNotFoundError:
        sample_ifpri = [
            # Kenya
            {"country": "Kenya", "food_group": 1, "income_elasticity": 0.45},
            {"country": "Kenya", "food_group": 2, "income_elasticity": 0.35},
            {"country": "Kenya", "food_group": 3, "income_elasticity": 0.50},
            {"country": "Kenya", "food_group": 4, "income_elasticity": 0.60},
            {"country": "Kenya", "food_group": 5, "income_elasticity": 0.75},
            {"country": "Kenya", "food_group": 6, "income_elasticity": 0.85},
            {"country": "Kenya", "food_group": 7, "income_elasticity": 0.80},
            {"country": "Kenya", "food_group": 8, "income_elasticity": 0.78},
            {"country": "Kenya", "food_group": 9, "income_elasticity": 0.55},
            # Brazil
            {"country": "Brazil", "food_group": 1, "income_elasticity": 0.15},
            {"country": "Brazil", "food_group": 2, "income_elasticity": 0.10},
            {"country": "Brazil", "food_group": 3, "income_elasticity": 0.25},
            {"country": "Brazil", "food_group": 4, "income_elasticity": 0.40},
            {"country": "Brazil", "food_group": 5, "income_elasticity": 0.50},
            {"country": "Brazil", "food_group": 6, "income_elasticity": 0.55},
            {"country": "Brazil", "food_group": 7, "income_elasticity": 0.50},
            {"country": "Brazil", "food_group": 8, "income_elasticity": 0.45},
            {"country": "Brazil", "food_group": 9, "income_elasticity": 0.30},
            # United States
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
# 3. APP HEADER & TAB NAVIGATION
# ==========================================
st.title("🌾 Food Demand Growth Simulator")
st.markdown(
    "Explore how population dynamics and economic growth shape global aggregate food demand and structural dietary transitions."
)

tab1, tab2 = st.tabs(
    ["Overview (2005 Aggregate Data)", "Deep Dive: 9 Food Groups (Bennett's Law)"]
)


# ==========================================
# TAB 1: ORIGINAL AGGREGATE MODEL (2005 DATA)
# ==========================================
with tab1:
    st.header("Aggregate Food Demand Growth (2005 Baseline)")
    st.write(
        "Calculate total national food demand growth using aggregate cross-country income elasticities."
    )

    col1, col2 = st.columns([1, 1])

    with col1:
        countries_2005 = sorted(df_2005["country"].unique())
        selected_country_2005 = st.selectbox(
            "Select Country:", countries_2005, index=0, key="country_2005"
        )

        pop_growth_2005 = st.number_input(
            "Population Growth Rate (%)",
            value=1.50,
            step=0.10,
            format="%.2f",
            key="pop_2005",
        )

        income_growth_2005 = st.number_input(
            "Income / GDP per Capita Growth Rate (%)",
            value=3.00,
            step=0.10,
            format="%.2f",
            key="inc_2005",
        )

        # Retrieve 2005 aggregate income elasticity
        country_row = df_2005[df_2005["country"] == selected_country_2005].iloc[
            0
        ]
        e_y_2005 = country_row["income_elasticity_2005"]

        # Calculation: %Δ Demand = %Δ Pop + (e_y * %Δ Income)
        pop_contrib_2005 = pop_growth_2005
        inc_contrib_2005 = e_y_2005 * income_growth_2005
        total_growth_2005 = pop_contrib_2005 + inc_contrib_2005

        st.markdown("---")
        st.markdown(f"**2005 Food Income Elasticity ($e_y$):** `{e_y_2005:.2f}`")

        st.metric(
            label=f"Projected Annual Demand Growth for {selected_country_2005}",
            value=f"{total_growth_2005:.2f}%",
        )

        st.caption(
            f"Driven by: **{pop_contrib_2005:.2f}%** population growth + **{inc_contrib_2005:.2f}%** income growth effect."
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
# TAB 2: NEW 9 FOOD GROUPS (BENNETT'S LAW)
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

    # Filter IFPRI dataset for selected country
    country_ifpri_df = df_ifpri[
        df_ifpri["country"] == selected_country_ifpri
    ].copy()
    country_ifpri_df["food_group_name"] = country_ifpri_df["food_group"].map(
        FOOD_GROUP_MAP
    )

    # Calculate growth rate per category
    country_ifpri_df["annual_demand_growth"] = group_pop_growth + (
        country_ifpri_df["income_elasticity"] * group_income_growth
    )

    # Sort for plot
    country_ifpri_df = country_ifpri_df.sort_values(
        by="annual_demand_growth", ascending=True
    )

    # Plotly Horizontal Bar Chart
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

    # Context and Data Tables
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
