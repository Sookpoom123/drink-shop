import streamlit as st
import pandas as pd
import sqlite3
import hashlib
from datetime import date

st.set_page_config(page_title="ระบบบันทึกยอดขายร้านน้ำ", layout="centered")

DB_FILE = "sales_data.db"
ADMIN_SECRET_KEY = "3475"  # 🔑 รหัสลับสำหรับแต่งตั้ง Admin

# --- ฟังก์ชันจัดการระบบความปลอดภัย (Password Hashing) ---
def make_hashes(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

# --- ส่วนจัดการฐานข้อมูล (SQLite) ---
def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    # ตารางบันทึกการขาย
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
    # ตารางผู้ใช้งาน
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

    # อัปเกรดให้ผู้ใช้ชื่อ 'admin' เป็น admin อัตโนมัติ
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

# --- หน้าเข้าสู่ระบบ / สมัครสมาชิก ---
if not st.session_state.logged_in:
    st.title("🔐 ระบบเข้าสู่ระบบร้านน้ำ")
    
    auth_tab1, auth_tab2 = st.tabs(["🔑 เข้าสู่ระบบ (Login)", "📝 สมัครสมาชิก (Register)"])

    with auth_tab1:
        st.subheader("เข้าสู่ระบบ")
        login_user_input = st.text_input("ชื่อผู้ใช้งาน (Username)", key="login_user")
        login_pass_input = st.text_input("รหัสผ่าน (Password)", type="password", key="login_pass")
        
        if st.button("เข้าสู่ระบบ"):
            user_data = login_user(login_user_input, login_pass_input)
            if user_data:
                st.session_state.logged_in = True
                st.session_state.username = user_data[0]
                st.session_state.role = user_data[1] if user_data[1] else "user"
                st.success(f"ยินดีต้อนรับคุณ {st.session_state.username} (สิทธิ์: {st.session_state.role.upper()})!")
                st.rerun()
            else:
                st.error("ชื่อผู้ใช้งานหรือรหัสผ่านไม่ถูกต้อง")

    with auth_tab2:
        st.subheader("สร้างบัญชีใหม่")
        
        with st.form("register_form"):
            reg_user_input = st.text_input("ตั้งชื่อผู้ใช้งาน (Username)", key="reg_user")
            reg_pass_input = st.text_input("ตั้งรหัสผ่าน (Password)", type="password", key="reg_pass")
            reg_confirm_pass = st.text_input("ยืนยันรหัสผ่านอีกครั้ง", type="password", key="reg_confirm")
            
            role_choice = st.radio("เลือกประเภทสิทธิ์การใช้งาน:", ["👤 พนักงานทั่วไป (User)", "👑 ผู้ดูแลระบบ (Admin)"], key="reg_role_choice")
            secret_code_input = st.text_input("🔑 ใส่รหัสลับเพื่อแต่งตั้ง Admin (เฉพาะกรณีเลือก Admin)", type="password", placeholder="กรอกรหัสลับที่นี่", key="reg_secret")
            
            submit_reg = st.form_submit_button("สมัครสมาชิก")

        if submit_reg:
            username_clean = reg_user_input.strip()
            password_clean = reg_pass_input.strip()

            if not username_clean or not password_clean:
                st.warning("⚠️ กรุณากรอกชื่อผู้ใช้งานและรหัสผ่านให้ครบถ้วน")
            elif password_clean != reg_confirm_pass.strip():
                st.error("❌ รหัสผ่านไม่ตรงกัน กรุณาตรวจสอบอีกครั้ง")
            elif role_choice == "👑 ผู้ดูแลระบบ (Admin)" and secret_code_input.strip() != ADMIN_SECRET_KEY:
                st.error("❌ รหัสลับแต่งตั้ง Admin ไม่ถูกต้อง! กรุณาตรวจสอบรหัสอีกครั้ง")
            else:
                assigned_role = 'admin' if role_choice == "👑 ผู้ดูแลระบบ (Admin)" else 'user'
                
                if add_user(username_clean, password_clean, role=assigned_role):
                    st.success(f"🎉 สมัครสมาชิกสำเร็จ! ได้รับสิทธิ์เป็น **'{assigned_role.upper()}'** สามารถสลับไปที่แท็บ 'เข้าสู่ระบบ' ได้เลยครับ")
                else:
                    st.error("❌ ชื่อผู้ใช้งานนี้มีในระบบแล้ว กรุณาใช้ชื่ออื่น")

# --- หน้าจอหลักหลังเข้าสู่ระบบสำเร็จ ---
else:
    PEARL_PRICE = 5.0
    PEARL_COST = 1.0

    if "menu" not in st.session_state:
        st.session_state.menu = {
            "ชาแดงปั่น": {"cost": 14.72, "price": 35},
            "ชาเขียวปั่น": {"cost": 15.73, "price": 35},
            "ชาไต้หวันปั่น": {"cost": 13.04, "price": 35},
            "โกโก้ปั่น": {"cost": 18.16, "price": 35},
            "นมชมพูปั่น": {"cost": 14.06, "price": 35},
            "ชาดำเย็น": {"cost": 6.61, "price": 19},
            "ชามะนาว": {"cost": 7.65, "price": 19},
            "โกโก้": {"cost": 13.11, "price": 25},
            "นมสดบราวซูการ์": {"cost": 11.20, "price": 25},
            "ชานมไต้หวัน": {"cost": 11.12, "price": 19},
            "ชาเย็น(ชานมไทย)": {"cost": 11.58, "price": 25},
            "ชาเขียว(ชาเขียวนม)": {"cost": 12.38, "price": 25},
            "ชาลูกบ๊วย": {"cost": 9.03, "price": 24},
            "น้ำผึ้งมะนาว": {"cost": 10.07, "price": 19},
        }

    # Sidebar: แสดงผู้ใช้งาน & ปุ่มออกจากระบบ & จัดการเมนู & จัดการสมาชิก
    with st.sidebar:
        role_label = "👑 ADMIN" if st.session_state.role == "admin" else "👤 พนักงาน (User)"
        st.write(f"ผู้ใช้งาน: **{st.session_state.username}** ({role_label})")
        if st.button("🚪 ออกจากระบบ (Logout)"):
            st.session_state.logged_in = False
            st.session_state.username = ""
            st.session_state.role = "user"
            st.rerun()

        st.divider()
        st.header("⚙️ จัดการเมนู")
        
        st.subheader("➕ เพิ่มเมนูใหม่")
        new_name = st.text_input("ชื่อเมนูใหม่")
        new_cost = st.number_input("ราคาต้นทุน (บาท)", min_value=0.0, value=10.0, step=0.5)
        new_price = st.number_input("ราคาขายปกติ (บาท)", min_value=0, value=25)
        
        if st.button("บันทึกเมนูใหม่"):
            if new_name.strip() != "":
                st.session_state.menu[new_name] = {"cost": new_cost, "price": new_price}
                st.success(f"เพิ่มเมนู '{new_name}' เรียบร้อย!")
                st.rerun()
            else:
                st.warning("กรุณากรอกชื่อเมนู")

        # 🔒 ส่วนสำหรับ ADMIN เท่านั้น (ลบเมนู / ลบสมาชิก)
        if st.session_state.role == "admin":
            st.divider()
            st.subheader("🗑️ ลบเมนู (สิทธิ์ Admin)")
            if len(st.session_state.menu) > 0:
                delete_item = st.selectbox("เลือกเมนูที่ต้องการลบ", list(st.session_state.menu.keys()))
                if st.button("❌ ลบเมนูนี้"):
                    del st.session_state.menu[delete_item]
                    st.success(f"ลบเมนู '{delete_item}' เรียบร้อย!")
                    st.rerun()

            st.divider()
            st.subheader("👥 ลบสมาชิก (สิทธิ์ Admin)")
            all_users = get_all_users()
            other_users = [f"{u[0]} ({u[1].upper()})" for u in all_users if u[0] != st.session_state.username]
            
            if other_users:
                selected_user_str = st.selectbox("เลือกบัญชีผู้ใช้ที่ต้องการลบ", other_users, key="del_user_select")
                target_username = selected_user_str.split(" ")[0]
                
                if st.button("❌ ลบบัญชีผู้ใช้นี้", key="btn_del_user"):
                    delete_user(target_username)
                    st.success(f"ลบบัญชีผู้ใช้ '{target_username}' สำเร็จ!")
                    st.rerun()
            else:
                st.info("ยังไม่มีสมาชิกอื่นในระบบ")

    st.title("🥤 ระบบบันทึกยอดขาย & กำไร (ร้านน้ำครอบครัว)")

    # --- ส่วนที่ 1: ตารางราคา ---
    st.subheader(f"📋 ตารางราคา & กำไร (ทั้งหมด {len(st.session_state.menu)} เมนู)")
    search_menu = st.text_input("🔍 พิมพ์ค้นหาดูราคาเมนูในตาราง...", "")

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
        st.dataframe(pd.DataFrame(menu_data), use_container_width=True, height=180)

    st.divider()

    # --- ส่วนที่ 2: บันทึกการขาย ---
    st.subheader("📝 บันทึกการขาย")
    selected_date = st.date_input("📅 เลือกวันที่ทำรายการ", value=date.today())

    if st.session_state.menu:
        search_sale_term = st.text_input("🔍 พิมพ์ค้นหาชื่อเมนูที่จะขาย:", placeholder="เช่น ชา, ปั่น, บ๊วย, นม...", key="search_sale_input")
        filtered_sale_menu = [item for item in st.session_state.menu.keys() if search_sale_term.strip().lower() in item.lower()]

        if filtered_sale_menu:
            selected_item = st.selectbox("เลือกรสชาติ / เมนู:", filtered_sale_menu)

            base_cost = st.session_state.menu[selected_item]["cost"]
            base_price = st.session_state.menu[selected_item]["price"]

            col_opt1, col_opt2 = st.columns(2)
            with col_opt1:
                add_pearl = st.checkbox("🧋 เพิ่มไข่มุก (+5 บาท)")
            with col_opt2:
                payment_method = st.radio("💳 ช่องทางการชำระเงิน", ["💵 เงินสด", "📱 สแกน QR Code"], horizontal=True)

            unit_price = base_price + (PEARL_PRICE if add_pearl else 0)
            unit_cost = base_cost + (PEARL_COST if add_pearl else 0)
            unit_profit = unit_price - unit_cost

            st.info(f"💡 **{selected_item}** {'(+เพิ่มไข่มุก)' if add_pearl else ''} | ราคาแก้วละ **{unit_price} บาท** (ต้นทุน {unit_cost:.2f} บาท | **กำไร {unit_profit:.2f} บาท**) ")

            qty = st.number_input("จำนวนแก้ว", min_value=1, value=1)
            
            total_price = unit_price * qty
            total_cost = unit_cost * qty
            total_profit = unit_profit * qty

            col_a, col_b, col_c = st.columns(3)
            col_a.markdown(f"💵 **ยอดขายรวม:** `{total_price:,} บาท`")
            col_b.markdown(f"📦 **ต้นทุนรวม:** `{total_cost:,.2f} บาท`")
            col_c.markdown(f"📈 **กำไรสุทธิ:** `{total_profit:,.2f} บาท`")

            if st.button("🛒 บันทึกการขาย"):
                item_name = f"{selected_item} (+มุก)" if add_pearl else selected_item
                add_sale(selected_date, item_name, qty, total_price, round(total_cost, 2), round(total_profit, 2), payment_method)
                st.success(f"บันทึก {item_name} ({qty} แก้ว) เรียบร้อย!")
                st.rerun()
        else:
            st.warning(f"❌ ไม่พบเมนูที่มีคำว่า '{search_sale_term}'")

    # --- ส่วนที่ 3: สรุปยอดขายประจำวัน ---
    st.divider()
    st.subheader(f"📊 สรุปยอดขายประจำวันที่ {selected_date}")

    df_all = get_sales()

    if not df_all.empty:
        df_day = df_all[df_all["sale_date"] == str(selected_date)]
        
        if not df_day.empty:
            total_sales = df_day["total_price"].sum()
            total_costs = df_day["total_cost"].sum()
            total_profits = df_day["total_profit"].sum()
            total_cups = df_day["qty"].sum()

            cash_total = df_day[df_day["payment_method"] == "💵 เงินสด"]["total_price"].sum()
            qr_total = df_day[df_day["payment_method"] == "📱 สแกน QR Code"]["total_price"].sum()

            col1, col2, col3, col4 = st.columns(4)
            col1.metric("ยอดขายรวม", f"{total_sales:,} บาท")
            col2.metric("ต้นทุนรวม", f"{total_costs:,.2f} บาท")
            col3.metric("กำไรสุทธิ", f"{total_profits:,.2f} บาท")
            col4.metric("ขายได้ทั้งหมด", f"{total_cups:,} แก้ว")

            st.write(f"💳 **สรุปยอดเงินเข้า:** 💵 เงินสด `{cash_total:,} บาท` | 📱 สแกน QR Code `{qr_total:,} บาท`")

            st.write("📋 **ประวัติรายการขายของวันนี้:**")
            df_display = df_day[["id", "item_name", "qty", "total_price", "total_cost", "total_profit", "payment_method"]].copy()
            df_display.columns = ["ID", "เมนู", "จำนวน", "ยอดขาย", "ต้นทุน", "กำไร", "ชำระโดย"]
            st.dataframe(df_display, use_container_width=True)

            csv_data = df_all.to_csv(index=False).encode('utf-8-sig')
            st.download_button(
                label="📥 ดาวน์โหลดประวัติการขายทั้งหมด (.CSV)",
                data=csv_data,
                file_name=f"sales_report_{date.today()}.csv",
                mime="text/csv"
            )

            st.subheader("🗑️ ลบรายการที่บันทึกผิด")
            delete_dict = {f"ID {row['id']}: {row['item_name']} ({row['qty']} แก้ว - กำไร {row['total_profit']} บ.)": row['id'] for _, row in df_day.iterrows()}
            selected_delete_label = st.selectbox("เลือกรายการที่ต้องการลบออก", list(delete_dict.keys()))
            
            if st.button("❌ ลบรายการนี้"):
                target_id = delete_dict[selected_delete_label]
                delete_sale_by_id(target_id)
                st.success("ลบรายการออกจากฐานข้อมูลเรียบร้อย!")
                st.rerun()

        else:
            st.info(f"ยังไม่มีรายการขายประจำวันที่ {selected_date}")
    else:
        st.info("ยังไม่มีข้อมูลรายการขายในระบบ")

    # --- ส่วนที่ 4: อันดับเมนูขายดี ---
    st.divider()
    st.subheader("🏆 อันดับเมนูขายดี (Top Sellers)")

    if not df_all.empty:
        filter_time = st.radio("เลือกช่วงเวลาดูเมนูขายดี:", ["ประจำวัน (วันที่เลือก)", "ทั้งหมดสะสม"], horizontal=True)

        if filter_time == "ประจำวัน (วันที่เลือก)":
            target_df = df_all[df_all["sale_date"] == str(selected_date)]
        else:
            target_df = df_all

        if not target_df.empty:
            top_sellers = target_df.groupby("item_name")["qty"].sum().reset_index()
            top_sellers.columns = ["เมนู", "จำนวน"]
            top_sellers = top_sellers.sort_values(by="จำนวน", ascending=False).reset_index(drop=True)
            top_sellers.index += 1

            col_top1, col_top2 = st.columns([1, 1])
            with col_top1:
                st.write("📊 **ตาราง 5 อันดับแรก**")
                st.dataframe(top_sellers.head(5), use_container_width=True)
            with col_top2:
                st.write("📈 **กราฟยอดขายตามเมนู (แก้ว)**")
                st.bar_chart(top_sellers.set_index("เมนู")["จำนวน"])
        else:
            st.info("ไม่มีข้อมูลการขายในวันที่เลือก")
    else:
        st.info("บันทึกการขายเพื่อดูอันดับเมนูขายดี")
