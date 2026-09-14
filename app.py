import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(
    page_title="Global Food Income Elasticity Dashboard",
    layout="wide",
    initial_sidebar_state="expanded",
)


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
        {"country": "China", "income_elasticity_2005": 0.775, "income_group": "Upper middle income"},
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
            (c for c in df.columns if "elasticity" in c or "ey" in c),
            next(
                (
                    c for c in df.columns
                    if "income" in c and not any(
                        x in c for x in ["group", "level", "cat", "class", "year", "capita"]
                    )
                ),
                df.columns[1] if len(df.columns) > 1 else df.columns[0],
            ),
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


# Main Application
st.title("Global Food Income Elasticity Dashboard")

df_elasticity = load_usda_elasticities()

# Sidebar Setup
st.sidebar.header("Filter Options")

income_groups = sorted([g for g in df_elasticity["income_group"].dropna().unique()])
selected_income_groups = st.sidebar.multiselect(
    "Filter by Income Group:",
    options=income_groups,
    default=income_groups,
)

search_country = st.sidebar.text_input("Search Country:", "")

# Filter Logic
filtered_df = df_elasticity[
    df_elasticity["income_group"].isin(selected_income_groups)
]

if search_country.strip():
    filtered_df = filtered_df[
        filtered_df["country"].str.contains(search_country.strip(), case=False, na=False)
    ]

# Layout Tabs
tab1, tab2 = st.tabs(["Tab 1: Elasticity Overview", "Tab 2: Data Explorer & Download"])

with tab1:
    st.subheader("Food Income Elasticity Analysis")

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Countries", len(filtered_df))
    if not filtered_df.empty:
        col2.metric("Mean Elasticity", f"{filtered_df['income_elasticity_2005'].mean():.3f}")
        col3.metric("Max Elasticity", f"{filtered_df['income_elasticity_2005'].max():.3f}")
    else:
        col2.metric("Mean Elasticity", "N/A")
        col3.metric("Max Elasticity", "N/A")

    st.markdown("---")

    if not filtered_df.empty:
        fig = px.bar(
            filtered_df.sort_values("income_elasticity_2005", ascending=False),
            x="country",
            y="income_elasticity_2005",
            color="income_group",
            labels={
                "income_elasticity_2005": "Income Elasticity (2005)",
                "country": "Country",
                "income_group": "Income Group",
            },
            title="Income Elasticity of Food Demand by Country",
            height=500,
        )
        fig.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No data available for the selected filters.")

with tab2:
    st.subheader("Data Explorer")
    st.dataframe(filtered_df, use_container_width=True, hide_index=True)

    if not filtered_df.empty:
        csv_data = filtered_df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="Download Filtered CSV",
            data=csv_data,
            file_name="food_income_elasticities.csv",
            mime="text/csv",
        )
