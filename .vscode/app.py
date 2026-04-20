import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import plotly.express as px
import numpy as np

# -------------------------
# Load Data
# -------------------------
# Page layout
st.set_page_config(page_title="System Capacity & Care Load Analytics for Unaccompanied Children monitoring Dashboard",
                   layout="wide")

# MAIN DASHBOARD TITLE
st.title("📊 System Capacity & Care Load Analytics for Unaccompanied Children monitoring Dashboard")
df = pd.read_csv(r".vscode/updated HHS_Unaccompanied_Alien_Children_Program.csv")
df.columns = df.columns.str.strip()

st.markdown(" ")

df['Date'] = pd.to_datetime(df['Date'])
df = df.sort_values('Date')
df.columns = df.columns.str.strip()

# -----------------------------
# KPI Calculations
# -------------------------# -----------------------------
# ENSURE NUMERIC SAFETY
# -----------------------------
num_cols = [
    "Children in CBP custody",
    "Children in HHS Care",
    "Children transferred out of CBP custody",
    "Children discharged from HHS Care"
]

for col in num_cols:
    if col in df.columns:
        df[col] = pd.to_numeric(df[col], errors="coerce")

df = df.fillna(0)

# -----------------------------
# DERIVED METRICS 
# -----------------------------
df["Total_System_Load"] = (
    df["Children in CBP custody"] +
    df["Children in HHS Care"]
)
df["Total_Children_Under_Care"] = (
    df["Children in CBP custody"] +
    df["Children in HHS Care"]
)
# -----------------------------
# 1. TOTAL CHILDREN UNDER CARE
# -----------------------------
total_children_under_care = float(df["Total_Children_Under_Care"].iloc[-1])

# -----------------------------
# 2. NET INTAKE PRESSURE
# -----------------------------
net_intake_pressure = (
    (df["Children transferred out of CBP custody"] -
     df["Children discharged from HHS Care"]) /
    df["Children in HHS Care"]
).iloc[-1]

# -----------------------------
# 3. CARE LOAD VOLATILITY INDEX
# -----------------------------
care_load_volatility = float(df["Children in HHS Care"].std())

# -----------------------------
# 4. BACKLOG ACCUMULATION RATE
# -----------------------------
backlog_accumulation_rate = (
    (df["Children in CBP custody"] -
     df["Children transferred out of CBP custody"]) /
    df["Children in CBP custody"]
).iloc[-1]

# -----------------------------
# 5. DISCHARGE OFFSET RATIO
# -----------------------------
discharge_offset_ratio = (
    df["Children discharged from HHS Care"] /
    df["Children transferred out of CBP custody"]
).iloc[-1]

# -----------------------------
# STREAMLIT KPI DISPLAY
# -----------------------------
k1, k2, k3, k4, k5 = st.columns(5)

k1.metric("Total Children", f"{total_children_under_care:,.0f}")
k2.metric("Net Intake", f"{net_intake_pressure:.2f}")
k3.metric("Volatility Rate", f"{care_load_volatility:.2f}")
k4.metric("Backlog Rate", f"{backlog_accumulation_rate:.2%}")
k5.metric("Discharge Ratio", f"{discharge_offset_ratio:.2%}")

st.divider()
#------------------------------
# Sidebar Filters
# -------------------------
st.sidebar.title("Filters")

# Date Range Selector
start_date = st.sidebar.date_input(
    "Start Date",
    df['Date'].min()
)

end_date = st.sidebar.date_input(
    "End Date",
    df['Date'].max()
)

#--------------------------------------
#Time Granularity Selector
#--------------------------------------
st.sidebar.subheader("Time Granularity")

granularity = st.sidebar.selectbox(
    "Select Time Level",
    ["Daily", "Weekly", "Monthly"]
)

# Filter data
filtered_df = df[(df['Date'] >= pd.to_datetime(start_date)) & 
                 (df['Date'] <= pd.to_datetime(end_date))]

# =========================
# RESAMPLING FUNCTION
# =========================
filtered_df = filtered_df.set_index("Date")

if granularity == "Weekly":
    filtered_df = filtered_df.resample("W").mean()
elif granularity == "Monthly":
    filtered_df = filtered_df.resample("ME").mean()
else:
    filtered_df = filtered_df.resample("D").mean()

