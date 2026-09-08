import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# ==========================================
# 1. PAGE CONFIGURATION & CONSTANTS
# ==========================================
st.set_page_config(
    page_title="Food Demand Growth Simulator", page_icon="🌾", layout="wide"
)

# Standard IFPRI FDME 9-category food mapping
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
# 2. DATA LOADERS (WITH SAMPLE DATA FALLBACKS)
# ==========================================
@st.cache_data
def load_aggregate_data():
    """Loads baseline aggregate national food data.

    Replace sample dataframe with pd.read_csv('your_aggregate_data.csv') as
    needed.
    """
    try:
        # Example loading logic for real dataset:
        # return pd.read_csv("aggregate_food_data.csv")
        pass
    except FileNotFoundError:
        pass

    # Sample dataset for immediate demonstration
    sample_data = {
        "Category": ["Starchy Staples", "Animal Proteins", "Fruits & Vegetables", "Fats & Sugars", "Other Groceries"],
        "Share_Percent": [40.0, 25.0, 20.0, 10.0, 5.0],
    }
    return pd.DataFrame(sample_data)


@st.cache_data
def load_ifpri_data():
    """Loads IFPRI Predicted Elasticities dataset (Food Groups 1-9).

    Replace sample dataframe with pd.read_csv('Predicted_Elasticities.csv') as
    needed.
    """
    try:
        # Real dataset loading logic:
        # df = pd.read_csv("Predicted_Elasticities.csv")
        # return df
        pass
    except FileNotFoundError:
        pass

    # Representative sample IFPRI elasticities across different country income tiers
    sample_ifpri = [
        # Low-Income Country (e.g., Kenya)
        {"country": "Kenya", "food_group": 1, "income_elasticity": 0.45},
        {"country": "Kenya", "food_group": 2, "income_elasticity": 0.35},
        {"country": "Kenya", "food_group": 3, "income_elasticity": 0.50},
        {"country": "Kenya", "food_group": 4, "income_elasticity": 0.60},
        {"country": "Kenya", "food_group": 5, "income_elasticity": 0.75},
        {"country": "Kenya", "food_group": 6, "income_elasticity": 0.85},
        {"country": "Kenya", "food_group": 7, "income_elasticity": 0.80},
        {"country": "Kenya", "food_group": 8, "income_elasticity": 0.78},
        {"country": "Kenya", "food_group": 9, "income_elasticity": 0.55},
        # Middle-Income Country (e.g., Brazil)
        {"country": "Brazil", "food_group": 1, "income_elasticity": 0.15},
        {"country": "Brazil", "food_group": 2, "income_elasticity": 0.10},
        {"country": "Brazil", "food_group": 3, "income_elasticity": 0.25},
        {"country": "Brazil", "food_group": 4, "income_elasticity": 0.40},
        {"country": "Brazil", "food_group": 5, "income_elasticity": 0.50},
        {"country": "Brazil", "food_group": 6, "income_elasticity": 0.55},
        {"country": "Brazil", "food_group": 7, "income_elasticity": 0.50},
        {"country": "Brazil", "food_group": 8, "income_elasticity": 0.45},
        {"country": "Brazil", "food_group": 9, "income_elasticity": 0.30},
        # High-Income Country (e.g., United States)
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


# Load Data
df_agg = load_aggregate_data()
df_ifpri = load_ifpri_data()

# ==========================================
# 3. HEADER & DASHBOARD NAVIGATION
# ==========================================
st.title("🌾 Food Demand Growth Simulator")
st.markdown(
    "Explore how population dynamics and economic growth shape global agricultural demand and dietary transitions."
)

tab1, tab2 = st.tabs(["Overview (Aggregate Demand)", "Deep Dive: 9 Food Groups (Bennett's Law)"])


# ==========================================
# TAB 1: OVERVIEW & AGGREGATE SCENARIO SIMULATOR
# ==========================================
with tab1:
    st.header("Aggregate Food Demand Baseline")
    st.write(
        "At a macro level, aggregate food demand is driven by the combination of population growth and income expansion."
    )

    # 1. Baseline Pie Chart
    col_left, col_right = st.columns([1, 1])

    with col_left:
        st.subheader("Baseline Food Share Breakdown")
        fig_pie = px.pie(
            df_agg,
            values="Share_Percent",
            names="Category",
            hole=0.4,
            color_discrete_sequence=px.colors.qualitative.Set2,
        )
        fig_pie.update_traces(textinfo="percent+label")
        fig_pie.update_layout(showlegend=False, height=350, margin=dict(l=10, r=10, t=30, b=10))
        st.plotly_chart(fig_pie, use_container_width=True)

    with col_right:
        st.subheader("Key Takeaways")
        st.markdown(
            """
            * **Population Growth** creates a baseline 1-to-1 shift in total food volume required.
            * **Income Growth** expands demand depending on a country's **income elasticity of food** ($e_y$).
            * In lower-income nations, a larger portion of household expenditure is dedicated to basic staples.
            * Use the scenario playground below to calculate total expected growth in national food demand.
            """
        )

    st.markdown("---")

    # 2. Interactive Scenario Playground
    st.subheader("🧮 Scenario Playground: Predict Aggregate Demand Growth")
    st.write(
        "Adjust the sliders below to see how population and income growth interact to drive aggregate food demand."
    )

    scen_col1, scen_col2, scen_col3 = st.columns(3)

    with scen_col1:
        pop_growth = st.number_input(
            "Population Growth (%)",
            value=1.50,
            step=0.10,
            format="%.2f",
            help="Annual percentage rate of population growth.",
        )

    with scen_col2:
        income_growth = st.number_input(
            "Income / GDP per Capita Growth (%)",
            value=3.00,
            step=0.10,
            format="%.2f",
            help="Annual rate of real income per capita growth.",
        )

    with scen_col3:
        income_elasticity = st.number_input(
            "Income Elasticity of Food ($e_y$)",
            value=0.35,
            step=0.05,
            format="%.2f",
            help="Responsiveness of food demand to income changes. (Higher in low-income nations, lower in high-income nations).",
        )

    # Growth Accounting Calculation
    pop_contribution = pop_growth
    income_contribution = income_elasticity * income_growth
    total_demand_growth = pop_contribution + income_contribution

    st.markdown("#### Projected Annual Demand Results")

    res_col1, res_col2, res_col3 = st.columns(3)

    res_col1.metric(
        label="Total Demand Growth",
        value=f"{total_demand_growth:.2f}%",
    )

    pop_pct_share = (pop_contribution / total_demand_growth * 100) if total_demand_growth != 0 else 0
    inc_pct_share = (income_contribution / total_demand_growth * 100) if total_demand_growth != 0 else 0

    res_col2.metric(
        label="Driven by Population",
        value=f"{pop_contribution:.2f}%",
        delta=f"{pop_pct_share:.1f}% of total growth",
        delta_color="off",
    )

    res_col3.metric(
        label="Driven by Income",
        value=f"{income_contribution:.2f}%",
        delta=f"{inc_pct_share:.1f}% of total growth",
        delta_color="off",
    )

    # Math Expander
    with st.expander("Show the Math"):
        st.markdown(
            f"""
            **Agricultural Growth Accounting Formula:**  
            $$\\text{{Total Demand Growth (\\%)}} = \\text{{Population Growth (\\%)}} + (e_y \\times \\text{{Income Growth (\\%)}})$$
            
            $$\\text{{Total Growth}} = {pop_growth:.2f}\\% + ({income_elasticity:.2f} \\times {income_growth:.2f}\\%)$$  
            $$\\text{{Total Growth}} = {pop_growth:.2f}\\% + {income_contribution:.2f}\\% = \\mathbf{{{total_demand_growth:.2f}\\%}}$$
            """
        )


# ==========================================
# TAB 2: DEEP DIVE (9 FOOD GROUPS & BENNETT'S LAW)
# ==========================================
with tab2:
    st.header("Commodity-Specific Demand Growth (Bennett's Law)")
    st.write(
        "Bennett's Law states that as incomes rise, consumers shift away from starchy staples toward higher-value proteins, vegetables, and dairy."
    )

    # 1. User Controls
    ctrl_col1, ctrl_col2, ctrl_col3 = st.columns(3)

    with ctrl_col1:
        countries = sorted(df_ifpri["country"].unique())
        selected_country = st.selectbox(
            "Select Country / Region:", countries, index=0
        )

    with ctrl_col2:
        group_pop_growth = st.number_input(
            "Annual Population Growth (%) ",
            value=1.20,
            step=0.10,
            format="%.2f",
            key="group_pop",
        )

    with ctrl_col3:
        group_income_growth = st.number_input(
            "Annual Income Growth (%) ",
            value=3.50,
            step=0.10,
            format="%.2f",
            key="group_inc",
        )

    # Filter country data
    country_df = df_ifpri[df_ifpri["country"] == selected_country].copy()
    country_df["food_group_name"] = country_df["food_group"].map(FOOD_GROUP_MAP)

    # Calculate growth rate per group: %ΔD = %ΔPop + (e_y * %ΔInc)
    country_df["annual_demand_growth"] = group_pop_growth + (
        country_df["income_elasticity"] * group_income_growth
    )

    # Sort values for visual ranking
    country_df = country_df.sort_values(by="annual_demand_growth", ascending=True)

    # 2. Horizontal Bar Chart
    fig_bar = px.bar(
        country_df,
        x="annual_demand_growth",
        y="food_group_name",
        orientation="h",
        text="annual_demand_growth",
        title=f"Projected Annual Demand Growth (%) by Category in {selected_country}",
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

    # 3. Data Table & Pedagogical Explanation
    col_exp1, col_exp2 = st.columns(2)

    with col_exp1:
        with st.expander("View Data Table"):
            display_df = country_df[
                ["food_group", "food_group_name", "income_elasticity", "annual_demand_growth"]
            ].rename(
                columns={
                    "food_group": "Group Code",
                    "food_group_name": "Category Name",
                    "income_elasticity": "Income Elasticity (e_y)",
                    "annual_demand_growth": "Total Growth (%)",
                }
            )
            st.dataframe(display_df.sort_values("Group Code"), use_container_width=True)

    with col_exp2:
        with st.expander("How to Interpret Bennett's Law in This Chart"):
            st.markdown(
                f"""
                * **Starchy Staples (Group 1):** Typically show lower income elasticities. Growth is heavily anchored to baseline population growth (**{group_pop_growth:.2f}%**).
                * **High-Value Products (Groups 5-8):** Meat, Dairy, and Fruits usually exhibit high income elasticities. Rapid GDP growth (**{group_income_growth:.2f}%**) dramatically accelerates demand for these categories.
                * **Educational Takeaway:** Food security strategies in developing nations must account for shifting structural demand toward animal proteins and fresh produce, not just total cereal calories.
                """
            )
