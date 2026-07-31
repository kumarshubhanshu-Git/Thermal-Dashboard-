import streamlit as st
import pandas as pd
import plotly.express as px

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="Live Sheet Dashboard", layout="wide")
st.title("📊 Live Testing Dashboard")
st.markdown("This dashboard pulls live data from your Google Sheet and plots parameters dynamically.")

# --- STEP 1: CONVERT GOOGLE SHEET LINK TO CSV EXPORT LINK ---
def convert_to_csv_url(url):
    if "/edit" in url:
        return url.split("/edit")[0] + "/export?format=csv"
    return url

# --- STEP 2: PASTE YOUR GOOGLE SHEET LINK HERE ---
# Make sure "Anyone with the link can view" is enabled in Google Sheets!
SHEET_1_URL = "https://docs.google.com/spreadsheets/d/1-J20gbbFJ0QOjMNxE1XMp3m3CKV4AZjlAWvypwq5X00/edit?usp=sharing"

# --- STEP 3: LOAD THE LIVE DATA ---
# Cache data for 10 seconds to keep performance snappy while ensuring it stays live
@st.cache_data(ttl=10)
def load_live_data(url1):
    csv_url1 = convert_to_csv_url(url1)
    df1 = pd.read_csv(csv_url1)
    return df1

try:
    combined_df = load_live_data(SHEET_1_URL)
    
    # Display preview expander so you can verify the data columns
    with st.expander("👀 View Raw Data Preview"):
        st.dataframe(combined_df.head())

    # --- STEP 4: DASHBOARD CONTROLS ---
    st.sidebar.header("🛠️ Dashboard Controls")
    
    # Select the primary x-axis column (e.g., 'Date' or 'Timestamp')
    index_key = st.sidebar.selectbox("Select the baseline column (X-Axis):", combined_df.columns)
    
    # ─────────────────────────────────────────────────────────────────
    # 🧪 CUSTOM CALCULATIONS ZONE
    # Add, change, or remove formulas below to match your sheet columns.
    # ─────────────────────────────────────────────────────────────────
    
    # Example A: Average of specific channels (Change column names to match yours)
    if 'Channel_A' in combined_df.columns and 'Channel_B' in combined_df.columns:
        combined_df['Avg_Channel_A_and_B'] = combined_df[['Channel_A', 'Channel_B']].mean(axis=1)
        
    # Example B: Total sum of channels (Change column names to match yours)
    if 'Facebook' in combined_df.columns and 'Instagram' in combined_df.columns:
        combined_df['Total_Social_Traffic'] = combined_df['Facebook'] + combined_df['Instagram']
        
    # Example C: Calculating a performance ratio (Change column names to match yours)
    if 'Sales' in combined_df.columns and 'Ad_Spend' in combined_df.columns:
        combined_df['ROI_Ratio'] = combined_df['Sales'] / combined_df['Ad_Spend']
        
    # ─────────────────────────────────────────────────────────────────

    # --- STEP 5: PARAMETER SELECTION ---
    # Get all column options available for plotting, excluding the chosen X-axis baseline
    available_metrics = [col for col in combined_df.columns if col != index_key]
    
    selected_metrics = st.sidebar.multiselect(
        "Select parameters to display on the graph:",
        options=available_metrics,
        default=[available_metrics[0]] if available_metrics else None
    )
    
    # Choose chart style preferences
    chart_type = st.sidebar.radio("Select Chart Style:", ["Line Chart", "Bar Chart"])

    # --- STEP 6: RENDER THE GRAPH ---
    if selected_metrics:
        st.subheader(f"📈 Analysis (Plotting against {index_key})")
        
        # Generate interactive Plotly figures dynamically based on sidebar choices
        if chart_type == "Line Chart":
            fig = px.line(combined_df, x=index_key, y=selected_metrics, markers=True,
                          title=f"Trends over {index_key}")
        else:
            fig = px.bar(combined_df, x=index_key, y=selected_metrics, barmode="group",
                         title=f"Comparison over {index_key}")
            
        # Update aesthetic layouts for a modern dashboard presentation
        fig.update_layout(
            hovermode="x unified",
            legend_title_text="Parameters",
            margin=dict(l=20, r=20, t=40, b=20)
        )
        
        # Show interactive plot
        st.plotly_chart(fig, use_container_width=True)
        
    else:
        st.warning("⚠️ Please select at least one parameter from the sidebar controls to display the chart.")

except Exception as e:
    st.error(f"❌ Failed to load live data. Please check your URLs and permissions. Error details: {e}")
