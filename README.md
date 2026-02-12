# 🌍 Global Earthquake Monitor & AI Risk Prediction

**Global Earthquake Monitor** คือระบบเฝ้าระวังแผ่นดินไหวทั่วโลกแบบ Real-time ที่มาพร้อมกับระบบ **AI Prediction Logic** เพื่อประเมินความเสี่ยงในการเกิดเหตุซ้ำหรือรุนแรงขึ้นในแต่ละพื้นที่

ระบบแสดงผลบน Dashboard ที่สวยงามด้วยแผนที่ **Interactive Map** พร้อมเอฟเฟกต์คลื่นกระแทก (Shockwaves) และมีระบบแจ้งเตือนภัยผ่าน **LINE Notify** และ **Discord** ที่ฉลาดขึ้น (ไม่แจ้งเตือนซ้ำเมื่อ Refresh หน้าจอ)



## ✨ ฟีเจอร์หลัก (Key Features)

### 📊 1. Real-time Monitoring & Analytics
* **Global Data:** ดึงข้อมูลแผ่นดินไหวล่าสุด (M2.5+) จาก **USGS** ทั่วโลก
* **Country Stats:** แยกสถิติรายประเทศ/ภูมิภาค แสดงจำนวนครั้งและความรุนแรงสูงสุด
* **Duplicate Prevention:** มีระบบ `History Log` จำ ID ของเหตุการณ์ที่แจ้งเตือนไปแล้ว ป้องกันการแจ้งเตือนซ้ำเมื่อ Reload หน้าเว็บ

### 🤖 2. AI Risk Prediction (ระบบประเมินความเสี่ยง)
* **Grid-based Analysis:** แบ่งโลกออกเป็นตาราง (Grid 5x5 องศา) เพื่อวิเคราะห์ความหนาแน่นของกิจกรรมแผ่นดินไหว
* **Risk Score:** คำนวณความเสี่ยงเป็น % โดยใช้สูตร:
  > $Risk = (Frequency \times 3) + (MaxMagnitude^2)$
* **Heatmap:** แสดงพื้นที่เสี่ยงสูง (High Risk Zones) ด้วยวงกลมสีแดงขนาดใหญ่บนแผนที่

### 🗺️ 3. Visualizations
* **Shockwaves:** แสดงวงคลื่นกระแทก 2 ชั้น (วงนอก/วงใน) ขนาดแปรผันตามความรุนแรง ($Radius \propto Magnitude^4$)
* **Interactive Map:** แผนที่ Dark Mode สวยงาม ซูมเข้า-ออกและคลิกดูรายละเอียดได้

### 🔔 4. Smart Alerts
* **Channels:** รองรับ **LINE Notify** และ **Discord Webhook**
* **Content:** ส่งข้อความแจ้งเตือนพร้อม ระดับความรุนแรง, สถานที่, เวลา, % ความเสี่ยง, และลิงก์ Google Maps
* **Config:** บันทึกการตั้งค่า Token ต่างๆ ลงไฟล์ `config.json` อัตโนมัติ

## 🛠️ เทคโนโลยีที่ใช้ (Tech Stack)

* [Python 3.x](https://www.python.org/)
* [Streamlit](https://streamlit.io/) - Web Framework
* [Folium](https://python-visualization.github.io/folium/) - Advanced Mapping
* [Pandas](https://pandas.pydata.org/) - Data Analysis
* [Requests](https://pypi.org/project/requests/) - API Integration

## 🚀 วิธีการติดตั้ง (Installation)

1.  **Clone หรือดาวน์โหลดโปรเจกต์**
    ```bash
    git clone [https://github.com/yourusername/earthquake-monitor.git](https://github.com/yourusername/earthquake-monitor.git)
    cd earthquake-monitor
    ```

2.  **สร้าง Virtual Environment**
    ```bash
    # Windows
    python -m venv venv
    venv\Scripts\activate

    # macOS/Linux
    python3 -m venv venv
    source venv/bin/activate
    ```

3.  **ติดตั้ง Library**
    ```bash
    pip install -r requirements.txt
    ```

## ▶️ วิธีใช้งาน (Usage)

รันคำสั่ง:

```bash
streamlit run app.py
```
มื่อรันสำเร็จ เว็บเบราว์เซอร์จะเปิดขึ้นมาที่ http://localhost:8501

⚙️ การตั้งค่าระบบ (Configuration)
ที่แถบด้านซ้าย (Sidebar) คุณสามารถตั้งค่าการแจ้งเตือนได้:

LINE Notify: ใส่ Token จาก LINE Notify

Discord Webhook: ใส่ URL จาก Discord Server Integrations

Save Settings: กดบันทึกเพื่อเก็บค่าลงไฟล์ config.json (ครั้งหน้าไม่ต้องกรอกใหม่)

📂 ไฟล์สำคัญในระบบ
config.json: เก็บ Token และการตั้งค่า (สร้างอัตโนมัติ)

alert_history.json: เก็บ ID ของแผ่นดินไหวที่แจ้งเตือนไปแล้ว เพื่อป้องกันการแจ้งซ้ำ (สร้างอัตโนมัติ)

🧪 การทดสอบ (Simulation & Reset)
🚨 Simulate Risk Event: จำลองเหตุการณ์แผ่นดินไหวรุนแรงเพื่อทดสอบการคำนวณ Risk และการแจ้งเตือน

🗑️ Reset All History: ล้างประวัติการแจ้งเตือนทั้งหมด (ทำให้เมื่อ Refresh หน้า ระบบจะแจ้งเตือนข้อมูลเก่าซ้ำ) ใช้สำหรับทดสอบเท่านั้น

⚠️ หมายเหตุ
Prediction Logic: ค่าความเสี่ยง (Risk %) เป็นการคำนวณทางสถิติจากข้อมูลในอดีต 24 ชม. ไม่ใช่การทำนายอนาคตที่แม่นยำ 100%

Security: ไฟล์ config.json เก็บข้อมูลส่วนตัว ห้ามแชร์ไฟล์นี้สู่สาธารณะ

Developed with ❤️ using Streamlit & Python
