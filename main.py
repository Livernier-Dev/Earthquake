import streamlit as st
import requests
import pandas as pd
import datetime
import folium
import random
import json
import os
from streamlit_folium import st_folium

# --- 1. ตั้งค่าหน้าเว็บ ---
st.set_page_config(page_title="Earthquake Monitor", layout="wide", page_icon="🌍")
st.title("🌍 ศูนย์เฝ้าระวังแผ่นดินไหว (LINE & Discord Only)")

# --- 2. ระบบจัดการ Config (Load/Save) ---
CONFIG_FILE = "config.json"

def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except: return {}
    return {}

def save_config(config_data):
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config_data, f, ensure_ascii=False, indent=4)
        return True
    except: return False

saved_config = load_config()

# --- 3. ฟังก์ชันแจ้งเตือน (ตัด Email ออกแล้ว) ---

def send_line_notify(token, data):
    url = 'https://notify-api.line.me/api/notify'
    headers = {'Authorization': f'Bearer {token}'}
    msg = (
        f"\n🔴 ALERT: แผ่นดินไหว!\n"
        f"จุดเกิดเหตุ: {data['place']}\n"
        f"ความแรง: {data['mag']:.1f}\n"
        f"เวลา: {data['time']}\n"
        f"พิกัด: {data['lat']:.4f}, {data['lon']:.4f}\n"
        f"Maps: http://maps.google.com/?q={data['lat']},{data['lon']}"
    )
    try:
        requests.post(url, headers=headers, data={'message': msg})
        return True
    except: return False

def send_discord_webhook(webhook_url, data):
    color = 15158332 if data['mag'] >= 6.0 else 3066993
    embed = {
        "username": "Earthquake Bot",
        "embeds": [{
            "title": f"🚨 Earthquake Mag {data['mag']:.1f}",
            "description": f"**Location:** {data['place']}\n**Time:** {data['time']}",
            "color": color,
            "fields": [
                {"name": "Magnitude", "value": f"{data['mag']:.1f}", "inline": True},
                {"name": "Coordinates", "value": f"{data['lat']:.4f}, {data['lon']:.4f}", "inline": True}
            ],
            "url": f"http://maps.google.com/?q={data['lat']},{data['lon']}"
        }]
    }
    try:
        requests.post(webhook_url, json=embed)
        return True
    except: return False

# --- 4. Main Data Logic ---
@st.cache_data(ttl=300)
def get_data():
    try:
        return requests.get("https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/2.5_day.geojson", timeout=10).json()
    except: return None

def get_marker_color(mag):
    if mag < 4: return 'green'      # เขียว (เบา)
    elif mag < 6: return 'orange'   # ส้ม (ปานกลาง)
    elif mag < 7.5: return 'red'    # แดง (แรง)
    else: return 'darkred'          # แดงเข้ม (วิกฤต)

if 'fake_data' not in st.session_state: st.session_state.fake_data = []
if 'alerted_ids' not in st.session_state: st.session_state.alerted_ids = set()

# --- 5. Sidebar & Settings ---
with st.sidebar:
    st.header("⚙️ ตั้งค่าการแจ้งเตือน")
    
    with st.form("settings_form"):
        # LINE Section
        st.subheader("🔔 LINE Notify")
        use_line = st.checkbox("เปิดใช้ LINE", value=saved_config.get("use_line", False))
        line_token = st.text_input("LINE Token", value=saved_config.get("line_token", ""), type="password")

        st.divider()
        
        # Discord Section
        st.subheader("👾 Discord Webhook")
        use_discord = st.checkbox("เปิดใช้ Discord", value=saved_config.get("use_discord", False))
        discord_url = st.text_input("Webhook URL", value=saved_config.get("discord_url", ""), type="password")

        # Save Button
        if st.form_submit_button("💾 บันทึกการตั้งค่า"):
            new_config = {
                "use_line": use_line, 
                "line_token": line_token,
                "use_discord": use_discord, 
                "discord_url": discord_url
            }
            if save_config(new_config):
                st.success("บันทึกเรียบร้อย!")
                saved_config = new_config

    st.divider()
    st.header("🧪 Simulation Zone")
    
    # ปุ่มจำลองเหตุการณ์
    if st.button("🚨 จำลองเหตุการณ์ (Test Map)", type="primary"):
        sim_data = {
            "id": f"sim_{int(datetime.datetime.now().timestamp())}",
            "place": "SIMULATION TEST ZONE",
            "mag": random.uniform(6.5, 9.0),
            "time": datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "lat": random.uniform(-20, 20),
            "lon": random.uniform(90, 140),
            "is_fake": True
        }
        st.session_state.fake_data.append(sim_data)
        st.toast("สร้างจุดจำลองบนแผนที่แล้ว...", icon="🗺️")

    # ปุ่มล้างข้อมูล
    if st.button("🗑️ Reset Map"):
        st.session_state.fake_data = []
        st.session_state.alerted_ids = set()
        st.rerun()

