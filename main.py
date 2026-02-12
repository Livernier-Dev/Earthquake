import streamlit as st
import requests
import pandas as pd
import datetime
import folium
import json
import os
import math
import random  # <--- เพิ่มบรรทัดนี้ครับ
from streamlit_folium import st_folium

# --- 1. ตั้งค่าหน้าเว็บ ---
st.set_page_config(page_title="Global Earthquake & Prediction AI", layout="wide", page_icon="🌍")
st.title("🌍 AI เฝ้าระวังและประเมินความเสี่ยงแผ่นดินไหวโลก")

# --- 2. Config System ---
CONFIG_FILE = "config.json"

def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f: return json.load(f)
        except: return {}
    return {}

def save_config(config_data):
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config_data, f, ensure_ascii=False, indent=4)
        return True
    except: return False

saved_config = load_config()

# --- 3. Alert System (Text Only) ---
def send_line_notify(token, data, risk_prob):
    url = 'https://notify-api.line.me/api/notify'
    headers = {'Authorization': f'Bearer {token}'}
    msg = (
        f"\n🔴 ALERT: แผ่นดินไหว!\n"
        f"จุดเกิดเหตุ: {data['place']}\n"
        f"ความแรง: {data['mag']:.1f}\n"
        f"โอกาสเกิดซ้ำ/รุนแรง: {risk_prob}%\n"
        f"พิกัด: {data['lat']:.4f}, {data['lon']:.4f}\n"
        f"Maps: http://maps.google.com/?q={data['lat']},{data['lon']}"
    )
    try: requests.post(url, headers=headers, data={'message': msg})
    except: pass

def send_discord_webhook(webhook_url, data, risk_prob):
    color = 15158332 if data['mag'] >= 6.0 else 3066993
    embed = {
        "username": "Seismic AI",
        "embeds": [{
            "title": f"🚨 Mag {data['mag']:.1f} | Risk: {risk_prob}%",
            "description": f"**{data['place']}**\nTime: {data['time']}",
            "color": color,
            "fields": [
                {"name": "Magnitude", "value": f"{data['mag']:.1f}", "inline": True},
                {"name": "AI Prediction Risk", "value": f"{risk_prob}%", "inline": True}
            ],
            "url": f"http://maps.google.com/?q={data['lat']},{data['lon']}"
        }]
    }
    try: requests.post(webhook_url, json=embed)
    except: pass

# --- 4. Helper: แยกชื่อประเทศ ---
def extract_country(place_str):
    if not place_str: return "Unknown"
    parts = place_str.split(',')
    return parts[-1].strip() # เอาส่วนท้ายสุดที่เป็นชื่อประเทศ/รัฐ

# --- 5. AI Prediction Logic (Risk Algorithm) ---
def calculate_risk_prediction(df):
    """
    คำนวณความเสี่ยง (0-100%) โดยแบ่งโลกเป็นตาราง Grid (5x5 องศา)
    ถ้า Grid ไหนมีกิจกรรมเยอะ = มีโอกาสเกิดเหตุรุนแรงต่อเนื่องสูง
    """
    if df.empty: return df
    
    # 1. สร้าง Grid ID (ปัดเศษ Lat/Lon เพื่อจัดกลุ่มพื้นที่ใกล้เคียง)
    df['lat_grid'] = df['lat'].apply(lambda x: round(x / 5.0) * 5.0)
    df['lon_grid'] = df['lon'].apply(lambda x: round(x / 5.0) * 5.0)
    
    # 2. คำนวณสถิติในแต่ละ Grid
    grid_stats = df.groupby(['lat_grid', 'lon_grid']).agg({
        'mag': ['count', 'max', 'mean'], # จำนวนครั้ง, แรงสุด, เฉลี่ย
        'time_stamp': 'max' # เวลาล่าสุด
    }).reset_index()
    
    grid_stats.columns = ['lat_grid', 'lon_grid', 'count', 'max_mag', 'mean_mag', 'last_time']
    
    # 3. สูตรคำนวณความเสี่ยง (Heuristic Probability)
    # ความเสี่ยง = (จำนวนครั้ง * 2) + (แรงสุด * 8)
    # ปรับแต่ง Weight ได้ตามความเหมาะสม
    grid_stats['risk_score'] = (grid_stats['count'] * 3) + (grid_stats['max_mag'] ** 2)
    
    # Normalize ให้เป็น 0-100%
    max_score = grid_stats['risk_score'].max() if grid_stats['risk_score'].max() > 0 else 1
    grid_stats['probability'] = (grid_stats['risk_score'] / max_score) * 100
    grid_stats['probability'] = grid_stats['probability'].round(1)
    
    # Merge กลับไปที่ DF หลัก
    df = pd.merge(df, grid_stats[['lat_grid', 'lon_grid', 'probability']], on=['lat_grid', 'lon_grid'], how='left')
    return df

