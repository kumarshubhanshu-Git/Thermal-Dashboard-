import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from streamlit_autorefresh import st_autorefresh

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="Live Sheet Dashboard", layout="wide")
st.title("📊 Live Interactive Dashboard")
st.markdown("This dashboard pulls live data from your Google Sheet and plots parameters dynamically.")

# --- STEP 0: AUTOMATIC REFRESH (EVERY 30 SECONDS - QUIET BACKGROUND) ---
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
    
    # Clean extra spaces from column headers
    df1.columns = df1.columns.str.strip()
    
    # Convert metric columns to numbers (handling commas/symbols)
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
    st.sidebar.info("🔄 Auto-refreshes every 30 seconds")
    
    index_key = st.sidebar.selectbox("Select baseline column (X-Axis):", combined_df.columns)
    
    # Sort dataframe by selected x-axis to keep line plots smooth
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

    # --- STEP 5: KPIS & DUAL-AXIS SELECTION ---
    available_metrics = [col for col in combined_df.columns if col != index_key]
    
    # Defaults configuration
    MY_DEFAULT_KPIS = ["Channel_A", "Channel_B", "Sales"]       
    MY_DEFAULT_PRIMARY = ["Channel_A"]              
    MY_DEFAULT_SECONDARY = ["Channel_B"]

    valid_kpis = [k for k in MY_DEFAULT_KPIS if k in available_metrics]
    valid_primary = [m for m in MY_DEFAULT_PRIMARY if m in available_metrics]
    valid_secondary = [m for m in MY_DEFAULT_SECONDARY if m in available_metrics]

    if not valid_kpis and available_metrics:
        valid_kpis = available_metrics[:3]
    if not valid_primary and available_metrics:
        valid_primary = [available_metrics[0]]

    # Sidebar controls for KPIs and Axis Mapping
    selected_kpis = st.sidebar.multiselect(
        "📌 Select KPI Scorecards (Top Cards):",
        options=available_metrics,
        default=valid_kpis
    )

    st.sidebar.markdown("---")
    st.sidebar.subheader("📈 Multi-Axis Graph Settings")
    
    primary_metrics = st.sidebar.multiselect(
        "Select Primary Axis Parameters (Left Y-Axis):",
        options=available_metrics,
        default=valid_primary
    )
    
    secondary_metrics = st.sidebar.multiselect(
        "Select Secondary Axis Parameters (Right Y-Axis):",
        options=available_metrics,
        default=valid_secondary
    )
    
    chart_type = st.sidebar.radio("Select Chart Style:", ["Line Chart", "Bar Chart"])

    # --- STEP 6: RENDER KPI SCORECARDS ---
    if selected_kpis:
        st.subheader("📌 Key Performance Indicators (KPIs)")
        kpi_cols = st.columns(len(selected_kpis))
        
        for idx, kpi in enumerate(selected_kpis):
            latest_val = combined_df[kpi].iloc[-1] if not combined_df[kpi].empty else 0
            val_str = f"{latest_val:,.2f}" if isinstance(latest_val, (int, float)) else str(latest_val)
            
            with kpi_cols[idx]:
                with st.container(border=True):
                    st.metric(label=kpi, value=val_str)
        st.markdown("<br>", unsafe_allow_html=True)

    # --- STEP 7: RENDER MULTI-AXIS GRAPH ---
    if primary_metrics or secondary_metrics:
        with st.container(border=True):
            st.subheader(f"📈 Analysis (Plotting against {index_key})")
            
            # Create Subplot with Secondary Y-Axis enabled
            fig = make_subplots(specs=[[{"secondary_y": True}]])
            
            # Add Primary (Left Y-Axis) Traces
            for metric in primary_metrics:
                if chart_type == "Line Chart":
                    fig.add_trace(
                        go.Scatter(x=combined_df[index_key], y=combined_df[metric], name=f"{metric} (Left)", mode='lines+markers'),
                        secondary_y=False
                    )
                else:
                    fig.add_trace(
                        go.Bar(x=combined_df[index_key], y=combined_df[metric], name=f"{metric} (Left)"),
                        secondary_y=False
                    )
                    
            # Add Secondary (Right Y-Axis) Traces
            for metric in secondary_metrics:
                if chart_type == "Line Chart":
                    fig.add_trace(
                        go.Scatter(x=combined_df[index_key], y=combined_df[metric], name=f"{metric} (Right)", mode='lines+markers'),
                        secondary_y=True
                    )
                else:
                    fig.add_trace(
                        go.Bar(x=combined_df[index_key], y=combined_df[metric], name=f"{metric} (Right)"),
                        secondary_y=True
                    )

            # Set Axis Titles
            fig.update_xaxes(title_text=index_key)
            fig.update_yaxes(title_text=", ".join(primary_metrics) if primary_metrics else "Primary Axis", secondary_y=False)
            fig.update_yaxes(title_text=", ".join(secondary_metrics) if secondary_metrics else "Secondary Axis", secondary_y=True)

            # Custom Layout Aesthetics
            fig.update_layout(
                hovermode="x unified",
                margin=dict(l=20, r=20, t=50, b=20),
                barmode="group" if chart_type == "Bar Chart" else None,
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
        st.warning("⚠️ Please select at least one parameter for either the Primary or Secondary axis to display the chart.")

except Exception as e:
    st.error(f"❌ Failed to load live data. Error details: {e}")
