# 🌍 Earthquake Monitor Dashboard (Real-time & Alerts)

**Earthquake Monitor** คือเว็บแอปพลิเคชันสำหรับเฝ้าระวังและติดตามสถานการณ์แผ่นดินไหวทั่วโลกแบบ Real-time พัฒนาด้วยภาษา **Python** และ **Streamlit**

ระบบดึงข้อมูลสดจาก **USGS** แสดงผลบนแผนที่แบบ Interactive พร้อมเอฟเฟกต์คลื่นกระแทก (Shockwaves) เพื่อแสดงรัศมีผลกระทบ และมีระบบแจ้งเตือนภัยผ่าน **LINE Notify** และ **Discord** โดยอัตโนมัติ



## ✨ ฟีเจอร์หลัก (Key Features)

* **📊 Real-time Data:** ดึงข้อมูลแผ่นดินไหวล่าสุด (M2.5+) จาก USGS ทุกครั้งที่รีเฟรช
* **🗺️ Interactive Map:** แผนที่โลกที่ซูมเข้า-ออกได้ พร้อมจุดสีแบ่งตามความรุนแรง
* **🌊 Shockwave Visuals:** แสดงวงคลื่นกระแทก 2 ชั้น (วงนอก/วงใน) ขนาดแปรผันตามความรุนแรง (Magnitude)
* **🔔 Instant Alerts:** แจ้งเตือนผ่าน **LINE Notify** และ **Discord Webhook** (ส่งข้อความ + ลิงก์ Google Maps)
* **⚙️ Auto-Save Settings:** บันทึก Token และการตั้งค่าลงไฟล์ `config.json` อัตโนมัติ ไม่ต้องกรอกใหม่ทุกครั้ง
* **🧪 Simulation Mode:** โหมดจำลองเหตุการณ์เพื่อทดสอบระบบแจ้งเตือนและดูเอฟเฟกต์บนแผนที่

## 🛠️ เทคโนโลยีที่ใช้ (Tech Stack)

* [Python 3.x](https://www.python.org/)
* [Streamlit](https://streamlit.io/) - Web Framework
* [Folium](https://python-visualization.github.io/folium/) - Interactive Maps
* [Pandas](https://pandas.pydata.org/) - Data Manipulation
* [Requests](https://pypi.org/project/requests/) - HTTP Client

## 🚀 วิธีการติดตั้ง (Installation)

1.  **Clone หรือดาวน์โหลดโปรเจกต์**
    ```bash
    git clone [https://github.com/yourusername/earthquake-monitor.git](https://github.com/yourusername/earthquake-monitor.git)
    cd earthquake-monitor
    ```

2.  **สร้าง Virtual Environment (แนะนำ)**
    ```bash
    # Windows
    python -m venv venv
    venv\Scripts\activate

    # macOS/Linux
    python3 -m venv venv
    source venv/bin/activate
    ```

3.  **ติดตั้ง Library ที่จำเป็น**
    ```bash
    pip install -r requirements.txt
    ```

## ▶️ วิธีใช้งาน (Usage)

รันคำสั่งต่อไปนี้ใน Terminal:

```bash
streamlit run app.py
