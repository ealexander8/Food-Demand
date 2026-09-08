import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import streamlit as st

# ==========================================
# 1. PAGE CONFIGURATION & GLOBAL MAPS
# ==========================================
st.set_page_config(
    page_title="Food Demand Growth Simulator", page_icon="🌾", layout="wide"
)

# --- MAPS FOR TAB 2 (FOOD SUBGROUPS) ---
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

# Distinct category colors for food subgroups
COLOR_MAP_SUBGROUP = {
    1: "#D7CCC8",  # Cereals & Staples
    2: "#BCAAA4",  # Roots
    3: "#8D6E63",  # Plant Proteins
    4: "#2E7D32",  # Vegetables
    5: "#81C784",  # Fruits
    6: "#C62828",  # Meat & Poultry
    7: "#0288D1",  # Fish
    8: "#7B1FA2",  # Milk & Dairy
    9: "#FBC02D",  # Sugar, Oils
}

NAME_COLOR_MAP_SUBGROUP = {
    FOOD_GROUP_MAP[k]: COLOR_MAP_SUBGROUP[k] for k in FOOD_GROUP_MAP
}

# --- MAPS FOR TAB 1 (BROAD GOODS) ---
# Map Excel names to code-friendly format
BROAD_GOODS_EXCEL_TO_CODE = {
    "food_beverages_tobacco": "e_food",
    "clothing_footwear": "e_clothing",
    "housing": "e_housing",
    "house_furnishing": "e_house_furn",
    "medical_health": "e_medical",
    "transport_communication": "e_transport",
    "recreation": "e_recreation",
    "education": "e_education",
    "other": "e_other",
}

# Map Code names to display friendly format
BROAD_GOODS_CODE_TO_FRIENDLY = {
    "e_food": "Food, Beverages & Tobacco",
    "e_clothing": "Clothing & Footwear",
    "e_housing": "Housing",
    "e_house_furn": "House Furnishing",
    "e_medical": "Medical & Health",
    "e_transport": "Transport & Communication",
    "e_recreation": "Recreation",
    "e_education": "Education",
    "e_other": "Other Expenditure",
}

# Distinct category colors for Engel's Law Stacked Area Chart (Tab 1)
BROAD_GOOD_COLOR_MAP = {
    "Food, Beverages & Tobacco": "#D7CCC8",
    "Clothing & Footwear": "#E040FB",  # purple
    "Housing": "#FFA726",  # orange
    "House Furnishing": "#FFEE58",  # yellow
    "Medical & Health": "#03A9F4",  # cyan
    "Transport & Communication": "#26A69A",  # teal
    "Recreation": "#43A047",  # green
    "Education": "#7E57C2",  # deep purple
    "Other Expenditure": "#78909C",  # blue-grey
}


# ==========================================
# 2. LIVE WORLD BANK API & DATA LOADERS
# ==========================================
@st.cache_data(ttl=86400)
def fetch_latest_world_bank_indicators():
    """Fetches most recent annual Population Growth (SP.POP.GROW) and
    Per Capita GDP Growth (NY.GDP.PCAP.KD.ZG) from World Bank API using mrnev=1.
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

    # Standardize names immediately on return
    if not df_combined.empty:
        df_combined["country"] = (
            df_combined["country"].astype(str).str.strip().str.title()
        )

    return df_combined


@st.cache_data
def load_full_elasticity_dataset():
    """Loads all broad income elasticities from the expanded Excel file,
    standardizing names so Afghanistan always appears.
    """
    try:
        # Assumes Cleaned_Table1_Full_Elasticity.xlsx exists in same folder
        df = pd.read_excel("Cleaned_Table1_Full_Elasticity.xlsx")

        # Standardize country names to guarantee dropdown matching
        df["country"] = df["country"].astype(str).str.strip().str.title()

        # Simplified rename format for internal coding use
        excel_rename_cols = {
            "food_beverages_tobacco": "e_food",
            "clothing_footwear": "e_clothing",
            "housing": "e_housing",
            "house_furnishing": "e_house_furn",
            "medical_health": "e_medical",
            "transport_communication": "e_transport",
            "recreation": "e_recreation",
            "education": "e_education",
            "other": "e_other",
        }
        df_cleaned = df.rename(columns=excel_rename_cols)

        columns_to_keep = ["country"] + list(excel_rename_cols.values())
        return df_cleaned[columns_to_keep].dropna()

    except FileNotFoundError:
        st.error(
            "Error: Cleaned_Table1_Full_Elasticity.xlsx not found. Please run the cleaning script first."
        )
        return pd.DataFrame()


@st.cache_data
def load_merged_data():
    """Merges all USDA broad elasticities with latest World Bank API indicators,
    supplying defaults to preserve Afghanistan.
    """
    df_wb = fetch_latest_world_bank_indicators()
    df_usda = load_full_elasticity_dataset()

    if not df_usda.empty and not df_wb.empty:
        # Use how="left" to keep all USDA countries (including Afghanistan) even if missing from World Bank API
        merged = pd.merge(df_usda, df_wb, on="country", how="left")

        # Fill in missing WB data with safe defaults for simulation
        merged["pop_growth"] = merged["pop_growth"].fillna(1.20)
        merged["income_growth"] = merged["income_growth"].fillna(2.50)
        merged["pop_year"] = merged["pop_year"].fillna("Default/Fallback")
        merged["income_year"] = merged["income_year"].fillna("Default/Fallback")
        return merged

    return pd.DataFrame()


@st.cache_data
def load_ifpri_data(df_merged):
    """Generates food subgroup income elasticities for ALL countries using Bennett's multipliers."""
    # Subgroup elasticities are relative to the *overall* food demand elasticity (e_food)
    group_multipliers = {
        1: 0.50,  # Cereals & Staples
        2: 0.40,  # Roots & Tubers
        3: 0.70,  # Pulses & Legumes
        4: 0.95,  # Vegetables
        5: 1.15,  # Fruits
        6: 1.30,  # Meat & Poultry
        7: 1.20,  # Fish & Seafood
        8: 1.10,  # Milk & Dairy
        9: 0.80,  # Fats, Oils & Sugars
    }

    records = []
    for _, row in df_merged.iterrows():
        country = row["country"]
        # Must subset explicitly for e_food from the multi-good dataset
        base_food_e = float(row.get("e_food", 0.45))
        for fg_id, mult in group_multipliers.items():
            sub_e = round(max(0.01, base_food_e * mult), 2)
            records.append(
                {
                    "country": country,
                    "food_group": fg_id,
                    "income_elasticity": sub_e,
                }
            )

    return pd.DataFrame(records)


