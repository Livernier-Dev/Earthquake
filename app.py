import streamlit as st
import requests
import pandas as pd
import datetime
import folium
import json
import os
import math
import random
from streamlit_folium import st_folium

# --- 1. ตั้งค่าหน้าเว็บ ---
st.set_page_config(page_title="Global Earthquake & Prediction AI", layout="wide", page_icon="🌍")
st.title("🌍 AI เฝ้าระวังและประเมินความเสี่ยงแผ่นดินไหวโลก")

# --- 2. System Files (Config & History) ---
CONFIG_FILE = "config.json"
HISTORY_FILE = "alert_history.json"  # <--- ไฟล์ใหม่สำหรับเก็บประวัติ

def load_json(filename):
    if os.path.exists(filename):
        try:
            with open(filename, "r", encoding="utf-8") as f: return json.load(f)
        except: return {} if filename == CONFIG_FILE else []
    return {} if filename == CONFIG_FILE else []

def save_json(filename, data):
    try:
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        return True
    except: return False

# โหลดค่าต่างๆ
saved_config = load_json(CONFIG_FILE)
alerted_ids_list = load_json(HISTORY_FILE) # โหลดประวัติ ID ที่เคยแจ้งแล้ว
alerted_ids = set(alerted_ids_list) # แปลงเป็น Set เพื่อให้ทำงานเร็ว

# --- 3. Alert System ---
def send_line_notify(token, data, risk_prob):
    url = 'https://notify-api.line.me/api/notify'
    headers = {'Authorization': f'Bearer {token}'}
    msg = (
        f"\n🔴 ALERT: แผ่นดินไหว!\n"
        f"จุดเกิดเหตุ: {data['place']}\n"
        f"ความแรง: {data['mag']:.1f}\n"
        f"ความเสี่ยง: {risk_prob}%\n"
        f"เวลา: {data['time']}\n"
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
                {"name": "Prediction Risk", "value": f"{risk_prob}%", "inline": True}
            ],
            "url": f"http://maps.google.com/?q={data['lat']},{data['lon']}"
        }]
    }
    try: requests.post(webhook_url, json=embed)
    except: pass

# --- 4. Helper & AI Logic ---
def extract_country(place_str):
    if not place_str: return "Unknown"
    parts = place_str.split(',')
    return parts[-1].strip()

def calculate_risk_prediction(df):
    if df.empty: return df
    df['lat_grid'] = df['lat'].apply(lambda x: round(x / 5.0) * 5.0)
    df['lon_grid'] = df['lon'].apply(lambda x: round(x / 5.0) * 5.0)
    
    grid_stats = df.groupby(['lat_grid', 'lon_grid']).agg({
        'mag': ['count', 'max'],
    }).reset_index()
    grid_stats.columns = ['lat_grid', 'lon_grid', 'count', 'max_mag']
    
    grid_stats['risk_score'] = (grid_stats['count'] * 3) + (grid_stats['max_mag'] ** 2)
    max_score = grid_stats['risk_score'].max() if grid_stats['risk_score'].max() > 0 else 1
    grid_stats['probability'] = ((grid_stats['risk_score'] / max_score) * 100).round(1)
    
    df = pd.merge(df, grid_stats[['lat_grid', 'lon_grid', 'probability']], on=['lat_grid', 'lon_grid'], how='left')
    return df

def get_marker_color(mag):
    if mag < 4: return 'green'
    elif mag < 6: return 'orange'
    elif mag < 7.5: return 'red'
    else: return 'darkred'

# --- 5. Main Data Logic ---
@st.cache_data(ttl=300)
def get_data():
    try:
        url = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/2.5_day.geojson"
        resp = requests.get(url, timeout=10)
        data = resp.json()
        features = []
        for f in data['features']:
            p, g = f['properties'], f['geometry']
            features.append({
                "id": f['id'], "place": p['place'], "country": extract_country(p['place']),
                "mag": p['mag'], "time_stamp": p['time'],
                "time": datetime.datetime.fromtimestamp(p['time']/1000).strftime('%Y-%m-%d %H:%M:%S'),
                "lat": g['coordinates'][1], "lon": g['coordinates'][0], "is_fake": False
            })
        return pd.DataFrame(features)
    except: return pd.DataFrame()

if 'fake_data' not in st.session_state: st.session_state.fake_data = []

