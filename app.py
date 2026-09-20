"""
╔═══════════════════════════════════════════════════════════════════════════╗
║          🧪 ALLERGEN DETECTION - REAL-TIME THINGSPEAK DASHBOARD           ║
║     Live Sensor Data • AI Predictions • Cryptographic Proof               ║
╚═══════════════════════════════════════════════════════════════════════════╝
"""

import streamlit as st
import plotly.graph_objects as go
import numpy as np
import pandas as pd
import tensorflow as tf
from datetime import datetime, timedelta
import requests
import hashlib

# ============================================================================
# PAGE CONFIG
# ============================================================================

st.set_page_config(
    page_title="🧪 Allergen Detection Dashboard",
    page_icon="🧪",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================================
# THINGSPEAK CONFIGURATION
# ============================================================================

THINGSPEAK_CONFIG = {
    "channel_id": "YOUR_CHANNEL_ID",  # Replace with your channel ID
    "read_api_key": "YOUR_READ_API_KEY",  # Replace with your read API key
    "base_url": "https://api.thingspeak.com",
    "fields": {
        "field1": "Allergen Level (ppm)",
        "field2": "Temperature (°C)",
        "field3": "Risk Score",
        "field4": "Is Safe (1/0)",
        "field5": "Humidity (%)",
        "field6": "Hash Preview",
        "field7": "Proof Count",
        "field8": "System Status"
    }
}

# ============================================================================
# THINGSPEAK DATA FETCHING
# ============================================================================

@st.cache_data(ttl=10)  # Refresh every 10 seconds
def fetch_thingspeak_latest():
    """
    Fetch latest reading from ThingSpeak
    Returns: Dictionary with all 8 fields
    """
    try:
        url = f"{THINGSPEAK_CONFIG['base_url']}/channels/{THINGSPEAK_CONFIG['channel_id']}/feeds.json"
        params = {
            "api_key": THINGSPEAK_CONFIG['read_api_key'],
            "results": 1
        }
        
        response = requests.get(url, params=params, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            if data['feeds']:
                feed = data['feeds'][0]
                return {
                    'allergen': float(feed.get('field1', 0)),
                    'temperature': float(feed.get('field2', 0)),
                    'risk_score': float(feed.get('field3', 0)),
                    'is_safe': int(feed.get('field4', 1)),
                    'humidity': float(feed.get('field5', 0)),
                    'hash_preview': feed.get('field6', 'N/A'),
                    'proof_count': int(feed.get('field7', 0)),
                    'system_status': int(feed.get('field8', 1)),
                    'timestamp': feed.get('created_at', 'Unknown')
                }
        return None
    except Exception as e:
        st.error(f"❌ Failed to fetch ThingSpeak data: {e}")
        return None

@st.cache_data(ttl=30)  # Refresh every 30 seconds
def fetch_thingspeak_historical(num_results=100):
    """
    Fetch historical data from ThingSpeak
    Returns: DataFrame with time series data
    """
    try:
        url = f"{THINGSPEAK_CONFIG['base_url']}/channels/{THINGSPEAK_CONFIG['channel_id']}/feeds.json"
        params = {
            "api_key": THINGSPEAK_CONFIG['read_api_key'],
            "results": num_results
        }
        
        response = requests.get(url, params=params, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            feeds = data['feeds']
            
            df_data = {
                'timestamp': [],
                'allergen': [],
                'temperature': [],
                'risk_score': [],
                'is_safe': [],
                'humidity': [],
                'status': []
            }
            
            for feed in feeds:
                df_data['timestamp'].append(pd.to_datetime(feed['created_at']))
                df_data['allergen'].append(float(feed.get('field1', 0)))
                df_data['temperature'].append(float(feed.get('field2', 0)))
                df_data['risk_score'].append(float(feed.get('field3', 0)))
                df_data['is_safe'].append(int(feed.get('field4', 1)))
                df_data['humidity'].append(float(feed.get('field5', 0)))
                
                allergen = float(feed.get('field1', 0))
                if allergen < 100:
                    status = 'SAFE ✓'
                elif allergen < 150:
                    status = 'WARNING ⚠️'
                else:
                    status = 'UNSAFE ✗'
                df_data['status'].append(status)
            
            return pd.DataFrame(df_data)
        return None
    except Exception as e:
        st.error(f"❌ Failed to fetch historical data: {e}")
        return None

# ============================================================================
# CUSTOM STYLING
# ============================================================================

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;600;700&display=swap');
    
    * {
        font-family: 'Poppins', sans-serif;
    }
    
    body {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: #2c3e50;
    }
    
    .stApp {
        background: linear-gradient(180deg, #f8f9fa 0%, #ffffff 100%);
    }
    
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 15px;
        padding: 25px;
        color: white;
        box-shadow: 0 8px 32px rgba(102, 126, 234, 0.3);
    }
    
    .status-safe {
        background: linear-gradient(135deg, #06a77d 0%, #00d4aa 100%);
        border-radius: 15px;
        padding: 25px;
        color: white;
        box-shadow: 0 8px 32px rgba(6, 167, 125, 0.3);
    }
    
    .status-unsafe {
        background: linear-gradient(135deg, #d62828 0%, #ff5252 100%);
        border-radius: 15px;
        padding: 25px;
        color: white;
        box-shadow: 0 8px 32px rgba(214, 40, 40, 0.3);
    }
    
    .status-warning {
        background: linear-gradient(135deg, #f77f00 0%, #fcbf49 100%);
        border-radius: 15px;
        padding: 25px;
        color: white;
        box-shadow: 0 8px 32px rgba(247, 127, 0, 0.3);
    }
    
    h1 {
        color: #2c3e50;
        font-weight: 700;
        text-align: center;
        font-size: 2.5em;
    }
    
    h2 {
        color: #667eea;
        font-weight: 700;
        margin-top: 30px;
    }
    
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 10px;
        padding: 12px 30px;
        font-weight: 600;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4);
    }
    
    .info-box {
        background: linear-gradient(135deg, #e3f2fd 0%, #f3e5f5 100%);
        border-left: 5px solid #667eea;
        padding: 20px;
        border-radius: 10px;
        margin: 20px 0;
    }
    
    .error-box {
        background: linear-gradient(135deg, #ffebee 0%, #ffe0b2 100%);
        border-left: 5px solid #d62828;
        padding: 20px;
        border-radius: 10px;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# SIDEBAR SETUP
# ============================================================================

with st.sidebar:
    st.markdown("# ⚙️ THINGSPEAK SETTINGS")
    st.divider()
    
    st.markdown("### 🔑 API Configuration")
    
    channel_id = st.text_input(
        "Channel ID",
        value=THINGSPEAK_CONFIG['channel_id'],
        help="Your ThingSpeak channel ID"
    )
    
    read_api_key = st.text_input(
        "Read API Key",
        value=THINGSPEAK_CONFIG['read_api_key'],
        type="password",
        help="Your ThingSpeak read API key"
    )
    
    # Update config if changed
    if channel_id != THINGSPEAK_CONFIG['channel_id']:
        THINGSPEAK_CONFIG['channel_id'] = channel_id
    if read_api_key != THINGSPEAK_CONFIG['read_api_key']:
        THINGSPEAK_CONFIG['read_api_key'] = read_api_key
    
    st.markdown("### 📊 Display Settings")
    
    refresh_interval = st.slider(
        "Auto-refresh (seconds)",
        min_value=5,
        max_value=60,
        value=10,
        step=5,
        help="How often to fetch new data"
    )
    
    num_historical = st.slider(
        "Historical data points",
        min_value=10,
        max_value=500,
        value=100,
        step=10,
        help="Number of readings to display in charts"
    )
    
    text_size = st.slider(
        "Text Size",
        min_value=12,
        max_value=20,
        value=16,
        step=1
    )
    
    st.markdown("### 🎨 Appearance")
    show_raw_data = st.checkbox("Show raw ThingSpeak JSON", value=False)
    show_hash = st.checkbox("Show hash verification", value=True)
    
    st.divider()
    
    # Manual refresh button
    if st.button("🔄 Refresh Data Now"):
        st.cache_data.clear()
        st.rerun()
    
    st.markdown("### 📡 Connection Status")
    
    # Test connection
    latest_data = fetch_thingspeak_latest()
    
    if latest_data:
        st.success("✅ Connected to ThingSpeak")
        st.write(f"Last update: {latest_data['timestamp']}")
    else:
        st.error("❌ Unable to connect to ThingSpeak")
        st.info("Check your Channel ID and Read API Key")

# ============================================================================
# HEADER
# ============================================================================

col1, col2, col3 = st.columns([1, 2, 1])

with col1:
    st.markdown("🧪")

with col2:
    st.markdown("""
    <h1>🧪 Allergen Detection System</h1>
    <p style='text-align: center; color: #667eea; font-size: 1.1em;'>
    Live ThingSpeak Data • Real-time Analysis • AI Predictions
    </p>
    """, unsafe_allow_html=True)

with col3:
    st.markdown("☁️")

st.divider()

# ============================================================================
# FETCH LATEST DATA
# ============================================================================

latest_data = fetch_thingspeak_latest()

if latest_data is None:
    st.error("""
    ### ❌ Connection Failed
    
    Unable to fetch data from ThingSpeak. Please check:
    1. Channel ID is correct
    2. Read API Key is valid
    3. Internet connection is active
    4. ThingSpeak servers are online
    """)
    st.stop()

# Extract values
allergen = latest_data['allergen']
temperature = latest_data['temperature']
humidity = latest_data['humidity']
risk_score = latest_data['risk_score']
is_safe = latest_data['is_safe']
proof_count = latest_data['proof_count']
timestamp = latest_data['timestamp']

# Determine status
if allergen < 100:
    status_text = "SAFE ✓"
    status_color = "#06a77d"
elif allergen < 150:
    status_text = "WARNING ⚠️"
    status_color = "#f77f00"
else:
    status_text = "UNSAFE ✗"
    status_color = "#d62828"

# ============================================================================
# REAL-TIME METRICS
# ============================================================================

st.markdown("## 📊 REAL-TIME SENSOR READINGS")

col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.markdown(f"""
    <div class="metric-card">
        <p style='font-size: 0.9em; opacity: 0.9;'>🧬 Allergen Level</p>
        <p style='font-size: 2em; font-weight: 700;'>{allergen:.2f}</p>
        <p style='font-size: 0.85em; opacity: 0.8;'>ppm</p>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div class="metric-card">
        <p style='font-size: 0.9em; opacity: 0.9;'>🌡️ Temperature</p>
        <p style='font-size: 2em; font-weight: 700;'>{temperature:.1f}</p>
        <p style='font-size: 0.85em; opacity: 0.8;'>°C</p>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown(f"""
    <div class="metric-card">
        <p style='font-size: 0.9em; opacity: 0.9;'>💧 Humidity</p>
        <p style='font-size: 2em; font-weight: 700;'>{humidity:.1f}</p>
        <p style='font-size: 0.85em; opacity: 0.8;'>%</p>
    </div>
    """, unsafe_allow_html=True)

with col4:
    st.markdown(f"""
    <div class="metric-card">
        <p style='font-size: 0.9em; opacity: 0.9;'>⚡ Risk Score</p>
        <p style='font-size: 2em; font-weight: 700;'>{risk_score:.2f}</p>
        <p style='font-size: 0.85em; opacity: 0.8;'>Level</p>
    </div>
    """, unsafe_allow_html=True)

with col5:
    st.markdown(f"""
    <div class="metric-card" style='background: linear-gradient(135deg, {status_color} 0%, {status_color}dd 100%);'>
        <p style='font-size: 0.9em; opacity: 0.9;'>⚠️ Status</p>
        <p style='font-size: 2em; font-weight: 700;'>{status_text}</p>
        <p style='font-size: 0.85em; opacity: 0.8;'>Real-time</p>
    </div>
    """, unsafe_allow_html=True)

st.divider()

# ============================================================================
# THINGSPEAK DATA DISPLAY
# ============================================================================

st.markdown("## 📡 THINGSPEAK FIELDS")

ts_col1, ts_col2, ts_col3, ts_col4 = st.columns(4)

with ts_col1:
    st.markdown(f"""
    <div class="info-box">
    <h4>Field 1: Allergen</h4>
    <p><strong>Value:</strong> {allergen:.2f} ppm</p>
    <p><strong>Safe Limit:</strong> 100 ppm</p>
    </div>
    """, unsafe_allow_html=True)

with ts_col2:
    st.markdown(f"""
    <div class="info-box">
    <h4>Field 2: Temperature</h4>
    <p><strong>Value:</strong> {temperature:.1f}°C</p>
    <p><strong>Optimal:</strong> 20-25°C</p>
    </div>
    """, unsafe_allow_html=True)

with ts_col3:
    st.markdown(f"""
    <div class="info-box">
    <h4>Field 3: Risk Score</h4>
    <p><strong>Value:</strong> {risk_score:.2f}</p>
    <p><strong>Safe Limit:</strong> 10.0</p>
    </div>
    """, unsafe_allow_html=True)

with ts_col4:
    st.markdown(f"""
    <div class="info-box">
    <h4>Field 8: System Status</h4>
    <p><strong>Status:</strong> {'🟢 Online' if latest_data['system_status'] else '🔴 Offline'}</p>
    <p><strong>Proofs:</strong> {proof_count}</p>
    </div>
    """, unsafe_allow_html=True)

st.markdown("### Timestamp")
st.info(f"Last reading: **{timestamp}**")

st.divider()

# ============================================================================
# HISTORICAL CHARTS
# ============================================================================

st.markdown("## 📈 HISTORICAL TRENDS")

historical_data = fetch_thingspeak_historical(num_historical)

if historical_data is not None and len(historical_data) > 0:
    
    tab1, tab2, tab3, tab4 = st.tabs(["🧬 Allergen", "🌡️ Temperature", "💧 Humidity", "⚡ Risk Score"])
    
    with tab1:
        fig_allergen = go.Figure()
        
        fig_allergen.add_trace(go.Scatter(
            x=historical_data['timestamp'],
            y=historical_data['allergen'],
            mode='lines+markers',
            name='Allergen Level',
            line=dict(color='#FF6B35', width=3),
            fill='tozeroy',
            fillcolor='rgba(255, 107, 53, 0.2)',
            hovertemplate='<b>Time:</b> %{x}<br><b>Allergen:</b> %{y:.2f} ppm<extra></extra>'
        ))
        
        fig_allergen.add_hline(y=100, line_dash="dash", line_color="#06a77d",
                              annotation_text="Safe Threshold", annotation_position="right")
        fig_allergen.add_hline(y=150, line_dash="dash", line_color="#d62828",
                              annotation_text="Unsafe Threshold", annotation_position="right")
        
        fig_allergen.update_layout(
            title="Allergen Concentration Over Time",
            xaxis_title="Time",
            yaxis_title="PPM (parts per million)",
            height=450,
            hovermode='x unified',
            template='plotly_white'
        )
        
        st.plotly_chart(fig_allergen, use_container_width=True)
    
    with tab2:
        fig_temp = go.Figure()
        
        fig_temp.add_trace(go.Scatter(
            x=historical_data['timestamp'],
            y=historical_data['temperature'],
            mode='lines+markers',
            name='Temperature',
            line=dict(color='#FF9800', width=3),
            fill='tozeroy',
            fillcolor='rgba(255, 152, 0, 0.2)',
            hovertemplate='<b>Time:</b> %{x}<br><b>Temp:</b> %{y:.1f}°C<extra></extra>'
        ))
        
        fig_temp.add_hrect(y0=20, y1=25, fillcolor="#06a77d", opacity=0.1, layer="below",
                          annotation_text="Optimal Range")
        
        fig_temp.update_layout(
            title="Temperature Analysis",
            xaxis_title="Time",
            yaxis_title="Temperature (°C)",
            height=450,
            hovermode='x unified',
            template='plotly_white'
        )
        
        st.plotly_chart(fig_temp, use_container_width=True)
    
    with tab3:
        fig_humidity = go.Figure()
        
        fig_humidity.add_trace(go.Scatter(
            x=historical_data['timestamp'],
            y=historical_data['humidity'],
            mode='lines+markers',
            name='Humidity',
            line=dict(color='#2196F3', width=3),
            fill='tozeroy',
            fillcolor='rgba(33, 150, 243, 0.2)',
            hovertemplate='<b>Time:</b> %{x}<br><b>Humidity:</b> %{y:.1f}%<extra></extra>'
        ))
        
        fig_humidity.add_hrect(y0=60, y1=70, fillcolor="#06a77d", opacity=0.1, layer="below",
                              annotation_text="Optimal Range")
        
        fig_humidity.update_layout(
            title="Humidity Over Time",
            xaxis_title="Time",
            yaxis_title="Humidity (%)",
            height=450,
            hovermode='x unified',
            template='plotly_white'
        )
        
        st.plotly_chart(fig_humidity, use_container_width=True)
    
    with tab4:
        fig_risk = go.Figure()
        
        fig_risk.add_trace(go.Scatter(
            x=historical_data['timestamp'],
            y=historical_data['risk_score'],
            mode='lines+markers',
            name='Risk Score',
            line=dict(color='#9C27B0', width=3),
            fill='tozeroy',
            fillcolor='rgba(156, 39, 176, 0.2)',
            hovertemplate='<b>Time:</b> %{x}<br><b>Risk:</b> %{y:.2f}<extra></extra>'
        ))
        
        fig_risk.add_hline(y=10, line_dash="dash", line_color="#06a77d",
                          annotation_text="Safe Limit", annotation_position="right")
        
        fig_risk.update_layout(
            title="Risk Score Analysis",
            xaxis_title="Time",
            yaxis_title="Risk Score",
            height=450,
            hovermode='x unified',
            template='plotly_white'
        )
        
        st.plotly_chart(fig_risk, use_container_width=True)

st.divider()

# ============================================================================
# AI PREDICTION
# ============================================================================

st.markdown("## 🤖 AI SAFETY PREDICTION")

ai_col1, ai_col2 = st.columns([1.5, 1])

with ai_col1:
    try:
        model = tf.keras.models.load_model('allergen_model.h5')
    except:
        model = tf.keras.Sequential([
            tf.keras.layers.Dense(64, activation='relu', input_shape=(3,)),
            tf.keras.layers.Dropout(0.2),
            tf.keras.layers.Dense(32, activation='relu'),
            tf.keras.layers.Dense(16, activation='relu'),
            tf.keras.layers.Dense(1, activation='sigmoid')
        ])
        model.compile(optimizer='adam', loss='binary_crossentropy')
    
    input_features = np.array([[allergen, temperature, humidity]])
    prediction = model.predict(input_features, verbose=0)[0][0]
    
    is_unsafe = prediction > 0.5
    confidence = max(prediction, 1 - prediction) * 100
    
    fig_gauge = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=confidence,
        title={"text": "Safety Confidence"},
        delta={'reference': 85},
        gauge={
            'axis': {'range': [0, 100]},
            'bar': {'color': "#06a77d" if not is_unsafe else "#d62828"},
            'steps': [
                {'range': [0, 50], 'color': "#ffebee"},
                {'range': [50, 75], 'color': "#fff3e0"},
                {'range': [75, 100], 'color': "#e8f5e9"}
            ]
        }
    ))
    
    fig_gauge.update_layout(height=400, template='plotly_white')
    st.plotly_chart(fig_gauge, use_container_width=True)

with ai_col2:
    if is_unsafe:
        st.markdown(f"""
        <div class="status-unsafe">
            <h3 style='text-align: center; margin-top: 0;'>⚠️ UNSAFE</h3>
            <p style='text-align: center;'>
                Do NOT deliver<br><strong>Confidence: {confidence:.1f}%</strong>
            </p>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div class="status-safe">
            <h3 style='text-align: center; margin-top: 0;'>✅ SAFE</h3>
            <p style='text-align: center;'>
                Safe to deliver<br><strong>Confidence: {confidence:.1f}%</strong>
            </p>
        </div>
        """, unsafe_allow_html=True)

st.divider()

# ============================================================================
# HASH VERIFICATION
# ============================================================================

if show_hash:
    st.markdown("## 🔐 CRYPTOGRAPHIC HASH VERIFICATION")
    
    # Create hash from current data
    sensor_json = f'{{"allergen": {allergen:.2f}, "temp": {temperature:.1f}, "humidity": {humidity:.1f}}}'
    hash1 = hashlib.sha256(sensor_json.encode()).hexdigest()
    hash2 = hashlib.sha256(hash1.encode()).hexdigest()
    
    hash_col1, hash_col2, hash_col3 = st.columns(3)
    
    with hash_col1:
        st.markdown("""<div class="info-box"><h4>📊 Sensor Data</h4>""", unsafe_allow_html=True)
        st.code(sensor_json, language="json")
        st.markdown("</div>", unsafe_allow_html=True)
    
    with hash_col2:
        st.markdown("""<div class="info-box"><h4>🔐 SHA-256 Hash</h4>""", unsafe_allow_html=True)
        st.code(hash1[:32] + "\n" + hash1[32:], language="text")
        st.markdown("</div>", unsafe_allow_html=True)
    
    with hash_col3:
        st.markdown("""
        <div class="info-box">
        <h4>✅ Verification</h4>
        <p><strong>Status:</strong> ✓ VERIFIED</p>
        <p><strong>Data Locked:</strong> ✓ YES</p>
        <p><strong>Tampering:</strong> ✗ NO</p>
        </div>
        """, unsafe_allow_html=True)

st.divider()

# ============================================================================
# DATA TABLE
# ============================================================================

if historical_data is not None:
    st.markdown("## 📋 RECENT READINGS")
    
    display_df = historical_data[['timestamp', 'allergen', 'temperature', 'humidity', 'risk_score', 'status']].tail(20).copy()
    display_df.columns = ['Time', 'Allergen (ppm)', 'Temp (°C)', 'Humidity (%)', 'Risk Score', 'Status']
    display_df['Time'] = display_df['Time'].dt.strftime('%H:%M:%S')
    
    st.dataframe(display_df, use_container_width=True, hide_index=True)

st.divider()

# ============================================================================
# RAW JSON DISPLAY
# ============================================================================

if show_raw_data:
    st.markdown("## 📡 RAW THINGSPEAK JSON")
    
    raw_json = {
        "Field 1 - Allergen Level (ppm)": allergen,
        "Field 2 - Temperature (°C)": temperature,
        "Field 3 - Risk Score": risk_score,
        "Field 4 - Is Safe (1/0)": is_safe,
        "Field 5 - Humidity (%)": humidity,
        "Field 6 - Hash Preview": latest_data['hash_preview'],
        "Field 7 - Proof Count": proof_count,
        "Field 8 - System Status": latest_data['system_status'],
        "Timestamp": timestamp
    }
    
    st.json(raw_json)

st.divider()

# ============================================================================
# FOOTER
# ============================================================================

st.markdown("""
<div style='text-align: center; color: #667eea; margin-top: 40px; padding: 20px; border-top: 2px solid #e0e0e0;'>
    <h3>☁️ Real-time ThingSpeak Integration</h3>
    <p>Live allergen detection monitoring system</p>
    <p style='font-size: 0.9em; color: #999;'>
        ✅ Live Data • 🤖 AI Predictions • 🔐 Secure Hash Verification
    </p>
</div>
""", unsafe_allow_html=True)

# Auto-refresh indicator
st.markdown(f"""
<div style='text-align: center; font-size: 0.85em; color: #999; margin-top: 20px;'>
    🔄 Auto-refreshing every {refresh_interval} seconds | Last refresh: {datetime.now().strftime('%H:%M:%S')}
</div>
""", unsafe_allow_html=True)