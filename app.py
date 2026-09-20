import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import time

st.set_page_config(page_title="Allergen Safety", layout="wide")

# ============================================================================
# THINGSPEAK CONFIGURATION
# ============================================================================


# ============================================================================
# FETCH DATA FROM THINGSPEAK
# ============================================================================

def get_latest_data():
    """Get latest sensor reading"""
    url = f"https://api.thingspeak.com/channels/{CHANNEL_ID}/feeds.json"
    params = {
        "api_key": READ_API_KEY,
        "results": 1
    }
    
    try:
        response = requests.get(url, params=params)
        if response.status_code == 200:
            data = response.json()
            if data['feeds']:
                feed = data['feeds'][0]
                return {
                    'allergen': float(feed.get('field1', 0)),
                    'temperature': float(feed.get('field2', 0)),
                    'risk_score': float(feed.get('field3', 0)),
                    'is_safe': int(feed.get('field4', 1)),
                    'timestamp': feed.get('created_at', '')
                }
    except Exception as e:
        st.error(f"Error fetching data: {e}")
    
    return None

def get_historical_data(results=100):
    """Get historical data"""
    url = f"https://api.thingspeak.com/channels/{CHANNEL_ID}/feeds.json"
    params = {
        "api_key": READ_API_KEY,
        "results": results
    }
    
    try:
        response = requests.get(url, params=params)
        if response.status_code == 200:
            data = response.json()
            feeds = data['feeds']
            
            df_data = {
                'timestamp': [],
                'allergen': [],
                'temperature': [],
                'risk_score': [],
                'status': []
            }
            
            for feed in feeds:
                df_data['timestamp'].append(feed['created_at'])
                df_data['allergen'].append(float(feed.get('field1', 0)))
                df_data['temperature'].append(float(feed.get('field2', 0)))
                df_data['risk_score'].append(float(feed.get('field3', 0)))
                status = 'SAFE' if float(feed.get('field4', 1)) == 1 else 'UNSAFE'
                df_data['status'].append(status)
            
            return pd.DataFrame(df_data)
    except Exception as e:
        st.error(f"Error fetching historical data: {e}")
    
    return None

# ============================================================================
# PAGE LAYOUT
# ============================================================================

st.title("🍽️ Allergen Safety Dashboard")
st.markdown("Real-time monitoring & verification system using ThingSpeak")

# Sidebar
with st.sidebar:
    st.header("Settings")
    refresh_interval = st.slider("Refresh interval (seconds)", 5, 60, 20)
    num_readings = st.slider("Show last N readings", 10, 200, 60)

# ============================================================================
# MAIN CONTENT
# ============================================================================

col1, col2, col3, col4 = st.columns(4)

# Get latest data
latest_data = get_latest_data()

if latest_data:
    with col1:
        st.metric(
            "Allergen Level",
            f"{latest_data['allergen']:.2f} ppm",
            "Safe" if latest_data['allergen'] < 100 else "Unsafe"
        )
    
    with col2:
        st.metric(
            "Temperature",
            f"{latest_data['temperature']:.1f} °C"
        )
    
    with col3:
        st.metric(
            "Risk Score",
            f"{latest_data['risk_score']:.2f}"
        )
    
    with col4:
        status = "SAFE" if latest_data['is_safe'] else "UNSAFE"
        st.metric("Status", status)

st.divider()

# ============================================================================
# CHARTS
# ============================================================================

col_chart1, col_chart2 = st.columns(2)

# Get historical data
historical_df = get_historical_data(num_readings)

if historical_df is not None:
    # Allergen Trend Chart
    with col_chart1:
        st.subheader("Allergen Level Trend")
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=historical_df['timestamp'],
            y=historical_df['allergen'],
            mode='lines+markers',
            name='Allergen Level',
            line=dict(color='#667eea', width=2),
            fill='tozeroy'
        ))
        
        fig.add_hline(y=100, line_dash="dash", line_color="green", annotation_text="Safe Threshold")
        fig.add_hline(y=150, line_dash="dash", line_color="red", annotation_text="Unsafe Threshold")
        
        fig.update_layout(
            title="Allergen Concentration Over Time",
            xaxis_title="Time",
            yaxis_title="PPM",
            hovermode='x unified',
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    # Risk Score Chart
    with col_chart2:
        st.subheader("Risk Score Trend")
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=historical_df['timestamp'],
            y=historical_df['risk_score'],
            mode='lines+markers',
            name='Risk Score',
            line=dict(color='#764ba2', width=2)
        ))
        
        fig.add_hline(y=10, line_dash="dash", line_color="red", annotation_text="Safe Limit (10)")
        
        fig.update_layout(
            title="Risk Score Over Time",
            xaxis_title="Time",
            yaxis_title="Risk Score",
            hovermode='x unified',
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)

st.divider()

# ============================================================================
# DATA TABLE
# ============================================================================

st.subheader("Recent Readings")

if historical_df is not None:
    # Reverse to show newest first
    display_df = historical_df.iloc[::-1].reset_index(drop=True)
    
    # Style the dataframe
    def style_row(row):
        if row['status'] == 'SAFE':
            return ['background-color: #d4edda'] * len(row)
        else:
            return ['background-color: #f8d7da'] * len(row)
    
    styled_df = display_df.style.apply(style_row, axis=1)
    st.dataframe(styled_df, use_container_width=True)
else:
    st.info("Waiting for data from ThingSpeak...")

# ============================================================================
# AUTO REFRESH
# ============================================================================

placeholder = st.empty()
with placeholder.container():
    st.info(f"Auto-refreshing every {refresh_interval} seconds...")

time.sleep(refresh_interval)
st.rerun()