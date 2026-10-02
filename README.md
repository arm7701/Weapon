# Weapon 3D Tactical Strike & Blast Simulation System 💥🌍
> ระบบจำลองอาวุธและวิเคราะห์รัศมีคลื่นแรงอัดระเบิด 3 มิติเชิงยุทธวิธี (3D Tactical Blast Radius Simulation & Video Export Engine) พัฒนาด้วย **CesiumJS**, **PySide6 (QtWebEngine)**, **Pillow**, **NumPy** และ **OpenCV**

---

## 🎯 จุดเด่นและฟังก์ชันการทำงาน (Key Features)

1. **3D Interactive Tactical Globe (ลูกโลกและแผนที่ยุทธวิธี 3 มิติ):**
   - แสดงผลภูมิประเทศระดับโลก (Cesium World Terrain) และอาคาร 3 มิติ (OSM 3D Buildings)
   - นำทาง ควบคุมมุมมอง หมุน ซูม วัดระยะ และเลือกตำแหน่งพิกัดเป้าหมายได้อย่างแม่นยำ

2. **Multi-Tier Tactical Blast Radius Calculation (การคำนวณรัศมีระเบิด 3 ชั้น):**
   - **🔴 Lethal Fireball & Blast Wave (Red Zone):** รัศมีลูกไฟและการทำลายล้างสังหาร 100%
   - **🟠 Severe Overpressure & Shrapnel (Orange Zone):** รัศมีแรงอัดคลื่นกระแทกโครงสร้างและสะเก็ดรุนแรง
   - **🟡 Fragmentation & Hazard Zone (Yellow Zone):** รัศมีสะเก็ดระเบิดรอบนอก
   - แสดงผลทั้งวงแหวนแนบผิวดิน (Terrain-Clamped Polyline) และโดมครึ่งทรงกลม 3 มิติ (3D Semi-Transparent Domes)

3. **Multi-Pin Cluster Shockwave Looping (อนิเมชันคลื่นแรงอัดระเบิดแบบวนลูป):**
   - วางเป้าหมายการโจมตีได้หลายจุดพร้อมกัน (Multi-Pin Strikes)
   - อนิเมชันคลื่นแรงอัดระเบิดแบบกระจายตัวพร้อมกันทุกจุดในกลุ่ม (Cluster Blast Wave)
   - โหมดจำลองแบบวนลูปต่อเนื่อง (`🔁 LOOP: ON`) สำหรับประเมินความครอบคลุมของพื้นที่เป้าหมาย

4. **360° Cinematic Orbital MP4 Video Export (การบันทึกและส่งออกวิดีโอ 360°):**
   - รองรับโหมดการบันทึก 2 รูปแบบ:
     - **โหมด Cluster / Centroid Orbit:** กล้องหมุนรอบจุดศูนย์กลาง 360° อย่างนุ่มนวล พร้อมแสดงรัศมีระเบิดขยายตัวแบบวนลูป
     - **โหมด Sequential Target Flight:** กล้องบินตรวจการณ์ทีละจุดตามลำดับ ก่อนซูมออกให้เห็นภาพรวมทั้งยุทธบริเวณ
   - ระบบเรนเดอร์ HUD ข้อมูลภารกิจ (Mission Info Overlay) ฝังลงในวิดีโอ MP4 อัตโนมัติด้วย OpenCV

5. **3D Object & Mesh Tools (เครื่องมือสร้างและจัดการวัตถุ 3 มิติ):**
   - เครื่องมือวาดรูปทรง 3 มิติ (Box, Cylinder, Ellipsoid, Polygon Wall) บนแผนที่
   - รองรับการนำเข้าไฟล์โมเดล 3 มิติภายนอก (.STL)
   - ส่งออกข้อมูลเป็นโครงข่าย 3D Mesh (.OBJ / .STL) สำหรับนำไปคำนวณพลศาสตร์ของไหล (CFD / OpenFOAM)
   - ระบบจำลองความเสียหายและการพังทลายของอาคารสิ่งปลูกสร้างรอบจุดระเบิด

---

## 🛠️ ความต้องการของระบบและไลบรารี่ (System Requirements & Dependencies)

- **Python:** 3.10 หรือใหม่กว่า
- **ระบบปฏิบัติการ:** Windows 10/11, Linux, หรือ macOS
- **การเชื่อมต่ออินเทอร์เน็ต:** จำเป็นสำหรับการโหลด CesiumJS CDN และสตรีมข้อมูล 3D Terrain / Satellite Imagery

