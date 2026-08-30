import streamlit as st
import pandas as pd
import requests
import difflib

st.title("🌍 Agricultural Economics: Food Demand Simulator")

# 1. LOAD THE CLEAN DATA FROM YOUR EXCEL FILE
@st.cache_data
def load_elasticity_data():
    # Reads the file we just generated!
    return pd.read_excel("Cleaned_Table1_Food_Elasticity.xlsx")

elasticity_df = load_elasticity_data()

# 2. CREATE THE DROPDOWN MENU
# Sort the countries alphabetically and add a default placeholder
country_list = elasticity_df['Country'].dropna().sort_values().tolist()
selected_country = st.selectbox("Select a Country to Analyze:", ["-- Select a Country --"] + country_list)

# 3. HELPER FUNCTION TO FETCH LIVE WORLD BANK DATA
@st.cache_data
def get_wb_data(country_name, indicator_code):
    # First, get the official list of World Bank country names and ISO codes
    search_url = "https://api.worldbank.org/v2/country?format=json&per_page=300"
    try:
        countries_resp = requests.get(search_url).json()
        wb_countries = {c['name']: c['id'] for c in countries_resp[1]}
        
        # Use Python's built-in auto-corrector to find the closest World Bank name
        matches = difflib.get_close_matches(country_name, wb_countries.keys(), n=1, cutoff=0.6)
        if matches:
            iso_code = wb_countries[matches[0]]
        else:
            return None, None # Country not found in WB database
            
        # Fetch the most recent non-empty data point (mrnev=1) for that specific country
        url = f"https://api.worldbank.org/v2/country/{iso_code}/indicator/{indicator_code}?format=json&mrnev=1"
        response = requests.get(url).json()
        
        if len(response) == 2 and response[1]:
            latest_data = response[1][0]
            return latest_data['value'], latest_data['date']
    except Exception as e:
        return None, None
        
    return None, None

# 4. RUN THE SIMULATION WHEN A COUNTRY IS SELECTED
if selected_country != "-- Select a Country --":
    with st.spinner(f"Fetching live macroeconomic data for {selected_country}..."):
        
        # Get the Income Elasticity from our uploaded Excel file
        country_row = elasticity_df[elasticity_df['Country'] == selected_country]
        income_elasticity = country_row['Income_Elasticity_Food_Demand'].iloc[0]
        
        # Fetch World Bank Indicators
        # SP.POP.GROW = Population growth (annual %)
        pop_growth, pop_year = get_wb_data(selected_country, "SP.POP.GROW")
        
        # NY.GDP.PCAP.KD.ZG = GDP per capita growth (annual %)
        # Note: This is the standard real growth metric the WB provides to track wealth changes
        gdp_growth, gdp_year = get_wb_data(selected_country, "NY.GDP.PCAP.KD.ZG")
        
        if pop_growth is not None and gdp_growth is not None:
            # --- THE CORE CALCULATION ---
            # % Growth in Demand = Pop Growth + (GDP Growth * Income Elasticity)
            food_demand_growth = pop_growth + (gdp_growth * income_elasticity)
            
            # --- DISPLAY THE DASHBOARD ---
            st.markdown(f"### Economic & Agricultural Outlook: **{selected_country}**")
            
            # Display the baseline metrics in three neat columns
            col1, col2, col3 = st.columns(3)
            col1.metric(label=f"Pop. Growth ({pop_year})", value=f"{pop_growth:.2f}%")
            col2.metric(label=f"GDP per Capita Growth ({gdp_year})", value=f"{gdp_growth:.2f}%")
            col3.metric(label="Income Elasticity of Food", value=f"{income_elasticity:.3f}")
            
            st.markdown("---")
            
            # Display the final calculated result
            st.subheader("🌾 Projected % Growth in Total Food Demand:")
            st.metric(label="Calculated Demand Growth", value=f"{food_demand_growth:.2f}%")
            
            # Provide an educational breakdown so students see the math in action
            st.info(f"**How this is calculated for {selected_country}:**\n\n"
                    f"Population Growth (`{pop_growth:.2f}%`) + [ GDP per Capita Growth (`{gdp_growth:.2f}%`) × Income Elasticity (`{income_elasticity:.3f}`) ] "
                    f"= **{food_demand_growth:.2f}%**")
        else:
            st.error(f"Could not fetch complete World Bank data for {selected_country}. The World Bank may be missing recent data for this specific country.")