def build_bennett_trapezoid_figure(country_df, country_name):
    """Builds stacked trapezoid diagram depicting changing food demand shares for subgroups as living standards rise."""
    y_levels = np.linspace(0, 100, 50)

    # Standard volume shares at current income (bottom)
    baseline_shares = {
        1: 35.0,  # Cereals & Staples
        2: 12.0,  # Roots & Tubers
        3: 10.0,  # Plant Proteins / Pulses
        4: 8.0,  # Vegetables
        5: 6.0,  # Fruits
        6: 10.0,  # Meat & Poultry
        7: 5.0,  # Fish
        8: 8.0,  # Milk & Dairy
        9: 6.0,  # Fats, Oils & Sugars
    }

    country_df_sorted = country_df.sort_values(
        by="income_elasticity", ascending=False
    ).copy()

    available_groups = country_df_sorted["food_group"].tolist()

    quantities = {}
    for _, row in country_df_sorted.iterrows():
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
        e_val = country_df_sorted.loc[
            country_df_sorted["food_group"] == g, "income_elasticity"
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
                fillcolor=COLOR_MAP_SUBGROUP.get(g, "#9E9E9E"),
                line=dict(color="#1A1A1A", width=1.2),
                name=f"{g_name} (e = {e_val:.2f})",
                hovertemplate=(
                    f"<b>{g_name}</b><br>Elasticity: {e_val:.2f}<br>Income"
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
            title="<b>Living Standards Tier</b>",
            tickmode="array",
            tickvals=[0, 25, 50, 75, 100],
            ticktext=["Baseline", "+25%", "+50%", "+75%", "+100% Increase"],
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
if df_2005.empty:
    st.error("Error merging data. App cannot load.")
    st.stop()

df_ifpri = load_ifpri_data(df_2005)

# ==========================================
# 3. APP HEADER & TAB NAVIGATION
# ==========================================
st.title("🌾 Food Demand Growth Simulator")
st.markdown(
    "Explore how population dynamics and economic growth shape global aggregate food demand and structural dietary transitions across all consumption categories."
)

tab1, tab2 = st.tabs(
    ["Engel's Law: All Goods", "Bennett's Law: Food Subgroups"]
)


# ==========================================
# TAB 1: ALL GOODS (ENGEL'S LAW SIMULATION)
# ==========================================
with tab1:
    st.header("Income Increase and Shifts in Broad Budget Allocation (Engel's Law)")
    st.markdown(
        " Engel's Law states that as income rises, the **proportion** of total income spent on food decreases, even if absolute food spending increases. Choose a country and adjust hypothetical income growth to see this projection across all goods."
    )

    countries_all = sorted(df_2005["country"].unique())
    default_tab1_index = (
        countries_all.index("United States") if "United States" in countries_all else 0
    )

    ctrl_c1, ctrl_c2 = st.columns([0.4, 0.6])

    with ctrl_c1:
        selected_country_all = st.selectbox(
            "Select Country:",
            countries_all,
            index=default_tab1_index,
            key="country_all",
        )

    country_row_all = df_2005[df_2005["country"] == selected_country_all].iloc[0]

    with ctrl_c2:
        max_inc_growth_hyp = st.number_input(
            "Hypothetical Income Level at end of projection (% increase)",
            value=100.0,
            step=10.0,
            format="%.1f",
        )

    # --- SIMULATION & ALLOCATION CHART ---
    st.subheader(f"Projected Budget Share Shift in {selected_country_all}")
    st.markdown(
        f"This simulation assumes that currently, budget shares are **equal** across all 9 goods (~11.1% each) to visualize relative shifts. Total income increases from 0% to **+{max_inc_growth_hyp:.1f}%** along the x-axis."
    )

    # List of Good categories for code use
    code_goods = [
        "e_clothing",
        "e_housing",
        "e_house_furn",
        "e_medical",
        "e_transport",
        "e_recreation",
        "e_education",
        "e_other",
    ]

    # Assume base shares are equal (100% / 9)
    base_shares_all = {
        "e_food": 1 / 9,
        "e_clothing": 1 / 9,
        "e_housing": 1 / 9,
        "e_house_furn": 1 / 9,
        "e_medical": 1 / 9,
        "e_transport": 1 / 9,
        "e_recreation": 1 / 9,
        "e_education": 1 / 9,
        "e_other": 1 / 9,
    }

    income_increase_range = np.linspace(0, max_inc_growth_hyp / 100.0, 11)

    proj_records = []
    for ΔY in income_increase_range:
        for c_good, base_s in base_shares_all.items():
            elasticity = float(country_row_all[c_good])
            # Engel's Law math to preserve budget constraint sum=1
            new_s = base_s * (1.0 + elasticity * ΔY) / (1.0 + ΔY)
            friendly_n = BROAD_GOODS_CODE_TO_FRIENDLY[c_good]
            proj_records.append(
                {
                    "Income Increase (%)": ΔY * 100.0,
                    "Budget Allocation (%)": new_s * 100.0,
                    "Good Category": friendly_n,
                }
            )

    df_proj = pd.DataFrame(proj_records)

    fig_proj = px.area(
        df_proj,
        x="Income Increase (%)",
        y="Budget Allocation (%)",
        color="Good Category",
        color_discrete_map=BROAD_GOOD_COLOR_MAP,
        line_shape="spline",
    )

    # Force x-axis labels to have explicitly clear + signs
    fig_proj.update_layout(
        height=500,
        xaxis=dict(tickformat="+.1f"),
        yaxis=dict(title="Budget Allocation (%)", ticksuffix="%", range=[0, 100]),
        legend=dict(
            orientation="h", yanchor="bottom", y=-0.3, xanchor="center", x=0.5
        ),
        margin=dict(l=20, r=20, t=30, b=80),
    )

    st.plotly_chart(fig_proj, use_container_width=True)


# ==========================================
# TAB 2: BENNETT'S LAW: FOOD SUBGROUPS
# ==========================================
with tab2:
    st.header("Commodity-Specific Demand Growth (Bennett's Law)")
    st.write(
        "Explore how demand shifts across 9 distinct food categories as incomes grow, using Bennett's multipliers relative to overall food demand."
    )

    countries_ifpri = sorted(df_ifpri["country"].unique())
    default_tab2_index = (
        countries_ifpri.index("United States") if "United States" in countries_ifpri else 0
    )

    ctrl_col1, ctrl_col2, ctrl_col3 = st.columns(3)

    with ctrl_col1:
        selected_country_ifpri = st.selectbox(
            "Select Country / Region:",
            countries_ifpri,
            index=default_tab2_index,
            key="country_ifpri",
        )

    # Look up actual World Bank/USDA indicators for selected country
    row_ifpri = df_2005[df_2005["country"] == selected_country_ifpri].iloc[0]
    wb_income_growth_actual = float(row_ifpri["income_growth"])
    wb_pop_growth_actual = float(row_ifpri["pop_growth"])
    group_income_year = str(row_ifpri.get("income_year", "Recent"))

    with ctrl_col2:
        st.metric(
            f"Annual Pop. Growth ({group_income_year})",
            f"{wb_pop_growth_actual:+.2f}%",
            help="Most recent reported world bank rate or safe fallback.",
        )

    with ctrl_col3:
        group_income_growth_sim = st.number_input(
            "Annual Income Growth (%)",
            value=wb_income_growth_actual,
            step=0.10,
            format="%.2f",
            key=f"group_inc_{selected_country_ifpri}",
        )

    country_ifpri_df = df_ifpri[
        df_ifpri["country"] == selected_country_ifpri
    ].copy()
    country_ifpri_df["food_group_name"] = country_ifpri_df["food_group"].map(
        FOOD_GROUP_MAP
    )

    # Final Calculation: Pop Growth + (Subgroup Elasticity * Income Growth)
    country_ifpri_df["annual_demand_growth"] = wb_pop_growth_actual + (
        country_ifpri_df["income_elasticity"] * group_income_growth_sim
    )

    # --- BAR CHART (COLORS MATCHED TO TRAPEZOID) ---
    country_ifpri_df_sorted = country_ifpri_df.sort_values(
        by="annual_demand_growth", ascending=True
    )

    fig_bar = px.bar(
        country_ifpri_df_sorted,
        x="annual_demand_growth",
        y="food_group_name",
        orientation="h",
        text="annual_demand_growth",
        title=f"Projected Annual Demand Growth (%) by Category in {selected_country_ifpri}",
        labels={
            "annual_demand_growth": "Annual Demand Growth (%)",
            "food_group_name": "Food Group",
        },
        color="food_group_name",
        color_discrete_map=NAME_COLOR_MAP_SUBGROUP,
    )

    # Use explicit clear + formatting for the labels next to bars
    fig_bar.update_traces(texttemplate="%{text:+.2f}%", textposition="outside")
    fig_bar.add_vline(x=0, line_dash="dash", line_color="black", opacity=0.7)
    
    fig_bar.update_layout(
        height=500,
        xaxis=dict(
            title="Predicted Annual Demand Growth (%)",
            tickformat="+.2f",
            ticksuffix="%"
        ),
        yaxis_title="",
        showlegend=False,
    )

    st.plotly_chart(fig_bar, use_container_width=True)

    # --- BENNETT'S LAW TRAPEZOID DIAGRAM ---
    st.markdown("---")
    fig_trapezoid = build_bennett_trapezoid_figure(
        country_ifpri_df, selected_country_ifpri
    )
    st.plotly_chart(fig_trapezoid, use_container_width=True)

    # --- INCOME ELASTICITIES TABLE ---
    st.markdown("---")
    st.subheader("Income Elasticities")

    # CSS to force center alignment on all dataframe column headers and data cells
    st.markdown(
        """
        <style>
        [data-testid="stDataFrame"] [role="columnheader"] {
            justify-content: center !important;
            text-align: center !important;
        }
        [data-testid="stDataFrame"] [role="columnheader"] * {
            justify-content: center !important;
            text-align: center !important;
        }
        [data-testid="stDataFrame"] th, [data-testid="stDataFrame"] td {
            text-align: center !important;
        }
        [data-testid="stDataFrame"] th > div, [data-testid="stDataFrame"] td > div {
            justify-content: center !important;
            text-align: center !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    display_df = (
        country_ifpri_df.sort_values("income_elasticity", ascending=False)[
            ["food_group_name", "income_elasticity", "annual_demand_growth"]
        ]
        .rename(
            columns={
                "food_group_name": "Food Category",
                "income_elasticity": "Income Elasticity (Subgroup)",
                "annual_demand_growth": "Total Growth (%)",
            }
        )
    )

    def highlight_food_category(col):
        styles = []
        for val in col:
            bg_color = NAME_COLOR_MAP_SUBGROUP.get(val, "#FFFFFF")
            text_color = (
                "#FFFFFF"
                if bg_color in ["#2E7D32", "#C62828", "#0288D1", "#7B1FA2", "#8D6E63"]
                else "#000000"
            )
            styles.append(
                f"background-color: {bg_color}; color: {text_color}; text-align: center !important;"
            )
        return styles

    # Use explicitly clear + signs for the total growth column in table
    styled_df = (
        display_df.style
        .set_properties(**{"text-align": "center"})
        .set_table_styles([
            {"selector": "th", "props": [("text-align", "center !important"), ("justify-content", "center !important")]},
            {"selector": "td", "props": [("text-align", "center !important"), ("justify-content", "center !important")]}
        ])
        .apply(highlight_food_category, subset=["Food Category"])
        .format(
            {
                "Income Elasticity (Subgroup)": "{:.2f}",
                "Total Growth (%)": "{:+.2f}%", 
            }
        )
    )

    # Render narrow, left-aligned table with centered headers and cells
    st.dataframe(
        styled_df,
        hide_index=True,
        use_container_width=False,
        column_config={
            "Food Category": st.column_config.TextColumn(
                alignment="center", width=220
            ),
            "Income Elasticity (Subgroup)": st.column_config.NumberColumn(
                alignment="center", format="%.2f", width=180
            ),
            "Total Growth (%)": st.column_config.TextColumn(
                alignment="center", width=140
            ),
        },
    )