# --- 6. Main Data Logic ---
@st.cache_data(ttl=300)
def get_data():
    try:
        # ดึงข้อมูลทั่วโลก (Global)
        url = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/2.5_day.geojson"
        resp = requests.get(url, timeout=10)
        data = resp.json()
        
        features = []
        for f in data['features']:
            p = f['properties']
            g = f['geometry']
            features.append({
                "id": f['id'],
                "place": p['place'],
                "country": extract_country(p['place']),
                "mag": p['mag'],
                "time_stamp": p['time'],
                "time": datetime.datetime.fromtimestamp(p['time']/1000).strftime('%Y-%m-%d %H:%M:%S'),
                "lat": g['coordinates'][1],
                "lon": g['coordinates'][0],
                "is_fake": False
            })
        return pd.DataFrame(features)
    except: return pd.DataFrame()

def get_marker_color(mag):
    if mag < 4: return 'green'
    elif mag < 6: return 'orange'
    elif mag < 7.5: return 'red'
    else: return 'darkred'

if 'fake_data' not in st.session_state: st.session_state.fake_data = []
if 'alerted_ids' not in st.session_state: st.session_state.alerted_ids = set()

# --- 7. Sidebar & Settings ---
with st.sidebar:
    st.header("⚙️ Settings")
    with st.form("settings"):
        st.subheader("🔔 Notification Config")
        use_line = st.checkbox("LINE Notify", value=saved_config.get("use_line", False))
        line_token = st.text_input("LINE Token", value=saved_config.get("line_token", ""), type="password")
        
        st.divider()
        use_discord = st.checkbox("Discord Webhook", value=saved_config.get("use_discord", False))
        discord_url = st.text_input("Webhook URL", value=saved_config.get("discord_url", ""), type="password")

        if st.form_submit_button("💾 Save Settings"):
            save_config({
                "use_line": use_line, "line_token": line_token,
                "use_discord": use_discord, "discord_url": discord_url
            })
            st.success("Saved!")
            saved_config = load_config()

    st.divider()
    if st.button("🚨 Simulate High Risk Event"):
        sim_data = {
            "id": f"sim_{int(datetime.datetime.now().timestamp())}",
            "place": "SIMULATION HIGH RISK ZONE",
            "country": "Simulation Land",
            "mag": random.uniform(7.0, 9.0), # <--- จุดที่เคย Error ตอนนี้หายแล้วครับเพราะ import random แล้ว
            "time_stamp": datetime.datetime.now().timestamp() * 1000,
            "time": datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "lat": random.uniform(-20, 20), "lon": random.uniform(120, 150),
            "is_fake": True
        }
        st.session_state.fake_data.append(sim_data)
        st.rerun()
    
    if st.button("🗑️ Clear Data"):
        st.session_state.fake_data = []
        st.session_state.alerted_ids = set()
        st.rerun()

# --- 8. Data Processing ---
df_real = get_data()
df = pd.concat([df_real, pd.DataFrame(st.session_state.fake_data)], ignore_index=True)

