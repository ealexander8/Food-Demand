import streamlit as st
import pandas as pd
import requests
import difflib
import matplotlib.pyplot as plt

st.title("🌾 Food Demand Growth Simulator")

# 1. LOAD ELASTICITY DATA
@st.cache_data
def load_elasticity_data():
    return pd.read_excel("Cleaned_Table1_Food_Elasticity.xlsx")

elasticity_df = load_elasticity_data()
country_list = elasticity_df['Country'].dropna().tolist()

# 2. TYPE-IN SEARCH WITH BEST MATCH
st.subheader("1. Find a Country")
user_input = st.text_input("Type a country name (e.g., 'Congo', 'USA', 'Viet Nam'):")

selected_country = None

if user_input.strip():
    matches = difflib.get_close_matches(user_input, country_list, n=1, cutoff=0.2)
    if matches:
        selected_country = matches[0]
        st.success(f"Best Match Found: **{selected_country}**")
    else:
        st.error("No close country match found. Please try a different spelling.")
else:
    selected_country = st.selectbox("Or choose from dropdown:", ["-- Select Country --"] + sorted(country_list))
    if selected_country == "-- Select Country --":
        selected_country = None

# 3. HELPER FUNCTION TO FETCH WORLD BANK DATA
@st.cache_data
def get_wb_data(country_name, indicator_code):
    search_url = "https://api.worldbank.org/v2/country?format=json&per_page=300"
    try:
        countries_resp = requests.get(search_url).json()
        wb_countries = {c['name']: c['id'] for c in countries_resp[1]}
        
        matches = difflib.get_close_matches(country_name, wb_countries.keys(), n=1, cutoff=0.5)
        if matches:
            iso_code = wb_countries[matches[0]]
        else:
            return None, None
            
        url = f"https://api.worldbank.org/v2/country/{iso_code}/indicator/{indicator_code}?format=json&mrnev=1"
        response = requests.get(url).json()
        
        if len(response) == 2 and response[1]:
            latest_data = response[1][0]
            return latest_data['value'], latest_data['date']
    except Exception:
        return None, None
        
    return None, None

# 4. CALCULATIONS AND DISPLAY
if selected_country:
    with st.spinner(f"Fetching macroeconomic data for {selected_country}..."):
        country_row = elasticity_df[elasticity_df['Country'] == selected_country]
        income_elasticity = float(country_row['Income_Elasticity_Food_Demand'].iloc[0])
        
        pop_growth, pop_year = get_wb_data(selected_country, "SP.POP.GROW")
        gdp_growth, gdp_year = get_wb_data(selected_country, "NY.GDP.PCAP.KD.ZG")
        
        if pop_growth is not None and gdp_growth is not None:
            pop_contrib = pop_growth
            income_contrib = gdp_growth * income_elasticity
            total_food_demand_growth = pop_contrib + income_contrib
            
            st.markdown(f"### Economic & Agricultural Outlook: **{selected_country}**")
            
            # Display core summary metrics
            col1, col2, col3, col4 = st.columns(4)
            col1.metric(f"Pop. Growth ({pop_year})", f"{pop_growth:.2f}%")
            col2.metric(f"GDP/Capita Growth ({gdp_year})", f"{gdp_growth:.2f}%")
            col3.metric("Inc. Elast. of Food Demand", f"{income_elasticity:.3f}")
            col4.metric("% Change in Food Demand", f"{total_food_demand_growth:.2f}%")
            
            st.markdown("---")
            
            # FORMULA & PLUGGED-IN VARIABLE BREAKDOWN
            st.subheader("📐 Formula & Calculation")
            
            # Multi-line LaTeX formula left-aligned across both lines
            st.latex(r"""
            \begin{aligned}
            &\text{\% Change in Food Demand} = \\
            &\text{Pop Growth (\%)} + \left(\text{GDP/Capita Growth (\%)} \times \text{Income Elasticity}\right)
            \end{aligned}
            """)
            
            # Vertically formatted calculation steps to ensure clean fit on all screen sizes
            st.info(
                f"**Calculation for {selected_country}:**\n\n"
                f"• **Step 1 (Plug in values):** `{pop_growth:.2f}% + ({gdp_growth:.2f}% × {income_elasticity:.3f})`\n\n"
                f"• **Step 2 (Multiply income terms):** `{pop_growth:.2f}% + {income_contrib:.2f}%`\n\n"
                f"• **Final Result:** **`{total_food_demand_growth:.2f}%`**"
            )
            
            # 5. PIE CHART VISUALIZATION
            st.subheader("📊 Drivers of Food Demand Growth")
            
            if pop_contrib > 0 or income_contrib > 0:
                slices = [max(0, pop_contrib), max(0, income_contrib)]
                labels = [
                    "Population Growth", 
                    "Income Growth Effect"
                ]
                
                fig, ax = plt.subplots(figsize=(6, 4))
                ax.pie(
                    slices, 
                    labels=labels, 
                    autopct='%1.1f%%', 
                    startangle=140, 
                    colors=['#3498db', '#2ecc71']
                )
                ax.axis('equal')
                st.pyplot(fig)
            else:
                st.warning("Both population and income growth rates are zero or negative, so a positive pie chart breakdown cannot be generated.")
        else:
            st.error("Could not fetch complete World Bank data for this country.")