filtered_df = filtered_df.reset_index()

# Recreate derived metrics AFTER resampling
filtered_df["Net_Intake"] = (
    filtered_df["Children transferred out of CBP custody"] -
    filtered_df["Children discharged from HHS Care"]
)

filtered_df["Backlog"] = (
    filtered_df["Children in CBP custody"] -
    filtered_df["Children in HHS Care"]
)

# -------------------------
# metric Toggle
# -------------------------
st.sidebar.subheader("metric selection")

# Metric toggle
metric = st.sidebar.selectbox(
    "Select Metric",
    ["System Load", "CBP Custody", "HHS Care", "Net Intake", "Backlog"]
)

metric_map = {
    "System Load": "Total_System_Load",
    "CBP Custody": "Children in CBP custody",
    "HHS Care": "Children in HHS Care",
    "Net Intake": "Net_Intake",
    "Backlog": "Backlog"
}

selected_col = metric_map[metric]
# -------------------------
# System Load Overview Pane
# -------------------------
with st.container(border=True):

    st.subheader("System Load Overview")

    fig1 = px.line(
            filtered_df,
            x="Date",
            y=selected_col,
            title=f"{metric} Trend Over Time"
        )
    
    fig1.update_traces(line_color="purple")
    fig1.update_layout(template="plotly_white")

    st.plotly_chart(fig1, width="stretch")
    st.info("Insight: The total system load shows how overall responsibility for unaccompanied children changes over time. Rising trends indicate increasing system pressure.")
    # Data used for chart
system_load_data = filtered_df[["Date", selected_col]]

# Download button
st.download_button(
    label="📥 Download System Load Data (CSV)",
    data=system_load_data.to_csv(index=False),
    file_name="system_load_data.csv",
    mime="text/csv"
)

# -------------------------
# CBP vs HHS COMPARISON
# =========================
colA,colB = st.columns(2)
with colA:
    with st.container(border=True):

        st.subheader("⚖️ CBP vs HHS Load Comparison")

        fig2 = px.line(
            filtered_df,
            x="Date",
            y=["Children in CBP custody", "Children in HHS Care"],
            title=f"CBP vs HHS Trends ({granularity})",
            color_discrete_sequence=["blue", "orange"]
        )
        fig2.update_layout(template="plotly_white")

        st.plotly_chart(fig2, width="stretch")
        st.info("Insight: This chart compares children in CBP custody with those in HHS care, helping understand how responsibilities are distributed between agencies.")
    cbp_hhs_data = filtered_df[
    ["Date", "Children in CBP custody", "Children in HHS Care"]
]

    st.download_button(
    label="📥 Download CBP vs HHS Data (CSV)",
    data=cbp_hhs_data.to_csv(index=False),
    file_name="cbp_hhs_comparison.csv",
    mime="text/csv"
)

st.divider()
# =========================
# NET INTAKE & BACKLOG
# =========================

with colB:
    with st.container(border=True):

         st.subheader("📉 Net Intake & Backlog Trends")

         fig3 = px.line(
        filtered_df,
        x="Date",
        y=["Net_Intake", "Backlog"],
        title=f"Net Intake & Backlog ({granularity})",
        color_discrete_sequence=["purple", "red"]
        )

         fig3.update_layout(template="plotly_white")
         fig3.add_hline(y=0, line_dash="dash", line_color="gray")
         st.plotly_chart(fig3, width="stretch")
         st.info("Net Intake: Net intake reflects the difference between arrivals and releases. Positive values indicate increasing system load.")
         st.info("Backlog Trend: Increasing backlog values indicate periods where system demand exceeds processing capacity, highlighting potential operational pressure."
)
    flow_data = filtered_df[["Date", "Net_Intake", "Backlog"]]

    st.download_button(
    label="📥 Download Net Intake & Backlog Data (CSV)",
    data=flow_data.to_csv(index=False),
    file_name="flow_pressure_metrics.csv",
    mime="text/csv"
    )
    st.divider()
    
st.success("""
**Key Insights**

• The total system load reflects overall system responsibility across CBP and HHS.  
• CBP and HHS trends show how custody and care responsibilities shift over time.  
• Net intake spikes indicate periods of higher arrivals.  
• Backlog indicators highlight potential capacity constraints.
""")

