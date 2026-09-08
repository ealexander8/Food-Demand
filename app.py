import streamlit as st
import pandas as pd
import plotly.express as px

# --- Page Configuration ---
st.set_page_config(page_title="Expenditure Elasticities App", layout="wide")

# --- 1. Data Loading Functions ---

@st.cache_data
def load_usda_data():
    """
    Loads the USDA data from 2005.
    (Assumes the file is named 'Table1(2).xlsx' or 'Table1(2).xls')
    """
    try:
        # Update the exact file extension if yours is .xls or .csv
        df = pd.read_excel("Table1(2).xlsx")
    except FileNotFoundError:
        try:
            df = pd.read_excel("Table1(2).xls")
        except Exception as e:
            st.error(f"Could not load USDA data: {e}")
            df = pd.DataFrame()
    return df

@st.cache_data
def load_ifpri_data():
    """
    Loads the IFPRI data from the newly uploaded Excel file.
    """
    try:
        df = pd.read_excel("Predicted_Expenditure_Elasticities.xlsx")
    except Exception as e:
        st.error(f"Could not load IFPRI data: {e}")
        df = pd.DataFrame()
    return df

# --- 2. Load the Datasets ---
usda_df = load_usda_data()
ifpri_df = load_ifpri_data()

# --- 3. App Title & Layout ---
st.title("Expenditure and Elasticities Dashboard")

# Create the 3 tabs exactly as requested
tab1, tab2, tab3 = st.tabs([
    "Tab 1: USDA Data (2005)", 
    "Tab 2: USDA Deep Dive", 
    "Tab 3: IFPRI Predicted Elasticities"
])

# --- TAB 1: USDA Data ---
with tab1:
    st.header("USDA Data (2005)")
    st.write("This tab relies exclusively on the USDA data from Table1(2).")
    
    if not usda_df.empty:
        st.dataframe(usda_df, use_container_width=True)
        # Add your Tab 1 USDA visualzations here
    else:
        st.warning("USDA data not found. Please ensure 'Table1(2).xlsx' is in the directory.")

# --- TAB 2: USDA Deep Dive ---
with tab2:
    st.header("USDA Data Analysis")
    st.write("Further analysis and visualizations for the 2005 USDA data.")
    
    if not usda_df.empty:
        st.dataframe(usda_df.head(15), use_container_width=True)
        # Add your Tab 2 USDA visualzations here
    else:
        st.warning("USDA data not found. Please ensure 'Table1(2).xlsx' is in the directory.")

# --- TAB 3: IFPRI Data ---
with tab3:
    st.header("IFPRI Predicted Expenditure Elasticities")
    st.write("This tab relies exclusively on `Predicted_Expenditure_Elasticities.xlsx`.")
    
    if not ifpri_df.empty:
        # Display the data table
        st.dataframe(ifpri_df, use_container_width=True)
        
        st.subheader("Interactive IFPRI Visualization")
        
        # A dynamic Plotly chart placeholder so the app won't crash 
        # while waiting for your exact column names
        if len(ifpri_df.columns) >= 2:
            col1, col2 = st.columns(2)
            with col1:
                x_axis = st.selectbox("Select X-axis:", ifpri_df.columns, index=0)
            with col2:
                y_axis = st.selectbox("Select Y-axis:", ifpri_df.columns, index=min(1, len(ifpri_df.columns)-1))
            
            fig = px.scatter(
                ifpri_df, 
                x=x_axis, 
                y=y_axis, 
                title=f"IFPRI: {y_axis} vs {x_axis}",
                template="plotly_white"
            )
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("IFPRI data not found. Please ensure 'Predicted_Expenditure_Elasticities.xlsx' is in the directory.")
