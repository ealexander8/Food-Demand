import streamlit as st
import requests

# --- CONFIGURATION ---
st.set_page_config(page_title="Real-World Country Data", page_icon="🌍")

# Dictionary of countries and their official World Bank ISO-3 codes
COUNTRIES = {
    "United States": "USA",
    "China": "CHN",
    "Brazil": "BRA",
    "India": "IND",
    "Germany": "DEU",
    "Japan": "JPN",
    "Egypt": "EGY",
    "Argentina": "ARG",
    "Nigeria": "NGA",
    "Australia": "AUS"
}

# Placeholder for your specific Income Elasticity data.
# You can update these numbers based on the source you are using!
IEOFD_DATA = {
    "United States": 0.15,
    "China": 0.45,
    "Brazil": 0.35,
    "India": 0.60,
    "Germany": 0.12,
    "Japan": 0.10,
    "Egypt": 0.55,
    "Argentina": 0.30,
    "Nigeria": 0.70,
    "Australia": 0.14
}

# --- WORLD BANK API FUNCTION ---
# We use @st.cache_data so if a student clicks a country twice, it loads instantly
@st.cache_data
def get_world_bank_data(iso_code, indicator):
    # Fetch the latest 5 years of data to guarantee we find the most recent non-blank year
    url = f"https://api.worldbank.org/v2/country/{iso_code}/indicator/{indicator}?format=json&per_page=5"
    try:
        response = requests.get(url)
        data = response.json()
        
        # The API returns a list where the second item contains the actual data
        if len(data) > 1:
            for entry in data[1]:
                if entry['value'] is not None:
                    return entry['value'], entry['date']
    except Exception as e:
        return None, None
    return None, None

# --- STREAMLIT DASHBOARD UI ---
st.title("🌍 Real-World Economic Data")
st.markdown("Select a country to pull the latest demographic and economic data directly from the World Bank.")

# Dropdown for students to pick a country
selected_country = st.selectbox("Choose a Country:", list(COUNTRIES.keys()))

if selected_country:
    iso_code = COUNTRIES[selected_country]
    
    with st.spinner("Fetching live data from the World Bank..."):
        # Indicator: SP.POP.GROW (Population growth annual %)
        pop_growth, pop_year = get_world_bank_data(iso_code, "SP.POP.GROW")
        
        # Indicator: NY.GDP.PCAP.PP.KD.ZG (GDP per capita, PPP annual % growth)
        gdp_growth, gdp_year = get_world_bank_data(iso_code, "NY.GDP.PCAP.PP.KD.ZG")
        
        # Fetch the static IEoFD data from our dictionary above
        ieofd = IEOFD_DATA.get(selected_country, "N/A")
    
    st.markdown(f"### Current Data for {selected_country}")
    st.divider()
    
    # Display the metrics in three neat columns
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Population Growth", f"{pop_growth:.2f}%" if pop_growth else "Data Missing", help=f"Reported in {pop_year}")
        
    with col2:
        st.metric("GDP per Capita Growth (PPP)", f"{gdp_growth:.2f}%" if gdp_growth else "Data Missing", help=f"Reported in {gdp_year}")
        
    with col3:
        st.metric("IEoFD", str(ieofd), help="Income Elasticity of Food Demand")
        
    st.caption("Note: Growth percentages are updated dynamically via the World Bank API. Hover over the metric to see the specific reporting year.")
