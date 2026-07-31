import streamlit as st
import pandas as pd
import plotly.express as px
from streamlit_autorefresh import st_autorefresh

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="Live Sheet Dashboard", layout="wide")
st.title("📊 Live Interactive Dashboard")
st.markdown("This dashboard pulls live data from your Google Sheet and plots parameters dynamically.")

# --- STEP 0: AUTOMATIC REFRESH (EVERY 30 SECONDS - BACKGROUND) ---
# Running quietly without displaying the raw count value
st_autorefresh(interval=30000, limit=None, key="sheet_autorefresh")

# --- STEP 1: CONVERT GOOGLE SHEET LINK TO CSV EXPORT LINK ---
def convert_to_csv_url(url):
    if "/edit" in url:
        return url.split("/edit")[0] + "/export?format=csv"
    return url

# --- STEP 2: PASTE YOUR GOOGLE SHEET LINK HERE ---
SHEET_1_URL = "https://docs.google.com/spreadsheets/d/1-J20gbbFJ0QOjMNxE1XMp3m3CKV4AZjlAWvypwq5X00/edit?usp=sharing"

# --- STEP 3: LOAD AND CLEAN LIVE DATA ---
@st.cache_data(ttl=0)
def load_live_data(url1):
    csv_url1 = convert_to_csv_url(url1)
    df1 = pd.read_csv(csv_url1)
    
    # 1. Clean extra spaces from column headers
    df1.columns = df1.columns.str.strip()
    
    # 2. Convert all metric columns to numbers (handling commas/symbols)
    for col in df1.columns:
        try:
            cleaned_col = df1[col].astype(str).str.replace(r'[\$,]', '', regex=True)
            df1[col] = pd.to_numeric(cleaned_col)
        except Exception:
            pass # Keep string/date columns as text
            
    return df1

try:
    combined_df = load_live_data(SHEET_1_URL)
    
    # Display preview expander
    with st.expander("👀 View Raw Data Preview"):
        st.dataframe(combined_df.head())

    # --- STEP 4: DASHBOARD CONTROLS ---
    st.sidebar.header("🛠️ Dashboard Controls")
    
    # Clean static auto-refresh message without displaying count
    st.sidebar.info("🔄 Auto-refreshes every 30 seconds")
    
    index_key = st.sidebar.selectbox("Select baseline column (X-Axis):", combined_df.columns)
    
    # Sort dataframe by the selected x-axis to keep line plots smooth
    combined_df = combined_df.sort_values(by=index_key)

    # ─────────────────────────────────────────────────────────────────
    # 🧪 CUSTOM CALCULATIONS ZONE
    # ─────────────────────────────────────────────────────────────────
    if 'Channel_A' in combined_df.columns and 'Channel_B' in combined_df.columns:
        combined_df['Avg_Channel_A_and_B'] = combined_df[['Channel_A', 'Channel_B']].mean(axis=1)
        
    if 'Facebook' in combined_df.columns and 'Instagram' in combined_df.columns:
        combined_df['Total_Social_Traffic'] = combined_df['Facebook'] + combined_df['Instagram']
        
    if 'Sales' in combined_df.columns and 'Ad_Spend' in combined_df.columns:
        combined_df['ROI_Ratio'] = combined_df['Sales'] / combined_df['Ad_Spend']
    # ─────────────────────────────────────────────────────────────────

    # --- STEP 5: URL PARAMETERS & PERSISTENT DEFAULTS ---
    available_metrics = [col for col in combined_df.columns if col != index_key]
    
    # Read choices passed through shared link (URL query parameters)
    query_params = st.query_params
    
    default_kpis = query_params.get("kpis", "").split(",") if query_params.get("kpis") else [available_metrics[0]] if available_metrics else []
    default_metrics = query_params.get("metrics", "").split(",") if query_params.get("metrics") else [available_metrics[0]] if available_metrics else []

    # Clean default filters against available columns
    valid_default_kpis = [m for m in default_kpis if m in available_metrics]
    valid_default_metrics = [m for m in default_metrics if m in available_metrics]

    # --- SIDEBAR CONTROL SELECTIONS ---
    selected_kpis = st.sidebar.multiselect(
        "📌 Select KPI Scorecards (Top Cards):",
        options=available_metrics,
        default=valid_default_kpis if valid_default_kpis else ([available_metrics[0]] if available_metrics else None)
    )

    selected_metrics = st.sidebar.multiselect(
        "📈 Select Graph Parameters:",
        options=available_metrics,
        default=valid_default_metrics if valid_default_metrics else ([available_metrics[0]] if available_metrics else None)
    )
    
    chart_type = st.sidebar.radio("Select Chart Style:", ["Line Chart", "Bar Chart"])

    # Update URL query parameters so copying/sharing the link retains current selections
    st.query_params["kpis"] = ",".join(selected_kpis)
    st.query_params["metrics"] = ",".join(selected_metrics)

    # --- STEP 6: RENDER KPI SCORECARDS ---
    if selected_kpis:
        st.subheader("📌 Key Performance Indicators (KPIs)")
        kpi_cols = st.columns(len(selected_kpis))
        
        for idx, kpi in enumerate(selected_kpis):
            latest_val = combined_df[kpi].iloc[-1] if not combined_df[kpi].empty else 0
            avg_val = combined_df[kpi].mean()
            
            # Format numbers cleanly
            val_str = f"{latest_val:,.2f}" if isinstance(latest_val, (int, float)) else str(latest_val)
            avg_str = f"Avg: {avg_val:,.2f}" if isinstance(avg_val, (int, float)) else ""
            
            with kpi_cols[idx]:
                st.metric(label=kpi, value=val_str, delta=avg_str)
        st.markdown("---")

    # --- STEP 7: RENDER THE GRAPH ---
    if selected_metrics:
        st.subheader(f"📈 Analysis (Plotting against {index_key})")
        
        if chart_type == "Line Chart":
            fig = px.line(combined_df, x=index_key, y=selected_metrics, markers=True,
                          title=f"Trends over {index_key}")
        else:
            fig = px.bar(combined_df, x=index_key, y=selected_metrics, barmode="group",
                         title=f"Comparison over {index_key}")
            
        fig.update_layout(
            hovermode="x unified",
            margin=dict(l=20, r=20, t=50, b=20),
            legend=dict(
                title_text="",
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1,
                bgcolor="rgba(15, 23, 42, 0.85)",
                font=dict(color="white"),
                bordercolor="rgba(255, 255, 255, 0.2)",
                borderwidth=1
            )
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
    else:
        st.warning("⚠️ Please select at least one parameter from the sidebar controls to display the chart.")

except Exception as e:
    st.error(f"❌ Failed to load live data. Error details: {e}")