# --- 6. Sidebar Settings ---
with st.sidebar:
    st.header("⚙️ Settings")
    with st.form("settings"):
        st.subheader("🔔 Notification")
        use_line = st.checkbox("LINE Notify", value=saved_config.get("use_line", False))
        line_token = st.text_input("LINE Token", value=saved_config.get("line_token", ""), type="password")
        st.divider()
        use_discord = st.checkbox("Discord Webhook", value=saved_config.get("use_discord", False))
        discord_url = st.text_input("Webhook URL", value=saved_config.get("discord_url", ""), type="password")

        if st.form_submit_button("💾 Save Settings"):
            save_json(CONFIG_FILE, {
                "use_line": use_line, "line_token": line_token,
                "use_discord": use_discord, "discord_url": discord_url
            })
            st.success("Saved!")
            saved_config = load_json(CONFIG_FILE)

    st.divider()
    if st.button("🚨 Simulate Risk Event"):
        sim_id = f"sim_{int(datetime.datetime.now().timestamp())}"
        st.session_state.fake_data.append({
            "id": sim_id, "place": "SIMULATION ZONE", "country": "Sim Land",
            "mag": random.uniform(7.0, 9.0), "time_stamp": datetime.datetime.now().timestamp()*1000,
            "time": datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "lat": random.uniform(-20, 20), "lon": random.uniform(120, 150), "is_fake": True
        })
        st.rerun()

    if st.button("🗑️ Reset All History"):
        st.session_state.fake_data = []
        save_json(HISTORY_FILE, []) # ล้างไฟล์ประวัติ
        alerted_ids = set()
        st.rerun()

# --- 7. Processing & Alert Logic ---
df_real = get_data()
df = pd.concat([df_real, pd.DataFrame(st.session_state.fake_data)], ignore_index=True)

if not df.empty:
    df = calculate_risk_prediction(df)
    
    # Alert Logic (ป้องกันการแจ้งซ้ำด้วยไฟล์ history)
    alerts = df[df['mag'] >= 5.0]
    new_alert_count = 0
    
    for _, row in alerts.iterrows():
        # เช็คว่า ID นี้เคยแจ้งไปหรือยัง (ดูจาก Set ที่โหลดจากไฟล์มา)
        if row['id'] not in alerted_ids:
            payload = row.to_dict()
            risk = row.get('probability', 0)
            
            # ส่งแจ้งเตือน
            if saved_config.get("use_line") and saved_config.get("line_token"):
                send_line_notify(saved_config["line_token"], payload, risk)
            if saved_config.get("use_discord") and saved_config.get("discord_url"):
                send_discord_webhook(saved_config["discord_url"], payload, risk)
            
            st.toast(f"New Alert Sent: {row['place']}", icon="🔔")
            
            # เพิ่ม ID ลงใน Set และนับจำนวน
            alerted_ids.add(row['id'])
            new_alert_count += 1
    
    # ถ้ามีการแจ้งเตือนใหม่ ให้บันทึกลงไฟล์ทันที
    if new_alert_count > 0:
        save_json(HISTORY_FILE, list(alerted_ids))

    # --- 8. UI Display ---
    tab1, tab2 = st.tabs(["🗺️ Global Map", "📊 Statistics"])

    with tab1:
        st.subheader("Global Risk Map")
        center = [df.iloc[0]['lat'], df.iloc[0]['lon']] if not df.empty else [20,0]
        m = folium.Map(location=center, zoom_start=2, tiles="CartoDB dark_matter")
        
        # Risk Zones
        high_risk = df[df.get('probability', 0) > 50].drop_duplicates(subset=['lat_grid', 'lon_grid'])
        for _, z in high_risk.iterrows():
            folium.Circle([z['lat_grid'], z['lon_grid']], radius=300000, color='red', fill=True, fill_opacity=0.2, weight=0).add_to(m)

        for _, row in df.iterrows():
            mag = row['mag']
            color = '#9900cc' if row['is_fake'] else get_marker_color(mag)
            folium.Circle([row['lat'], row['lon']], radius=(mag**4)*20, color=color, weight=1, fill=True, fill_color=color, fill_opacity=0.1).add_to(m)
            folium.CircleMarker([row['lat'], row['lon']], radius=4, color=color, fill=True, fill_color=color, fill_opacity=1.0, 
                                popup=f"{row['place']} ({mag})", tooltip=f"Mag {mag}").add_to(m)
        st_folium(m, height=600, width=None)

    with tab2:
        st.subheader("Statistics by Country")
        stats = df.groupby('country').agg({'mag': 'count', 'probability': 'max'}).reset_index().sort_values('mag', ascending=False)
        st.dataframe(stats, hide_index=True)
