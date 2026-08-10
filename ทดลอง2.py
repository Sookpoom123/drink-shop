import streamlit as st
import pandas as pd
import sqlite3
import hashlib
from datetime import date

# --- ตั้งค่าหน้าตาเว็บไซต์ ---
st.set_page_config(
    page_title="ร้านน้ำสร้างตัว 🧋", 
    page_icon="🧋", 
    layout="centered"
)

DB_FILE = "sales_data.db"
ADMIN_SECRET_KEY = "3475"  # 🔑 รหัสลับสำหรับแต่งตั้ง Admin
PEARL_PRICE = 5.0           # 🧋 ราคาไข่มุก
PEARL_COST = 1.0            # 🧋 ต้นทุนไข่มุก

# --- รายการเมนูทั้งหมด (68 เมนู) ---
DEFAULT_MENU = {
    # --- ชาใส / ชาผลไม้ / กาแฟ / นมสดรสต่างๆ ---
    "ชาดำเย็น": {"cost": 6.61, "price": 19},
    "ชามะนาว": {"cost": 7.65, "price": 19},
    "ชาเขียวมะนาว": {"cost": 8.45, "price": 19},
    "ชาเขียวใส": {"cost": 7.41, "price": 19},
    "โอเลี้ยง": {"cost": 6.07, "price": 19},
    "โกโก้": {"cost": 13.11, "price": 25},
    "โอวัลติน": {"cost": 10.85, "price": 25},
    "เนสกาแฟ": {"cost": 15.63, "price": 30},
    "กาแฟโบราณ": {"cost": 10.51, "price": 25},
    "นมชมพู": {"cost": 10.87, "price": 25},
    "ผลไม้โซดา": {"cost": 10.47, "price": 19},
    "น้ำแดงโซดา": {"cost": 10.88, "price": 19},
    "แดงมะนาวโซดา": {"cost": 11.92, "price": 25},
    "มะนาวโซดา": {"cost": 9.85, "price": 19},
    "นมสดบราวซูการ์": {"cost": 11.20, "price": 25},
    "นมสดสีขาว": {"cost": 12.07, "price": 25},
    "นมสดคาราเมล": {"cost": 14.55, "price": 30},
    "นมสดวนิลา": {"cost": 14.55, "price": 30},
    "นมสดน้ำผึ้ง": {"cost": 13.67, "price": 25},
    "โยเกิร์ตผลไม้": {"cost": 11.36, "price": 25},
    "มันม่วงนมสด": {"cost": 13.76, "price": 25},
    "มะพร้าวนมสด": {"cost": 12.76, "price": 25},
    "สตรอเบอร์รี่นมสด": {"cost": 11.49, "price": 25},
    "เผือกนมสด": {"cost": 11.49, "price": 25},
    "กล้วยนมสด": {"cost": 11.49, "price": 25},
    "แคนตาลูปนมสด": {"cost": 11.49, "price": 25},
    "ช็อคโกแลตนมสด": {"cost": 14.64, "price": 25},

    # --- เมนูปั่น ---
    "ชาแดงปั่น": {"cost": 14.72, "price": 35},
    "ชาเขียวปั่น": {"cost": 15.73, "price": 35},
    "ชาไต้หวันปั่น": {"cost": 13.04, "price": 35},
    "ชานมโกโก้ปั่น": {"cost": 15.07, "price": 35},
    "ชานมกาแฟ": {"cost": 16.33, "price": 35},
    "ชานมโอวัลติน": {"cost": 13.94, "price": 35},
    "ชานมน้ำผึ้ง": {"cost": 17.58, "price": 35},
    "ชานมลิ้นจี่": {"cost": 15.69, "price": 35},
    "ชานมแอปเปิ้ล": {"cost": 15.69, "price": 35},
    "ชาแชมเมล่อน(แคนตาลูป)": {"cost": 15.69, "price": 35},
    "ชานมสตรอเบอร์รี่": {"cost": 15.69, "price": 35},
    "โกโก้ปั่น": {"cost": 18.16, "price": 35},
    "เนสกาแฟปั่น": {"cost": 21.94, "price": 45},
    "โอวัลตินปั่น": {"cost": 14.77, "price": 35},
    "นมชมพูปั่น": {"cost": 14.06, "price": 35},
    "นมสดปั่น": {"cost": 18.35, "price": 35},
    "วนิลานมสดปั่น": {"cost": 25.19, "price": 45},
    "คาราเมลนมสดปั่น": {"cost": 25.19, "price": 45},
    "นมสดน้ำผึ้งปั่น": {"cost": 23.43, "price": 45},
    "นมสดบราวซูการ์ปั่น": {"cost": 20.58, "price": 45},
    "ชาไต้หวันบราวซูการ์ปั่น": {"cost": 14.88, "price": 45},
    "มัทฉะนมสดปั่น": {"cost": 30.66, "price": 55},
    "มะพร้าวนมสดปั่น": {"cost": 17.17, "price": 35},
    "มันม่วงนมสดปั่น": {"cost": 18.13, "price": 45},
    "ผงสตรอเบอร์รี่": {"cost": 14.94, "price": 35},
    "ผงแคนตาลูป": {"cost": 14.77, "price": 35},
    "ผงกล้วย": {"cost": 14.77, "price": 35},
    "ผงเผือก": {"cost": 15.25, "price": 35},

    # --- ชานม / ชาเขียว / ชานมเย็น ---
    "ชานมไต้หวัน": {"cost": 11.12, "price": 19},
    "ชานมผลไม้": {"cost": 11.89, "price": 25},
    "ชานมโกโก้": {"cost": 12.13, "price": 25},
    "ชานมกาแฟ": {"cost": 12.76, "price": 25},
    "ชานมโอวัลติน": {"cost": 11.57, "price": 25},
    "ชานมคาราเมล": {"cost": 14.03, "price": 30},
    "ชานมวนิลา": {"cost": 14.03, "price": 30},
    "ชานมน้ำผึ้ง": {"cost": 13.15, "price": 25},
    "ชานมไต้หวันบราวซูการ์": {"cost": 11.96, "price": 25},
    "ชานมเผือก": {"cost": 13.20, "price": 25},
    "ชาผลไม้ใส": {"cost": 8.03, "price": 19},
    "ชาเย็น(ชานมไทย)": {"cost": 11.58, "price": 25},
    "ชาเขียว(ชาเขียวนม)": {"cost": 12.38, "price": 25},
    "ชาเขียวน้ำผึ้งมะนาว": {"cost": 12.11, "price": 25},
    "ชาแดงน้ำผึ้งมะนาว": {"cost": 11.31, "price": 25},
    "น้ำผึ้งมะนาว": {"cost": 10.07, "price": 19},

    # --- เมนูบ๊วย ---
    "ชาลูกบ๊วย": {"cost": 9.03, "price": 24},
    "น้ำลูกบ๊วย": {"cost": 6.95, "price": 24},
    "น้ำลูกบ๊วยโซดา": {"cost": 11.94, "price": 24},
    "น้ำผึ้งมะนาวลูกบ๊วย": {"cost": 12.79, "price": 24},
    "น้ำแดงลูกบ๊วย": {"cost": 9.18, "price": 24},
    "น้ำแดงโซดาลูกบ๊วย": {"cost": 14.01, "price": 24},
    "น้ำลูกบ๊วยปั่น": {"cost": 9.70, "price": 29},
}

