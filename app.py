import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import json
from openai import OpenAI

# Initialize OpenAI Client
client = OpenAI(api_key=st.secrets.get("OPENAI_API_KEY", "YOUR_OPENAI_API_KEY"))

st.set_page_config(
    page_title="ExpiryGuard AI | Smart Inventory Middleware",
    page_layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling
st.markdown("""
<style>
    .metric-card {
        background-color: #ffffff;
        padding: 16px;
        border-radius: 10px;
        border-left: 5px solid #3b82f6;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    .red-alert { border-left-color: #ef4444; background-color: #fef2f2; }
    .yellow-alert { border-left-color: #f59e0b; background-color: #fffbeb; }
    .green-alert { border-left-color: #10b981; background-color: #ecfdf5; }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# SIDEBAR CONTROLS
# ---------------------------------------------------------
with st.sidebar:
    st.title("🛡️ ExpiryGuard AI")
    st.caption("Proactive FEFO & Inventory Waste Prevention Middleware")
    
    system_mode = st.radio("Select Integration Mode:", ["🏥 Hospital HMIS (Pharmacy)", "🛒 Shopify / E-Commerce"])
    expiry_threshold = st.slider("Red Alert Expiry Window (Days):", 15, 90, 30)

# ---------------------------------------------------------
# MOCK DATA GENERATOR
# ---------------------------------------------------------
today = datetime.now()

if system_mode == "🏥 Hospital HMIS (Pharmacy)":
    mock_data = [
        {"Item ID": "DRUG-101", "Name": "Injectable Amoxicillin 500mg", "Location": "Main Pharmacy", "Stock Qty": 120, "Daily Use Rate": 2, "Expiry Date": (today + timedelta(days=18)).strftime('%Y-%m-%d'), "Unit Cost ($)": 15.00},
        {"Item ID": "DRUG-102", "Name": "IV Saline Bags 1000mL", "Location": "Ward 3", "Stock Qty": 300, "Daily Use Rate": 25, "Expiry Date": (today + timedelta(days=25)).strftime('%Y-%m-%d'), "Unit Cost ($)": 3.50},
        {"Item ID": "DRUG-103", "Name": "Atorvastatin 20mg", "Location": "Main Pharmacy", "Stock Qty": 500, "Daily Use Rate": 15, "Expiry Date": (today + timedelta(days=120)).strftime('%Y-%m-%d'), "Unit Cost ($)": 0.80},
        {"Item ID": "DRUG-104", "Name": "Specialized Oncology Vial B", "Location": "Outpatient Clinic", "Stock Qty": 15, "Daily Use Rate": 0.1, "Expiry Date": (today + timedelta(days=22)).strftime('%Y-%m-%d'), "Unit Cost ($)": 450.00},
    ]
else:
    mock_data = [
        {"Item ID": "SKU-881", "Name": "Organic Baby Formula Stage 1", "Location": "Warehouse A", "Stock Qty": 85, "Daily Use Rate": 1, "Expiry Date": (today + timedelta(days=20)).strftime('%Y-%m-%d'), "Unit Cost ($)": 28.00},
        {"Item ID": "SKU-882", "Name": "Hydrating Face Serum", "Location": "Warehouse B", "Stock Qty": 200, "Daily Use Rate": 10, "Expiry Date": (today + timedelta(days=45)).strftime('%Y-%m-%d'), "Unit Cost ($)": 18.00},
        {"Item ID": "SKU-883", "Name": "Vitamin C Gummies 60s", "Location": "Storefront 1", "Stock Qty": 150, "Daily Use Rate": 0.5, "Expiry Date": (today + timedelta(days=15)).strftime('%Y-%m-%d'), "Unit Cost ($)": 12.00},
    ]

df = pd.DataFrame(mock_data)
df['Days to Expiry'] = (pd.to_datetime(df['Expiry Date']) - today).dt.days
df['Projected Waste Qty'] = df.apply(lambda row: max(0, row['Stock Qty'] - (row['Daily Use Rate'] * row['Days to Expiry'])), axis=1)
df['At Risk Value ($)'] = df['Projected Waste Qty'] * df['Unit Cost ($)']

# ---------------------------------------------------------
# DASHBOARD METRICS
# ---------------------------------------------------------
st.title(f"📦 Inventory Risk Dashboard — {system_mode}")
st.caption("Analyzing stock velocity against expiration timelines to prevent capital loss.")

col1, col2, col3, col4 = st.columns(4)

total_items = len(df)
critical_items = len(df[df['Days to Expiry'] <= expiry_threshold])
total_risk_val = df['At Risk Value ($)'].sum()

col1.metric("Total Tracked SKUs", total_items)
col2.metric("Critical Expiry SKUs", critical_items, delta_color="inverse")
col3.metric("Projected Financial Loss", f"${total_risk_val:,.2f}")
col4.metric("Middleware System Status", "Active Sync ✅")

st.divider()

# ---------------------------------------------------------
# DATA TABLE & SELECTION
# ---------------------------------------------------------
st.subheader("📋 Active Inventory Risk Matrix")

def highlight_risk(val):
    if val <= expiry_threshold:
        return 'background-color: #fef2f2; color: #991b1b; font-weight: bold;'
    elif val <= 60:
        return 'background-color: #fffbeb; color: #92400e;'
    return 'background-color: #ecfdf5; color: #065f46;'

st.dataframe(df.style.map(highlight_risk, subset=['Days to Expiry']), use_container_width=True)

# ---------------------------------------------------------
# AI DECISION ENGINE
# ---------------------------------------------------------
st.divider()
st.subheader("🤖 AI Mitigation Engine")
st.write("Select a high-risk SKU to generate automated mitigation workflows:")

selected_item_id = st.selectbox("Select SKU for Action Plan:", df['Item ID'].tolist() + ["Select..."], index=0)

if selected_item_id and selected_item_id != "Select...":
    item_row = df[df['Item ID'] == selected_item_id].iloc[0]
    
    col_left, col_right = st.columns([1, 1])
    
    with col_left:
        st.markdown(f"""
        <div class='metric-card red-alert'>
            <h4>Item Selected: {item_row['Name']}</h4>
            <p><b>Current Location:</b> {item_row['Location']}</p>
            <p><b>Current Stock:</b> {item_row['Stock Qty']} units</p>
            <p><b>Consumption Velocity:</b> {item_row['Daily Use Rate']} units/day</p>
            <p><b>Days Until Expiry:</b> {item_row['Days to Expiry']} Days</p>
            <p><b>Estimated Financial Loss:</b> <span style='color:red;'>${item_row['At Risk Value ($)']:,.2f}</span></p>
        </div>
        """, unsafe_allow_html=True)
        
        generate_btn = st.button("⚡ Generate Automated Action Plan", type="primary")

    if generate_btn:
        with col_right:
            with st.spinner("Calculating optimal FEFO transfer / markdown strategy..."):
                
                prompt = f"""
                You are an enterprise AI inventory optimization engine for {system_mode}.
                Analyze this high-risk expiring item and generate a concise mitigation action plan:
                - Item: {item_row['Name']}
                - Days to Expiry: {item_row['Days to Expiry']}
                - Stock Qty: {item_row['Stock Qty']}
                - Daily Use Rate: {item_row['Daily Use Rate']}
                - Current Location: {item_row['Location']}
                - Potential Loss: ${item_row['At Risk Value ($)']}

                Return a JSON object with:
                1. "primary_action": A clear header title for the recommended action.
                2. "steps": List of 3 specific operational steps.
                3. "projected_recovery": Percentage of financial loss prevented by taking this action.
                """

                try:
                    response = client.chat.completions.create(
                        model="gpt-4o",
                        messages=[{"role": "user", "content": prompt}],
                        response_format={"type": "json_object"}
                    )
                    
                    action_data = json.loads(response.choices[0].message.content)

                    st.success(f"**Recommended Strategy: {action_data.get('primary_action')}**")
                    st.metric("Projected Value Recovery", f"{action_data.get('projected_recovery', '85%')}")
                    
                    st.markdown("**Action Steps:**")
                    for step in action_data.get("steps", []):
                        st.markdown(f"• {step}")
                        
                    st.button("✅ Execute 1-Click Middleware Action (Sync to System)", key="execute_action")

                except Exception as e:
                    st.error(f"Error generating action plan: {e}")