### ไลบรารี่ที่จำเป็น (`requirements.txt`):
| ไลบรารี่ | เวอร์ชันขั้นต่ำ | หน้าที่การทำงาน |
| :--- | :--- | :--- |
| **`PySide6`** | `>= 6.5.0` | Desktop GUI และ Chromium WebEngine สำหรับแสดงผล Cesium 3D |
| **`Pillow`** | `>= 10.0.0` | การประมวลผลกราฟิกและเรนเดอร์ HUD ตัวหนังสือภาษาไทย/อังกฤษ |
| **`numpy`** | `>= 1.24.0` | การคำนวณเมทริกซ์และพิกัดเชิงเรขาคณิต |
| **`opencv-python`** | `>= 4.8.0` | การเข้ารหัสและบันทึกวิดีโอความละเอียดสูง MP4 (H.264 / FFMPEG) |

---

## 🚀 วิธีการติดตั้งและเริ่มต้นใช้งาน (Installation & Quick Start)

### 1. โคลนคลังโค้ด (Clone Repository)
```bash
git clone https://github.com/arm7701/Weapon.git
cd Weapon
```

### 2. สร้าง Virtual Environment (แนะนำ)
```bash
# สำหรับ Windows
python -m venv venv
.\venv\Scripts\activate

# สำหรับ Linux / macOS
python3 -m venv venv
source venv/bin/activate
```

### 3. ติดตั้งไลบรารี่ (Install Dependencies)
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. เปิดใช้งานโปรแกรม (Run Application)
สามารถรันผ่านสคริปต์หลักได้ทันที:
```bash
python was_test7.py
```
หรือรันผ่าน Launcher:
```bash
python main.py
```
*(สำหรับ Windows สามารถดับเบิลคลิกที่ไฟล์ `run.bat` ได้โดยตรง)*

---

## 📁 โครงสร้างโปรเจกต์ (Project Structure)

```text
Weapon/
├── was_test7.py          # โปรแกรมหลัก (PySide6 GUI + Cesium 3D Interactive Engine)
├── main.py               # Launcher entry point สะดวกสำหรับการเรียกใช้งาน
├── requirements.txt      # รายการไลบรารี่ Python ที่ต้องติดตั้ง
├── run.bat               # สคริปต์คลิกรันด่วนสำหรับ Windows
├── 1.stl                 # ตัวอย่างไฟล์โมเดล 3D CAD สำหรับทดสอบการวางวัตถุ
├── cesium_model.stl      # ตัวอย่างไฟล์โมเดล 3D STL สำหรับทดสอบ
├── .gitignore            # กำหนดไฟล์ที่ไม่ต้องส่งขึ้น Git (venv, แคช, วิดีโอชั่วคราว)
└── README.md             # คู่มือและเอกสารประกอบโปรเจกต์
```

---

## 🎮 การควบคุมและปุ่มคำสั่งสำคัญ (Interface Controls)

| แถบคำสั่ง | คำอธิบาย |
| :--- | :--- |
| **📍 PIN MODE** | โหมดคลิกบนแผนที่เพื่อวางจุดหมุดเป้าหมายระเบิด (พิกัด ละติจูด, ลองจิจูด, ความสูง) |
| **💥 REPLAY / ANIM** | เล่นซ้ำอนิเมชันลูกไฟและคลื่นกระแทก ณ จุดเป้าหมาย |
| **🔁 LOOP: ON/OFF** | เปิด/ปิด โหมดระเบิดวนลูปต่อเนื่องสำหรับทุกจุดพร้อมกัน |
| **🎥 EXPORT MP4** | ส่งออกวิดีโอความละเอียดสูง 360° รอบจุดระเบิด พร้อมเลือกโหมดบินตรวจการณ์ |
| **🌐 DOME 3D** | เปิด/ปิด การแสดงผลโดมรัศมีระเบิดทรงกลม 3 มิติ |
| **⚡ แสดงทันที** | สลับกล้องให้มองภาพรวมทุกจุดและเริ่มอนิเมชันทันทีระหว่างการบันทึกวิดีโอ |
| **🔧 3D TOOLS** | เปิดแถบเครื่องมือสำหรับสร้างอาคาร รูปทรงเรขาคณิต และนำเข้าไฟล์ STL |

---

## 📄 License & Credits
- พัฒนาสำหรับงานวิเคราะห์และจำลองสถานการณ์ทางยุทธวิธี
- ขับเคลื่อนด้วย [CesiumJS](https://cesium.com/cesiumjs/) และ [Qt for Python (PySide6)](https://wiki.qt.io/Qt_for_Python)