# --- ฟังก์ชันจัดการระบบความปลอดภัย ---
def make_hashes(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

# --- ส่วนจัดการฐานข้อมูล (SQLite) ---
def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS sales (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sale_date TEXT,
            item_name TEXT,
            qty INTEGER,
            total_price REAL,
            total_cost REAL,
            total_profit REAL,
            payment_method TEXT
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password TEXT,
            role TEXT DEFAULT 'user'
        )
    ''')
    try:
        c.execute("ALTER TABLE users ADD COLUMN role TEXT DEFAULT 'user'")
    except sqlite3.OperationalError:
        pass

    c.execute("UPDATE users SET role = 'admin' WHERE username = 'admin'")
    conn.commit()
    conn.close()

def add_user(username, password, role='user'):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    try:
        c.execute('INSERT INTO users (username, password, role) VALUES (?, ?, ?)', 
                  (username, make_hashes(password), role))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        conn.close()
        return False

def login_user(username, password):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('SELECT username, role FROM users WHERE username = ? AND password = ?', 
              (username, make_hashes(password)))
    data = c.fetchone()
    conn.close()
    return data

def get_all_users():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('SELECT username, role FROM users')
    users = c.fetchall()
    conn.close()
    return users

def delete_user(username):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('DELETE FROM users WHERE username = ?', (username,))
    conn.commit()
    conn.close()

def add_sale(sale_date, item_name, qty, total_price, total_cost, total_profit, payment_method):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
        INSERT INTO sales (sale_date, item_name, qty, total_price, total_cost, total_profit, payment_method)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (str(sale_date), item_name, qty, total_price, total_cost, total_profit, payment_method))
    conn.commit()
    conn.close()

def get_sales():
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query("SELECT * FROM sales", conn)
    conn.close()
    return df

def delete_sale_by_id(record_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("DELETE FROM sales WHERE id = ?", (record_id,))
    conn.commit()
    conn.close()

# เรียกใช้งานฐานข้อมูล
init_db()

# ตัวแปรสถานะการเข้าสู่ระบบ
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = ""
if "role" not in st.session_state:
    st.session_state.role = "user"

# บังคับใช้เมนู 68 รายการเสมอ
if "menu" not in st.session_state or len(st.session_state.menu) != len(DEFAULT_MENU):
    st.session_state.menu = DEFAULT_MENU.copy()

# ==========================================
# 🎨 ปรับแต่งธีมสีสดใส (CSS Overrides)
# ==========================================
st.markdown(
    """
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    /* 1. พื้นหลังหลักทั้งหน้าเว็บเป็นสีไล่เฉดสดใส */
    .stApp {
        background: linear-gradient(135deg, #FF9A9E 0%, #FECFEF 50%, #A1C4FD 100%) !important;
    }

    /* 2. พื้นหลังแถบข้าง Sidebar */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #FFE29F 0%, #FFAE34 100%) !important;
    }

    /* 3. การ์ดหัวข้อหลัก */
    .header-card {
        background: linear-gradient(135deg, #FFF6B7 0%, #F68084 100%) !important;
        padding: 25px;
        border-radius: 24px;
        box-shadow: 0 10px 25px rgba(255, 71, 126, 0.2);
        border: 3px solid #FF5252;
        text-align: center;
        margin-bottom: 20px;
    }

    /* 4. กล่องเนื้อหาและฟอร์มสีพาสเทลสดใส */
    div[data-testid="stForm"], div[data-testid="stExpander"], div[data-testid="stVerticalBlock"] > div[style*="background-color"] {
        background-color: #FFF9C4 !important;
        border-radius: 18px !important;
        border: 2px solid #FFD54F !important;
        box-shadow: 0 4px 15px rgba(0,0,0,0.05) !important;
    }

    /* 5. ปุ่มกดสีส้มชมพูสะดุดตา */
    div.stButton > button, div.stFormSubmitButton > button {
        background: linear-gradient(90deg, #FF512F 0%, #DD2476 100%) !important;
        color: white !important;
        border-radius: 14px !important;
        font-weight: bold !important;
        font-size: 16px !important;
        height: 50px !important;
        border: none !important;
        box-shadow: 0 4px 15px rgba(221, 36, 118, 0.4) !important;
        transition: all 0.3s ease !important;
    }
    div.stButton > button:hover, div.stFormSubmitButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(221, 36, 118, 0.6) !important;
    }

    /* 6. ช่องกรอกข้อมูล */
    div[data-baseweb="input"] {
        background-color: #FFFFFF !important;
        border-radius: 12px !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# ==========================================
# 1. หน้าเข้าสู่ระบบ / สมัครสมาชิก
# ==========================================
if not st.session_state.logged_in:

    st.markdown(
        """
        <div class="header-card">
            <img src="https://cdn-icons-png.flaticon.com/512/3081/3081162.png" width="95" style="margin-bottom: 8px;">
            <h1 style="color: #C2185B; font-size: 30px; font-weight: 900; margin: 0; text-shadow: 1px 1px 2px #FFF;">ร้านน้ำสร้างตัว 🧋</h1>
            <p style="color: #880E4F; font-size: 15px; font-weight: bold; margin-top: 5px;">ระบบบันทึกยอดขาย & สรุปกำไรประจำวัน</p>
        </div>
        """, 
        unsafe_allow_html=True
    )
    
    col1, col2, col3 = st.columns([0.1, 2, 0.1])
    
    with col2:
        auth_tab1, auth_tab2 = st.tabs(["🔑 เข้าสู่ระบบ (Login)", "📝 สมัครสมาชิก (Register)"])

        with auth_tab1:
            with st.container():
                st.write("")
                login_user_input = st.text_input("👤 ชื่อผู้ใช้งาน (Username)", key="login_user")
                login_pass_input = st.text_input("🔒 รหัสผ่าน (Password)", type="password", key="login_pass")
                st.write("")
                
                if st.button("🚀 เข้าสู่ระบบ", use_container_width=True):
                    user_data = login_user(login_user_input, login_pass_input)
                    if user_data:
                        st.session_state.logged_in = True
                        st.session_state.username = user_data[0]
                        st.session_state.role = user_data[1] if user_data[1] else "user"
                        st.success(f"🎉 ยินดีต้อนรับคุณ {st.session_state.username}!")
                        st.rerun()
                    else:
                        st.error("❌ ชื่อผู้ใช้งานหรือรหัสผ่านไม่ถูกต้อง")

        with auth_tab2:
            with st.container():
                st.write("")
                with st.form("register_form"):
                    reg_user_input = st.text_input("👤 ตั้งชื่อผู้ใช้งาน (Username)", key="reg_user")
                    reg_pass_input = st.text_input("🔒 ตั้งรหัสผ่าน (Password)", type="password", key="reg_pass")
                    reg_confirm_pass = st.text_input("🔁 ยืนยันรหัสผ่านอีกครั้ง", type="password", key="reg_confirm")
                    
                    role_choice = st.radio("เลือกสิทธิ์การใช้งาน:", ["👤 พนักงานทั่วไป (User)", "👑 ผู้ดูแลระบบ (Admin)"], key="reg_role_choice")
                    secret_code_input = st.text_input("🔑 รหัสลับแต่งตั้ง Admin", type="password", placeholder="ใส่เฉพาะเมื่อเลือกสิทธิ์ Admin", key="reg_secret")
                    st.write("")
                    
                    submit_reg = st.form_submit_button("✨ สมัครสมาชิก", use_container_width=True)

                if submit_reg:
                    username_clean = reg_user_input.strip()
                    password_clean = reg_pass_input.strip()

                    if not username_clean or not password_clean:
                        st.warning("⚠️ กรุณากรอกชื่อผู้ใช้งานและรหัสผ่านให้ครบถ้วน")
                    elif password_clean != reg_confirm_pass.strip():
                        st.error("❌ รหัสผ่านไม่ตรงกัน กรุณาตรวจสอบอีกครั้ง")
                    elif role_choice == "👑 ผู้ดูแลระบบ (Admin)" and secret_code_input.strip() != ADMIN_SECRET_KEY:
                        st.error("❌ รหัสลับแต่งตั้ง Admin ไม่ถูกต้อง!")
                    else:
                        assigned_role = 'admin' if role_choice == "👑 ผู้ดูแลระบบ (Admin)" else 'user'
                        if add_user(username_clean, password_clean, role=assigned_role):
                            st.success(f"🎉 สมัครสมาชิกสำเร็จ! สิทธิ์: '{assigned_role.upper()}' สามารถสลับไปล็อกอินได้เลย")
                        else:
                            st.error("❌ ชื่อผู้ใช้งานนี้มีในระบบแล้ว")

# ==========================================
# 2. หน้าจอหลักหลังเข้าสู่ระบบสำเร็จ
# ==========================================
else:
    # Sidebar: แสดงผู้ใช้งาน & ปุ่มจัดการเมนู
    with st.sidebar:
        role_badge = "👑 ADMIN" if st.session_state.role == "admin" else "👤 USER"
        st.markdown(f"### 👤 ผู้ใช้งาน: **{st.session_state.username}**")
        st.caption(f"สถานะ: `{role_badge}`")
        
        if st.button("🚪 ออกจากระบบ", use_container_width=True):
            st.session_state.logged_in = False
            st.session_state.username = ""
            st.session_state.role = "user"
            st.rerun()

        st.divider()
        st.header("⚙️ จัดการเมนู")
        
        if st.button("🔄 รีเซ็ตเมนูทั้งหมด (คืนค่าจากรูปภาพ)", use_container_width=True):
            st.session_state.menu = DEFAULT_MENU.copy()
            st.success("คืนค่าเมนูทั้งหมดเรียบร้อย!")
            st.rerun()

        with st.expander("➕ เพิ่มเมนูใหม่"):
            new_name = st.text_input("ชื่อเมนูใหม่")
            new_cost = st.number_input("ราคาต้นทุน (บาท)", min_value=0.0, value=10.0, step=0.5)
            new_price = st.number_input("ราคาขายปกติ (บาท)", min_value=0, value=25)
            
            if st.button("💾 บันทึกเมนูใหม่", use_container_width=True):
                if new_name.strip() != "":
                    st.session_state.menu[new_name] = {"cost": new_cost, "price": new_price}
                    st.success(f"เพิ่มเมนู '{new_name}' เรียบร้อย!")
                    st.rerun()
                else:
                    st.warning("กรุณากรอกชื่อเมนู")

        if st.session_state.role == "admin":
            with st.expander("🗑️ ลบเมนู (สิทธิ์ Admin)"):
                if len(st.session_state.menu) > 0:
                    delete_item = st.selectbox("เลือกเมนูที่ต้องการลบ", list(st.session_state.menu.keys()))
                    if st.button("❌ ลบเมนูนี้", use_container_width=True):
                        del st.session_state.menu[delete_item]
                        st.success(f"ลบเมนู '{delete_item}' เรียบร้อย!")
                        st.rerun()

            with st.expander("👥 จัดการสมาชิก (สิทธิ์ Admin)"):
                all_users = get_all_users()
                other_users = [f"{u[0]} ({u[1].upper()})" for u in all_users if u[0] != st.session_state.username]
                
                if other_users:
                    selected_user_str = st.selectbox("เลือกบัญชีที่ต้องการลบ", other_users, key="del_user_select")
                    target_username = selected_user_str.split(" ")[0]
                    
                    if st.button("❌ ลบบัญชีนี้", key="btn_del_user", use_container_width=True):
                        delete_user(target_username)
                        st.success(f"ลบบัญชี '{target_username}' สำเร็จ!")
                        st.rerun()
                else:
                    st.info("ไม่มีสมาชิกอื่นในระบบ")

    # Header หลัก
    st.markdown(
        """
        <div style="background: linear-gradient(135deg, #FFE29F 0%, #FF719A 100%); padding: 18px; border-radius: 18px; border: 2px solid #FF5252; margin-bottom: 20px; text-align: center;">
            <h2 style="color: #7B1FA2; margin: 0; font-size: 26px; font-weight: bold;">🧋 ร้านน้ำสร้างตัว</h2>
            <p style="color: #4A148C; margin: 5px 0 0 0; font-size: 15px; font-weight: 500;">ระบบบันทึกยอดขาย & กำไรประจำวัน</p>
        </div>
        """, 
        unsafe_allow_html=True
    )

    # --- ส่วนที่ 1: ตารางราคา ---
    menu_count = len(st.session_state.menu)
    with st.expander(f"📋 ดูตารางราคา & กำไรทั้งหมด (ทั้งหมด {menu_count} เมนู)", expanded=False):
        search_menu = st.text_input("🔍 ค้นหาเมนูในตาราง...", "")
        if st.session_state.menu:
            menu_data = []
            for item, info in st.session_state.menu.items():
                if search_menu.lower() in item.lower():
                    cost_base = info['cost']
                    price_base = info['price']
                    profit_base = price_base - cost_base
                    
                    price_pearl = price_base + PEARL_PRICE
                    cost_pearl = cost_base + PEARL_COST
                    profit_pearl = price_pearl - cost_pearl
                    
                    menu_data.append({
                        "เมนู": item,
                        "ราคาปกติ": f"{price_base} บ.",
                        "กำไรปกติ": f"{profit_base:.2f} บ.",
                        "ราคา (+มุก)": f"{price_pearl} บ.",
                        "กำไร (+มุก)": f"{profit_pearl:.2f} บ."
                    })
            st.dataframe(pd.DataFrame(menu_data), use_container_width=True, height=250)

    # --- ส่วนที่ 2: บันทึกการขาย ---
    with st.container():
        st.subheader("🛒 บันทึกรายการขาย")
        selected_date = st.date_input("📅 วันที่ทำรายการ", value=date.today())

        if st.session_state.menu:
            search_sale_term = st.text_input("🔍 ค้นหาชื่อเมนูที่จะขาย:", placeholder="พิมพ์ค้นหา เช่น ชานม, บ๊วย, ปั่น, นมสด...", key="search_sale_input")
            filtered_sale_menu = [item for item in st.session_state.menu.keys() if search_sale_term.strip().lower() in item.lower()]

            if filtered_sale_menu:
                selected_item = st.selectbox("เลือกรสชาติ / เมนู:", filtered_sale_menu)

                base_cost = st.session_state.menu[selected_item]["cost"]
                base_price = st.session_state.menu[selected_item]["price"]

                col_opt1, col_opt2 = st.columns(2)
                with col_opt1:
                    add_pearl = st.checkbox("🧋 เพิ่มไข่มุก (+5 บ.)")
                with col_opt2:
                    payment_method = st.radio("💳 ช่องทางชำระเงิน", ["💵 เงินสด", "📱 สแกน QR"], horizontal=True)

                unit_price = base_price + (PEARL_PRICE if add_pearl else 0)
                unit_cost = base_cost + (PEARL_COST if add_pearl else 0)
                unit_profit = unit_price - unit_cost

                st.info(f"💡 **{selected_item}** {'(+เพิ่มไข่มุก)' if add_pearl else ''} | แก้วละ **{unit_price} บาท** (กำไร **{unit_profit:.2f} บาท**)")

                qty = st.number_input("จำนวนแก้ว", min_value=1, value=1)
                
                total_price = unit_price * qty
                total_cost = unit_cost * qty
                total_profit = unit_profit * qty

                st.markdown(
                    f"""
                    <div style="background-color: #FFF59D; padding: 12px; border-radius: 10px; margin: 10px 0; text-align: center; border: 1px solid #FBC02D;">
                        <span style="font-size: 17px; color: #333;">💵 ยอดขาย: <b>{total_price:,} บาท</b> | 📈 กำไรสุทธิ: <b style="color: #2E7D32;">{total_profit:,.2f} บาท</b></span>
                    </div>
                    """, 
                    unsafe_allow_html=True
                )

                if st.button("✅ บันทึกการขาย", use_container_width=True):
                    item_name = f"{selected_item} (+มุก)" if add_pearl else selected_item
                    add_sale(selected_date, item_name, qty, total_price, round(total_cost, 2), round(total_profit, 2), payment_method)
                    st.success(f"🎉 บันทึก {item_name} ({qty} แก้ว) เรียบร้อย!")
                    st.rerun()
            else:
                st.warning(f"❌ ไม่พบเมนูที่ค้นหา '{search_sale_term}'")

    # --- ส่วนที่ 3: สรุปยอดขายประจำวัน ---
    st.write("")
    st.subheader(f"📊 สรุปยอดขายวันที่ {selected_date}")

    df_all = get_sales()

    if not df_all.empty:
        df_day = df_all[df_all["sale_date"] == str(selected_date)]
        
        if not df_day.empty:
            total_sales = df_day["total_price"].sum()
            total_costs = df_day["total_cost"].sum()
            total_profits = df_day["total_profit"].sum()
            total_cups = df_day["qty"].sum()

            cash_total = df_day[df_day["payment_method"] == "💵 เงินสด"]["total_price"].sum()
            qr_total = df_day[df_day["payment_method"].str.contains("QR", na=False)]["total_price"].sum()

            col1, col2, col3, col4 = st.columns(4)
            col1.metric("ยอดขายรวม", f"{total_sales:,} บ.")
            col2.metric("ต้นทุนรวม", f"{total_costs:,.2f} บ.")
            col3.metric("กำไรสุทธิ", f"{total_profits:,.2f} บ.")
            col4.metric("ขายได้ทั้งหมด", f"{total_cups:,} แก้ว")

            st.write(f"💳 **แยกตามช่องทางเงินเข้า:** 💵 เงินสด `{cash_total:,} บ.` | 📱 สแกน QR `{qr_total:,} บ.`")

            with st.expander("📋 รายละเอียดประวัติการขายวันนี้", expanded=True):
                df_display = df_day[["id", "item_name", "qty", "total_price", "total_cost", "total_profit", "payment_method"]].copy()
                df_display.columns = ["ID", "เมนู", "จำนวน", "ยอดขาย", "ต้นทุน", "กำไร", "ชำระโดย"]
                st.dataframe(df_display, use_container_width=True)

                csv_data = df_all.to_csv(index=False).encode('utf-8-sig')
                st.download_button(
                    label="📥 ดาวน์โหลดประวัติทั้งหมด (.CSV)",
                    data=csv_data,
                    file_name=f"sales_report_{date.today()}.csv",
                    mime="text/csv"
                )

            with st.expander("🗑️ ลบรายการที่บันทึกผิด"):
                delete_dict = {f"ID {row['id']}: {row['item_name']} ({row['qty']} แก้ว - กำไร {row['total_profit']} บ.)": row['id'] for _, row in df_day.iterrows()}
                selected_delete_label = st.selectbox("เลือกรายการที่ต้องการลบ", list(delete_dict.keys()))
                
                if st.button("❌ ลบรายการนี้", use_container_width=True):
                    target_id = delete_dict[selected_delete_label]
                    delete_sale_by_id(target_id)
                    st.success("ลบรายการเรียบร้อย!")
                    st.rerun()

        else:
            st.info(f"ยังไม่มีรายการขายในวันที่ {selected_date}")
    else:
        st.info("ยังไม่มีข้อมูลรายการขายในระบบ")

    # --- ส่วนที่ 4: อันดับเมนูขายดี ---
    st.divider()
    st.subheader("🏆 อันดับเมนูขายดี (Top Sellers)")

    if not df_all.empty:
        filter_time = st.radio("เลือกช่วงเวลา:", ["ประจำวัน (วันที่เลือก)", "ทั้งหมดสะสม"], horizontal=True)

        if filter_time == "ประจำวัน (วันที่เลือก)":
            target_df = df_all[df_all["sale_date"] == str(selected_date)]
        else:
            target_df = df_all

        if not target_df.empty:
            top_sellers = target_df.groupby("item_name")["qty"].sum().reset_index()
            top_sellers.columns = ["เมนู", "จำนวนแก้ว"]
            top_sellers = top_sellers.sort_values(by="จำนวนแก้ว", ascending=False).reset_index(drop=True)
            top_sellers.index += 1

            col_top1, col_top2 = st.columns([1, 1])
            with col_top1:
                st.write("📊 **5 อันดับแรก**")
                st.dataframe(top_sellers.head(5), use_container_width=True)
            with col_top2:
                st.write("📈 **กราฟยอดขาย**")
                st.bar_chart(top_sellers.set_index("เมนู")["จำนวนแก้ว"])
        else:
            st.info("ไม่มีข้อมูลการขายในช่วงเวลาที่เลือก")
    else:
        st.info("บันทึกการขายเพื่อดูอันดับเมนูขายดี")
