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
    page_title="Food Demand Growth Simulator",
    page_icon="🌾",
    layout="wide"
)

# Tab 3: Food Subgroups (Bennett's Law)
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
    1: "#D7CCC8",
    2: "#BCAAA4",
    3: "#8D6E63",
    4: "#64B5F6",
    5: "#C62828",
    6: "#0288D1",
    7: "#FFF176",
    8: "#2E7D32",
    9: "#FBC02D",
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
# 2. DATA LOADERS & LIVE WORLD BANK API
# ==========================================
@st.cache_data(ttl=86400)
def fetch_latest_world_bank_indicators():
    """Fetches Population Growth and GDP per capita Growth from World Bank API."""
    indicators = {
        "SP.POP.GROW": ("pop_growth", "pop_year"),
        "NY.GDP.PCAP.KD.ZG": ("income_growth", "income_year"),
        "NY.GDP.PCAP.CD": ("gdp_per_capita", "gdp_year"),
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
                        df_combined = pd.merge(df_combined, df_ind, on="country", how="outer")
        except Exception:
            pass

    if not df_combined.empty:
        df_combined["country"] = df_combined["country"].astype(str).str.strip().str.title()

    return df_combined


@st.cache_data
def load_usda_elasticities():
    """Loads overall food income elasticities."""
    usda_base = [
        {"country": "United States", "income_elasticity_2005": 0.15},
        {"country": "China", "income_elasticity_2005": 0.42},
        {"country": "India", "income_elasticity_2005": 0.62},
        {"country": "Nigeria", "income_elasticity_2005": 0.67},
        {"country": "United Kingdom", "income_elasticity_2005": 0.10},
        {"country": "Brazil", "income_elasticity_2005": 0.38},
        {"country": "Germany", "income_elasticity_2005": 0.12},
        {"country": "Japan", "income_elasticity_2005": 0.14},
        {"country": "Kenya", "income_elasticity_2005": 0.71},
        {"country": "Mexico", "income_elasticity_2005": 0.45},
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
    """Merges World Bank API indicator data with income elasticities."""
    df_wb = fetch_latest_world_bank_indicators()
    df_usda = load_usda_elasticities()

    if not df_wb.empty:
        merged = pd.merge(df_usda, df_wb, on="country", how="left")
        merged["pop_growth"] = merged["pop_growth"].fillna(1.20)
        merged["income_growth"] = merged["income_growth"].fillna(2.50)
        merged["gdp_per_capita"] = merged["gdp_per_capita"].fillna(12000)
        merged["pop_year"] = merged["pop_year"].fillna("Recent")
        merged["income_year"] = merged["income_year"].fillna("Recent")
        return merged

    df_usda["pop_growth"] = 1.20
    df_usda["income_growth"] = 2.50
    df_usda["gdp_per_capita"] = 12000
    df_usda["pop_year"] = "N/A"
    df_usda["income_year"] = "N/A"
    return df_usda


@st.cache_data
def load_table1_broad_categories(df_merged):
    """Loads 9 broad expenditure categories per country based on Engel's Law principles."""
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
    """Loads IFPRI food subgroup elasticity data."""
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
        df_ifpri_raw = pd.read_excel("IFPRI.xlsx")

        df_ifpri_raw.columns = [str(c).strip().lower() for c in df_ifpri_raw.columns]

        if "estimate_2021" in df_ifpri_raw.columns:
            df_ifpri_raw = df_ifpri_raw.rename(columns={"estimate_2021": "income_elasticity"})

        if "specification" in df_ifpri_raw.columns:
            df_ifpri_raw = df_ifpri_raw[df_ifpri_raw["specification"] == 6]

        if "region" in df_ifpri_raw.columns:
            df_ifpri_raw.loc[df_ifpri_raw["region"] == 0, "country"] = "World Average"

        if all(col in df_ifpri_raw.columns for col in ["country", "food_group", "income_elasticity"]):
            df_ifpri_raw["country"] = df_ifpri_raw["country"].astype(str).str.strip().str.title()
            df_ifpri_raw["food_group"] = pd.to_numeric(df_ifpri_raw["food_group"], errors="coerce")
            df_ifpri_raw["income_elasticity"] = pd.to_numeric(df_ifpri_raw["income_elasticity"], errors="coerce")

            merged = pd.merge(
                df_fallback,
                df_ifpri_raw.dropna(subset=["country", "food_group", "income_elasticity"]),
                on=["country", "food_group"],
                how="outer",
                suffixes=("_fallback", "_real")
            )
            merged["income_elasticity"] = merged["income_elasticity_real"].fillna(merged["income_elasticity_fallback"])
            return merged[["country", "food_group", "income_elasticity"]].dropna()
    except Exception:
        pass

    return df_fallback


# ==========================================
# 3. TRAPEZOID DIAGRAM & STYLING HELPER FUNCTIONS
# ==========================================
def build_bennett_trapezoid_figure(country_df, country_name):
    """Builds a Bennett's Law stacked trapezoid diagram."""
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


def highlight_inferior(val):
    if isinstance(val, (int, float)) and val < 0:
        return "color: #D32F2F; font-weight: bold; background-color: #FFEBEE;"
    return ""


def highlight_food_category(col):
    styles = []
    for val in col:
        bg_color = FOOD_NAME_COLOR_MAP.get(val, "#FFFFFF")
        text_color = "#FFFFFF" if bg_color in ["#2E7D32", "#C62828", "#0288D1"] else "#000000"
        styles.append(f"background-color: {bg_color}; color: {text_color}; text-align: center !important;")
    return styles


# ==========================================
# 4. MAIN APP INITIALIZATION & NAVIGATION
# ==========================================
df_merged = load_merged_data()
df_broad = load_table1_broad_categories(df_merged)
df_ifpri = load_ifpri_data(df_merged)

st.title("🌾 Food Demand & Consumer Expenditure Growth Simulator")
st.markdown("An interactive analytical platform modeling food growth trajectories using World Bank indicator data, Engel's Law, and Bennett's Law.")

tab1, tab2, tab3 = st.tabs([
    "📈 Tab 1: Aggregate Food Demand Growth",
    "📊 Tab 2: Engel's Law (9 Expenditure Types)",
    "🥗 Tab 3: Bennett's Law (9 Food Subgroups)"
])


# ==========================================
# TAB 1: AGGREGATE FOOD DEMAND GROWTH
# ==========================================
with tab1:
    st.header("Aggregate Food Demand Growth Model")
    st.markdown(
        "Food demand growth is driven by **population growth** and **income growth** scaled by the **income elasticity of food demand** ($d = p + e \\cdot y$)."
    )

    col1, col2 = st.columns([1, 2])

    country_list = sorted(df_merged["country"].unique())
    
    with col1:
        st.subheader("Scenario Parameters")
        selected_country = st.selectbox("Select Primary Country", country_list, index=country_list.index("United States") if "United States" in country_list else 0, key="t1_country")
        
        c_data = df_merged[df_merged["country"] == selected_country].iloc[0]
        
        st.caption(f"World Bank Live Data ({c_data['pop_year']}):")
        pop_g = st.slider("Population Growth Rate (%/yr)", -2.0, 5.0, float(c_data["pop_growth"]), 0.1, key="t1_pop")
        inc_g = st.slider("GDP per Capita Growth Rate (%/yr)", -2.0, 8.0, float(c_data["income_growth"]), 0.1, key="t1_inc")
        e_y = st.slider("Income Elasticity of Demand (e)", 0.0, 1.0, float(c_data["income_elasticity_2005"]), 0.01, key="t1_ey")
        years = st.slider("Projection Horizon (Years)", 5, 30, 10, key="t1_horizon")

        # Annual and Cumulative Calculations
        annual_demand_growth = pop_g + (e_y * inc_g)
        cum_demand_growth = ((1 + annual_demand_growth / 100) ** years - 1) * 100
        cum_pop_growth = ((1 + pop_g / 100) ** years - 1) * 100

    with col2:
        st.subheader(f"Demand Growth Breakdown: {selected_country}")
        
        m1, m2, m3 = st.columns(3)
        m1.metric("Annual Demand Growth", f"{annual_demand_growth:.2f}%")
        m2.metric(f"Cumulative ({years} yrs)", f"{cum_demand_growth:.1f}%")
        m3.metric("Pop Contribution", f"{(pop_g / max(annual_demand_growth, 0.001))*100:.1f}%")

        # Growth Decomposition Chart
        decomp_df = pd.DataFrame({
            "Component": ["Population Growth", "Income-Driven Growth", "Total Demand Growth"],
            "Annual Rate (%)": [pop_g, e_y * inc_g, annual_demand_growth]
        })
        fig_decomp = px.bar(
            decomp_df, x="Component", y="Annual Rate (%)", color="Component",
            title=f"Annual Growth Drivers for {selected_country}", text_auto=".2f",
            color_discrete_sequence=["#1976D2", "#388E3C", "#F57C00"]
        )
        fig_decomp.update_layout(showlegend=False, height=350)
        st.plotly_chart(fig_decomp, use_container_width=True)

    st.markdown("---")
    st.subheader("Multi-Country Horizon Trajectory & Global Overview")
    
    col_c1, col_c2 = st.columns([1, 1])
    
    with col_c1:
        selected_countries = st.multiselect("Compare Projection Trajectories", country_list, default=[selected_country, "China", "India"] if "China" in country_list and "India" in country_list else [selected_country])
        
        proj_records = []
        for yr in range(0, years + 1):
            for c_name in selected_countries:
                row_c = df_merged[df_merged["country"] == c_name].iloc[0]
                d_rate = row_c["pop_growth"] + (row_c["income_elasticity_2005"] * row_c["income_growth"])
                idx_val = 100 * ((1 + d_rate / 100) ** yr)
                proj_records.append({"Year": yr, "Country": c_name, "Demand Index (Base=100)": round(idx_val, 2)})
        
        df_proj = pd.DataFrame(proj_records)
        fig_proj = px.line(
            df_proj, x="Year", y="Demand Index (Base=100)", color="Country",
            title=f"Food Demand Index Trajectory Over {years} Years", markers=True
        )
        fig_proj.update_layout(height=400)
        st.plotly_chart(fig_proj, use_container_width=True)

    with col_c2:
        df_merged["Annual Food Growth (%)"] = df_merged["pop_growth"] + (df_merged["income_elasticity_2005"] * df_merged["income_growth"])
        fig_map = px.choropleth(
            df_merged, locations="country", locationmode="country names",
            color="Annual Food Growth (%)", hover_name="country",
            title="Global Annual Food Demand Growth Rate (%)",
            color_continuous_scale="YlGnBu"
        )
        fig_map.update_layout(height=400, margin=dict(l=0, r=0, t=40, b=0))
        st.plotly_chart(fig_map, use_container_width=True)


# ==========================================
# TAB 2: ENGEL'S LAW (9 BROAD EXPENDITURE TYPES)
# ==========================================
with tab2:
    st.header("Engel's Law: 9 Broad Expenditure Categories")
    st.markdown(
        "**Engel's Law** states that as income increases, the proportion of income spent on food decreases, even if total food expenditure rises."
    )

    col1, col2 = st.columns([1, 2])

    with col1:
        st.subheader("Income Simulation")
        selected_country_t2 = st.selectbox("Select Country", country_list, index=country_list.index("United States") if "United States" in country_list else 0, key="t2_country")
        
        inc_increase = st.slider("Simulated Per Capita Income Increase (%)", 0, 300, 100, 10, key="t2_inc_slider")
        
        country_broad_df = df_broad[df_broad["country"] == selected_country_t2].copy()
        
        # Recalculate simulated shares based on elasticities
        country_broad_df["raw_sim_share"] = country_broad_df["base_budget_share"] * (1 + country_broad_df["income_elasticity"] * (inc_increase / 100.0))
        total_raw = country_broad_df["raw_sim_share"].sum()
        country_broad_df["simulated_budget_share"] = (country_broad_df["raw_sim_share"] / total_raw) * 100
        country_broad_df["share_change"] = country_broad_df["simulated_budget_share"] - country_broad_df["base_budget_share"]

    with col2:
        st.subheader(f"Budget Share Shift for {selected_country_t2} (+{inc_increase}% Income)")
        
        melted_df = country_broad_df.melt(
            id_vars=["good_type"], value_vars=["base_budget_share", "simulated_budget_share"],
            var_name="Scenario", value_name="Budget Share (%)"
        )
        melted_df["Scenario"] = melted_df["Scenario"].map({"base_budget_share": "Baseline Share", "simulated_budget_share": "Simulated Share"})

        fig_broad = px.bar(
            melted_df, x="good_type", y="Budget Share (%)", color="Scenario", barmode="group",
            color_discrete_sequence=["#1976D2", "#388E3C"], text_auto=".1f"
        )
        fig_broad.update_layout(xaxis_title="", height=400, legend=dict(orientation="h", y=1.1))
        st.plotly_chart(fig_broad, use_container_width=True)

    st.markdown("---")
    st.subheader("Cross-Country Engel Curve Scatter Plot")
    
    # Scatter Plot showing Engel's Law across countries
    df_merged["Base Food Share (%)"] = df_merged["income_elasticity_2005"].apply(lambda e: max(10.0, min(58.0, e * 65.0)))
    
    fig_engel_scatter = px.scatter(
        df_merged, x="gdp_per_capita", y="Base Food Share (%)", text="country", size="pop_growth",
        color="income_elasticity_2005", color_continuous_scale="Viridis",
        log_x=True, title="Food Budget Share vs. GDP Per Capita (Engel Curve Pattern)",
        labels={"gdp_per_capita": "GDP Per Capita (USD, Log Scale)", "income_elasticity_2005": "Food Elasticity (e)"}
    )
    fig_engel_scatter.update_traces(textposition="top center")
    fig_engel_scatter.update_layout(height=450)
    st.plotly_chart(fig_engel_scatter, use_container_width=True)


# ==========================================
# TAB 3: BENNETT'S LAW (9 FOOD SUBGROUPS)
# ==========================================
with tab3:
    st.header("Bennett's Law: 9 Food Subgroups & Dietary Transition")
    st.markdown(
        "**Bennett's Law** states that as incomes rise, consumers shift away from starchy staples (grains/tubers) toward high-value foods (meats, dairy, fruits, vegetables)."
    )

    t3_country = st.selectbox("Select Country for Dietary Analysis", country_list, index=country_list.index("United States") if "United States" in country_list else 0, key="t3_country")

    c_ifpri_df = df_ifpri[df_ifpri["country"] == t3_country].copy()
    if c_ifpri_df.empty:
        c_ifpri_df = df_ifpri[df_ifpri["country"] == "World Average"].copy()
        st.warning(f"Using World Average data for {t3_country}.")

    c_ifpri_df["Food Category"] = c_ifpri_df["food_group"].map(FOOD_GROUP_MAP)

    col_b1, col_b2 = st.columns([1.2, 1])

    with col_b1:
        st.subheader("Bennett's Law Dietary Transition Diagram")
        fig_trap = build_bennett_trapezoid_figure(c_ifpri_df, t3_country)
        st.plotly_chart(fig_trap, use_container_width=True)

    with col_b2:
        st.subheader("Subgroup Elasticity Spectrum")
        c_ifpri_df_sorted = c_ifpri_df.sort_values(by="income_elasticity", ascending=True)
        
        fig_sub_bar = px.bar(
            c_ifpri_df_sorted, y="Food Category", x="income_elasticity", orientation="h",
            color="Food Category", color_discrete_map=FOOD_NAME_COLOR_MAP,
            text_auto=".2f", title=f"Food Subgroup Income Elasticities ({t3_country})"
        )
        fig_sub_bar.add_vline(x=0.0, line_dash="solid", line_color="red", annotation_text="Inferior (e < 0)")
        fig_sub_bar.add_vline(x=1.0, line_dash="dash", line_color="gray", annotation_text="Luxury Threshold (e = 1)")
        fig_sub_bar.update_layout(showlegend=False, height=480, xaxis_title="Income Elasticity (e)")
        st.plotly_chart(fig_sub_bar, use_container_width=True)

    st.subheader("Detailed Subgroup Elasticity Table")
    
    display_df = c_ifpri_df[["food_group", "Food Category", "income_elasticity"]].rename(
        columns={"food_group": "Group ID", "income_elasticity": "Income Elasticity (e)"}
    ).sort_values(by="Group ID")

    styled_df = display_df.style.apply(highlight_food_category, subset=["Food Category"])\
                               .applymap(highlight_inferior, subset=["Income Elasticity (e)"])\
                               .format({"Income Elasticity (e)": "{:.2f}"})

    st.dataframe(styled_df, use_container_width=True, hide_index=True)