# --- 6. Processing & Visualization ---
raw = get_data()
all_data = []
if raw:
    for f in raw['features']:
        all_data.append({
            "id": f['id'], "place": f['properties']['place'], "mag": f['properties']['mag'],
            "time": datetime.datetime.fromtimestamp(f['properties']['time']/1000).strftime('%Y-%m-%d %H:%M:%S'),
            "lat": f['geometry']['coordinates'][1], "lon": f['geometry']['coordinates'][0], "is_fake": False
        })
all_data.extend(st.session_state.fake_data)
df = pd.DataFrame(all_data)

if not df.empty:
    # Alert Logic (Text Only)
    alerts = df[df['mag'] >= 5.0]
    for _, row in alerts.iterrows():
        if row['id'] not in st.session_state.alerted_ids:
            payload = row.to_dict()
            
            # Send LINE
            if saved_config.get("use_line") and saved_config.get("line_token"):
                send_line_notify(saved_config["line_token"], payload)
            
            # Send Discord
            if saved_config.get("use_discord") and saved_config.get("discord_url"):
                send_discord_webhook(saved_config["discord_url"], payload)
            
            st.session_state.alerted_ids.add(row['id'])
            st.toast(f"New Alert Sent: {row['place']}", icon="🔔")

    # --- ส่วนแผนที่ (Interactive Map with Visuals) ---
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.subheader(f"📍 แผนที่แสดงจุดเกิดเหตุ ({len(df)} จุด)")
        
        # Center Map ไปที่จุดล่าสุด
        if not df.empty:
            center_lat, center_lon = df.iloc[0]['lat'], df.iloc[0]['lon']
        else:
            center_lat, center_lon = 20, 0
            
        m = folium.Map(location=[center_lat, center_lon], zoom_start=3, tiles="CartoDB positron")

        for _, row in df.iterrows():
            mag = row['mag']
            # เลือกสี
            if row['is_fake']:
                color = '#9900cc' # สีม่วง (Simulation)
            else:
                color = get_marker_color(mag)

            # --- เพิ่มวงคลื่นกระแทก (Shockwaves) ---
            # 1. วงนอก (รัศมีผลกระทบกว้าง - จางๆ)
            folium.Circle(
                location=[row['lat'], row['lon']],
                radius=(mag ** 4) * 50, 
                color=color, weight=1, fill=True, fill_color=color, fill_opacity=0.08 
            ).add_to(m)

            # 2. วงใน (พื้นที่สั่นสะเทือนหลัก - เข้มขึ้น)
            folium.Circle(
                location=[row['lat'], row['lon']],
                radius=(mag ** 4) * 10, 
                color=color, weight=1, fill=True, fill_color=color, fill_opacity=0.3 
            ).add_to(m)

            # 3. จุดตรงกลาง (Marker)
            popup_html = f"""
            <b>{row['place']}</b><br>
            Mag: {mag:.1f}<br>
            Time: {row['time']}
            """
            folium.CircleMarker(
                [row['lat'], row['lon']],
                radius=4, color='black', weight=1, fill=True, fill_color=color, fill_opacity=1.0,
                popup=folium.Popup(popup_html, max_width=200),
                tooltip=f"Mag {mag:.1f}"
            ).add_to(m)

        # แสดงแผนที่
        st_folium(m, height=600, width=None)

    with col2:
        st.subheader("📋 รายการล่าสุด")
        st.dataframe(
            df[['mag','place','time']],
            height=600,
            hide_index=True,
            column_config={
                "mag": st.column_config.NumberColumn("ขนาด", format="%.1f ⭐"),
                "place": "สถานที่",
                "time": "เวลา"
            }
        )