if not df.empty:
    # 8.1 คำนวณค่า Prediction Risk
    df = calculate_risk_prediction(df)

    # 8.2 ส่ง Alert (ถ้ามี Event ใหม่)
    alerts = df[df['mag'] >= 5.0]
    for _, row in alerts.iterrows():
        if row['id'] not in st.session_state.alerted_ids:
            payload = row.to_dict()
            risk = row['probability']
            
            if saved_config.get("use_line") and saved_config.get("line_token"):
                send_line_notify(saved_config["line_token"], payload, risk)
            if saved_config.get("use_discord") and saved_config.get("discord_url"):
                send_discord_webhook(saved_config["discord_url"], payload, risk)
                
            st.session_state.alerted_ids.add(row['id'])
            st.toast(f"New Alert! Risk: {risk}%", icon="⚠️")

    # --- 9. Display Section ---
    
    # สร้าง Tabs เพื่อแยกมุมมอง
    tab1, tab2, tab3 = st.tabs(["🗺️ Global Map & Prediction", "📊 Statistics by Country", "📋 Raw Data"])

    with tab1:
        st.subheader("แผนที่โลกแสดงจุดเกิดเหตุและความเสี่ยง (Risk Heatmap)")
        
        # กรอง Grid ที่มีความเสี่ยงสูงมาแสดงเป็นวงกลมใหญ่
        high_risk_zones = df[df['probability'] > 50].drop_duplicates(subset=['lat_grid', 'lon_grid'])
        
        # Center Map
        center = [df.iloc[0]['lat'], df.iloc[0]['lon']] if not df.empty else [20,0]
        m = folium.Map(location=center, zoom_start=2, tiles="CartoDB dark_matter")

        # 1. วาด Risk Zones (พื้นที่เสี่ยงสูง)
        for _, zone in high_risk_zones.iterrows():
            folium.Circle(
                location=[zone['lat_grid'], zone['lon_grid']],
                radius=300000, # รัศมี 300km
                color='red', weight=0, fill=True, fill_color='red', fill_opacity=0.2,
                popup=f"🔥 High Risk Zone: {zone['probability']}%"
            ).add_to(m)

        # 2. วาดจุดแผ่นดินไหว
        for _, row in df.iterrows():
            mag = row['mag']
            prob = row['probability']
            color = '#9900cc' if row['is_fake'] else get_marker_color(mag)
            
            popup_html = f"""
            <b>{row['place']}</b><br>
            Mag: {mag:.1f}<br>
            Risk Probability: {prob}%<br>
            Country: {row['country']}
            """
            
            # วงคลื่น Shockwave
            folium.Circle(
                [row['lat'], row['lon']],
                radius=(mag**4)*20, color=color, weight=1, fill=True, fill_color=color, fill_opacity=0.1
            ).add_to(m)
            
            # จุด Marker
            folium.CircleMarker(
                [row['lat'], row['lon']],
                radius=4, color=color, fill=True, fill_color=color, fill_opacity=1.0,
                popup=folium.Popup(popup_html, max_width=200),
                tooltip=f"{row['country']} ({mag}) - Risk {prob}%"
            ).add_to(m)

        st_folium(m, height=600, width=None)
        
        st.info("ℹ️ **Risk Probability** คำนวณจากความหนาแน่นและความรุนแรงในพื้นที่นั้นๆ ในช่วง 24 ชม. (ยิ่งสูง = ยิ่งมีโอกาสเกิด Aftershock หรือเหตุการณ์ต่อเนื่อง)")

    with tab2:
        st.subheader("สถิติแยกรายประเทศ (Global Statistics)")
        
        col_stat1, col_stat2 = st.columns(2)
        
        # Group Data by Country
        country_stats = df.groupby('country').agg({
            'mag': ['count', 'max', 'mean'],
            'probability': 'max' # ความเสี่ยงสูงสุดในประเทศนั้น
        }).reset_index()
        country_stats.columns = ['Country', 'Count', 'Max Mag', 'Avg Mag', 'Max Risk %']
        country_stats = country_stats.sort_values(by='Count', ascending=False)
        
        with col_stat1:
            st.dataframe(
                country_stats,
                column_config={
                    "Country": "ประเทศ/ภูมิภาค",
                    "Count": st.column_config.NumberColumn("จำนวนครั้ง", format="%d"),
                    "Max Mag": st.column_config.NumberColumn("แรงสุด (Mag)", format="%.1f 💥"),
                    "Max Risk %": st.column_config.ProgressColumn("ความเสี่ยงสูงสุด", format="%.0f%%", min_value=0, max_value=100)
                },
                hide_index=True,
                height=500
            )
            
        with col_stat2:
            st.write("### 🏆 Top 5 Countries (Activity)")
            st.bar_chart(country_stats.set_index('Country')['Count'].head(5))
            
            st.write("### ⚠️ Top 5 Highest Risk Areas")
            st.bar_chart(country_stats.sort_values('Max Risk %', ascending=False).set_index('Country')['Max Risk %'].head(5), color="#ff4b4b")

    with tab3:
        st.subheader("ข้อมูลดิบ (Raw Data)")
        st.dataframe(df)

else:
    st.warning("ขณะนี้ไม่สามารถดึงข้อมูลได้ หรือไม่มีแผ่นดินไหวเกิดขึ้น")
