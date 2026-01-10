import streamlit as st
import sys
import subprocess
import time
import os
import pandas as pd  # <--- Essential for dataframes
import urllib.parse
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey
from sqlalchemy.orm import sessionmaker, declarative_base, relationship
from werkzeug.security import generate_password_hash, check_password_hash

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="GNC Admin Dashboard", page_icon="🎓", layout="wide")

# --- COLLEGE / AUTH CONFIG ---
COLLEGE_NAME = "Guru Nanak College"
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "")

# --- CUSTOM CSS ---
st.markdown("""
<style>
    .dept-card {
        background-color: #262730; color: white; padding: 20px;
        border-radius: 8px; text-align: center; height: 180px;
        display: flex; flex-direction: column; align-items: center; justify-content: center;
        margin-bottom: 15px; border: 1px solid #3d3d3d;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3); transition: transform 0.2s;
    }
    .dept-card:hover { transform: scale(1.02); border-color: #ff4b4b; }
    .dept-name { font-size: 18px; font-weight: 600; margin-bottom: 12px; }
    .dept-badge { background-color: #444; color: #ddd; padding: 4px 10px; border-radius: 12px; font-size: 12px; }
</style>
""", unsafe_allow_html=True)

# --- DATABASE CONNECTION ---
db_user = "root"
raw_password = "abiR@3121" 
encoded_password = urllib.parse.quote_plus(raw_password)
db_host = "localhost"
db_name = "qp_generator"
DB_URL = f'mysql+pymysql://{db_user}:{encoded_password}@{db_host}/{db_name}'
UPLOAD_FOLDER = 'uploads'

try:
    engine = create_engine(
        DB_URL,
        pool_size=10, max_overflow=20, pool_pre_ping=True, pool_recycle=3600, echo=False
    )
    with engine.connect() as conn: pass
except Exception as e:
    st.error(f"❌ Database Connection Error: {e}")
    st.stop()

Session = sessionmaker(bind=engine)
Base = declarative_base()

# --- MODELS ---
class School(Base):
    __tablename__ = 'school'
    id = Column(Integer, primary_key=True)
    name = Column(String(100))
    departments = relationship("Department", back_populates="school", cascade="all, delete-orphan")

class Department(Base):
    __tablename__ = 'department'
    id = Column(Integer, primary_key=True)
    school_id = Column(Integer, ForeignKey('school.id'))
    name = Column(String(100))
    level = Column(String(20))
    pattern_name = Column(String(50))
    school = relationship("School", back_populates="departments")
    subjects = relationship("Subject", back_populates="department", cascade="all, delete-orphan")

class GridType(Base):
    __tablename__ = 'grid_type'
    id = Column(Integer, primary_key=True)
    name = Column(String(50))
    has_problem_column = Column(Integer)

class Subject(Base):
    __tablename__ = 'subject'
    id = Column(Integer, primary_key=True)
    dept_id = Column(Integer, ForeignKey('department.id'))
    name = Column(String(100))
    code = Column(String(20))
    semester = Column(Integer)
    pattern_name = Column(String(50))
    grid_type_id = Column(Integer, ForeignKey('grid_type.id'))
    department = relationship("Department", back_populates="subjects")
    grid_type = relationship("GridType")

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    username = Column(String(100), unique=True)
    password = Column(String(255))
    role = Column(String(50))
    school_access_id = Column(Integer, ForeignKey('school.id'), nullable=True)
    school = relationship("School")

Base.metadata.create_all(engine)

# --- HELPER FUNCTIONS ---
def get_recent_files():
    if not os.path.exists(UPLOAD_FOLDER): os.makedirs(UPLOAD_FOLDER)
    files = []
    for f in os.listdir(UPLOAD_FOLDER):
        if f.endswith('.docx'):
            path = os.path.join(UPLOAD_FOLDER, f)
            stats = os.stat(path)
            files.append({
                "File Name": f,
                "Created At": datetime.fromtimestamp(stats.st_mtime).strftime('%Y-%m-%d %H:%M')
            })
    return sorted(files, key=lambda x: x['Created At'], reverse=True)

def get_accessible_schools(session, role=None, school_access_id=None):
    if role == "admin" or school_access_id is None:
        return session.query(School).all()
    else:
        school = session.get(School, school_access_id)
        return [school] if school else []

def safe_rerun():
    if hasattr(st, "rerun"): st.rerun()
    elif hasattr(st, "experimental_rerun"): st.experimental_rerun()

# --- CALLBACKS FOR SAFE DELETION ---

def delete_school_callback(school_id):
    local_session = Session()
    try:
        dept_count = local_session.query(Department).filter(Department.school_id == school_id).count()
        if dept_count > 0:
            st.toast(f"⚠️ Cannot delete! School has {dept_count} departments.", icon="🚫")
        else:
            item = local_session.get(School, school_id)
            if item:
                local_session.delete(item)
                local_session.commit()
                st.toast(f"✅ Deleted School: {item.name}")
            else:
                st.toast("School not found.", icon="❓")
    except Exception as e:
        st.error(f"Error: {e}")
    finally:
        local_session.close()

def delete_department_callback(dept_id):
    local_session = Session()
    try:
        sub_count = local_session.query(Subject).filter(Subject.dept_id == dept_id).count()
        if sub_count > 0:
            st.toast(f"⚠️ Cannot delete! Department has {sub_count} subjects.", icon="🚫")
        else:
            item = local_session.get(Department, dept_id)
            if item:
                local_session.delete(item)
                local_session.commit()
                st.toast(f"✅ Deleted Department: {item.name}")
            else:
                st.toast("Department not found.", icon="❓")
    except Exception as e:
        st.error(f"Error: {e}")
    finally:
        local_session.close()

def delete_subject_callback(subject_id):
    local_session = Session()
    try:
        item = local_session.get(Subject, subject_id)
        if item:
            local_session.delete(item)
            local_session.commit()
            st.toast(f"Deleted Subject: {item.name}")
    except Exception as e:
        st.error(f"Error: {e}")
    finally:
        local_session.close()

def delete_user_callback(user_id):
    local_session = Session()
    try:
        item = local_session.get(User, user_id)
        if item:
            local_session.delete(item)
            local_session.commit()
            st.toast(f"Deleted User: {item.username}")
    except Exception as e:
        st.error(f"Error: {e}")
    finally:
        local_session.close()

# --- LOGIN PAGE ---
def login_page():
    st.markdown(f"<h1 style='text-align:center'>{COLLEGE_NAME}</h1>", unsafe_allow_html=True)
    st.subheader("Admin Login")
    
    session = Session()
    admin_exists = False
    try:
        admin_exists = session.query(User).filter(User.role == 'admin').count() > 0
    except: pass
    finally: session.close()

    if not ADMIN_PASSWORD and not admin_exists:
        st.info("No admin user configured. Create one now.")
        with st.form("create_admin"):
            new_user = st.text_input("Username", value=ADMIN_USERNAME)
            new_pass = st.text_input("Password", type="password")
            if st.form_submit_button("Create Admin"):
                if new_user and new_pass:
                    sess = Session()
                    try:
                        if sess.query(User).filter(User.username==new_user).first():
                            st.error("Username taken.")
                        else:
                            sess.add(User(username=new_user, password=generate_password_hash(new_pass), role='admin'))
                            sess.commit()
                            st.success("Admin created! Logging in...")
                            st.session_state.update({'logged_in':True, 'user':new_user, 'role':'admin'})
                            time.sleep(1)
                            safe_rerun()
                    except Exception as e:
                        sess.rollback()
                        st.error(f"Error: {e}")
                    finally: sess.close()
        return

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.form("login"):
            u = st.text_input("Username")
            p = st.text_input("Password", type="password")
            if st.form_submit_button("Login"):
                sess = Session()
                try:
                    user = sess.query(User).filter(User.username==u).first()
                    valid = False
                    if user:
                        try: valid = check_password_hash(user.password or "", p)
                        except: valid = False
                        if not valid and user.password == p: 
                            valid = True
                            try:
                                user.password = generate_password_hash(p)
                                sess.commit()
                            except: sess.rollback()
                    
                    if not valid and u == ADMIN_USERNAME and ADMIN_PASSWORD and p == ADMIN_PASSWORD:
                        st.session_state.update({'logged_in':True, 'user':u, 'role':'admin'})
                        st.success("Logged in via Env")
                        time.sleep(0.5); safe_rerun()
                        return

                    if valid and user:
                        st.session_state.update({
                            'logged_in':True, 'user':user.username, 
                            'role':user.role, 'school_access_id':user.school_access_id
                        })
                        st.success("Logged in!")
                        time.sleep(0.5); safe_rerun()
                    else:
                        st.error("Invalid credentials")
                finally: sess.close()

# --- MAIN DASHBOARD ---
def main_dashboard():
    if not st.session_state.get('logged_in'):
        login_page(); return

    with st.sidebar:
        st.title("Admin Panel")
        if st.button("Logout"):
            st.session_state.clear()
            safe_rerun()
        menu = st.radio("Menu", ["🏠 Home", "🏫 Manage Schools", "🎓 Manage Departments", "📘 Manage Subjects", "👥 Manage Users", "📂 Downloads"])

    user_role = st.session_state.get('role', 'staff')
    user_school_id = st.session_state.get('school_access_id')
    
    session = Session() 
    try:
        # --- HOME ---
        if menu == "🏠 Home":
            st.header("Home — Visual Overview")
            schools = get_accessible_schools(session, user_role, user_school_id)
            
            c1, c2 = st.columns(2)
            lev = c1.selectbox("Filter Level:", ["All", "UG", "PG"])
            sch_opts = ["All"] + [s.name for s in schools]
            sch_filter = c2.selectbox("Filter School:", sch_opts)

            q = session.query(Department)
            if lev != "All": q = q.filter(Department.level == lev)
            if sch_filter != "All": 
                q = q.filter(Department.school.has(School.name == sch_filter))
            else:
                s_ids = [s.id for s in schools]
                if s_ids: q = q.filter(Department.school_id.in_(s_ids))
            
            depts = q.all()
            if depts:
                cols = st.columns(3)
                for i, d in enumerate(depts):
                    with cols[i%3]:
                        st.markdown(f"""<div class="dept-card">
                            <div class="dept-name">{d.name}</div>
                            <div class="dept-badge">{d.school.name if d.school else 'No School'}</div>
                            <div style="margin-top:5px; font-size:10px; color:#aaa;">{d.level}</div>
                        </div>""", unsafe_allow_html=True)
            else: st.info("No departments found.")

        # --- MANAGE SCHOOLS ---
        elif menu == "🏫 Manage Schools":
            if user_school_id is None: # Admin Only
                st.header("Manage Schools")
                c1, c2 = st.columns(2)
                
                with c1:
                    with st.form("add_sch_form"):
                        st.subheader("Create School")
                        nm = st.text_input("School Name")
                        if st.form_submit_button("Create"):
                            if nm.strip():
                                ls = Session()
                                try:
                                    if not ls.query(School).filter(School.name == nm.strip()).first():
                                        ls.add(School(name=nm.strip()))
                                        ls.commit()
                                        st.success(f"Created: {nm}")
                                        time.sleep(0.5); safe_rerun()
                                    else: st.warning("School exists!")
                                except Exception as e: st.error(f"Error: {e}")
                                finally: ls.close()
                            else: st.error("Name required.")

                with c2:
                    st.subheader("Existing Schools")
                    schools = session.query(School).all()
                    if schools:
                        data = [{"ID": s.id, "Name": s.name} for s in schools]
                        st.dataframe(pd.DataFrame(data), hide_index=True, use_container_width=True)
                        st.write("---")
                        sel_s = st.selectbox("Delete School", schools, format_func=lambda x: x.name, key="del_school_select")
                        st.button("Delete School", on_click=delete_school_callback, args=(sel_s.id,))
                    else: st.info("No schools.")
            else:
                st.warning("Restricted Access.")

        # --- MANAGE DEPARTMENTS ---
        elif menu == "🎓 Manage Departments":
            st.header("Manage Departments")
            
            if user_school_id:
                avail_schools = session.query(School).filter(School.id == user_school_id).all()
            else:
                avail_schools = session.query(School).all()

            c1, c2 = st.columns(2)

            with c1:
                with st.form("new_dept"):
                    st.subheader("Create Department")
                    dn = st.text_input("Dept Name").strip()
                    dl = st.selectbox("Level", ["UG", "PG", "Ph.D"])
                    ds = st.selectbox("School", avail_schools, format_func=lambda x: x.name) if avail_schools else None
                    
                    if st.form_submit_button("Create"):
                        if dn and ds:
                            ls = Session()
                            try:
                                exists = ls.query(Department).filter(Department.name == dn, Department.school_id == ds.id).first()
                                if exists: st.warning("Dept exists in this school!")
                                else:
                                    ls.add(Department(name=dn, level=dl, school_id=ds.id, pattern_name="Pattern_1"))
                                    ls.commit()
                                    st.success(f"Added {dn}")
                                    time.sleep(0.5); safe_rerun()
                            except Exception as e: st.error(f"Error: {e}")
                            finally: ls.close()
                        else: st.error("Missing fields.")

            with c2:
                st.subheader("Existing Departments")
                query = session.query(Department)
                if user_school_id:
                    query = query.filter(Department.school_id == user_school_id)
                depts = query.all()

                if depts:
                    data = [{"Name": d.name, "Level": d.level, "School": d.school.name} for d in depts]
                    st.dataframe(pd.DataFrame(data), hide_index=True, use_container_width=True)
                    st.write("---")
                    sel_d = st.selectbox("Delete Dept", depts, format_func=lambda x: f"{x.name} ({x.level})", key="del_dept_select")
                    st.button("Delete Department", on_click=delete_department_callback, args=(sel_d.id,))
                else: st.info("No departments found.")

        # --- SUBJECTS (FIXED INDENTATION) ---
        elif menu == "📘 Manage Subjects":
            st.header("Manage Subjects")
            
            # 1. Fetch available data
            depts = session.query(Department).all()
            grids = session.query(GridType).all()
            
            # 2. Filter departments if User is Staff
            if user_school_id:
                # Only show departments belonging to the user's school
                depts = [d for d in depts if d.school_id == user_school_id]

            c1, c2 = st.columns(2)
            
            # --- LEFT: Create Subject Form ---
            with c1:
                with st.form("add_sub"):
                    st.subheader("Add Subject")
                    n = st.text_input("Name")
                    c = st.text_input("Code")
                    s = st.number_input("Sem", 1, 6)
                    
                    if depts and grids:
                        dc = st.selectbox("Dept", depts, format_func=lambda x: x.name)
                        gc = st.selectbox("Grid", grids, format_func=lambda x: x.name)
                        pt = st.text_input("Pattern", "Pattern_1")
                        
                        if st.form_submit_button("Save") and n and c:
                            ls = Session()
                            try:
                                if ls.query(Subject).filter(Subject.code == c).first():
                                    st.warning("Code exists!")
                                else:
                                    ls.add(Subject(name=n, code=c, semester=s, dept_id=dc.id, grid_type_id=gc.id, pattern_name=pt))
                                    ls.commit()
                                    st.success("Saved!")
                                    time.sleep(0.5); safe_rerun()
                            except Exception as e:
                                st.error(f"Error: {e}")
                            finally:
                                ls.close()
                    else:
                        st.warning("Configure Depts/Grids first.")

            # --- RIGHT: List & Delete Subjects ---
            with c2:
                st.subheader("Existing Subjects")
                
                # Fetch subjects
                query = session.query(Subject)
                
                # Filter subjects if user is staff (by their school's departments)
                if user_school_id:
                    dept_ids = [d.id for d in depts] # depts is already filtered above
                    if dept_ids:
                        query = query.filter(Subject.dept_id.in_(dept_ids))
                    else:
                        query = query.filter(False) # No depts = no subjects

                subs = query.all()

                if subs:
                    try:
                        df = pd.DataFrame([
                            {"Code": x.code, "Name": x.name, "Dept": x.department.name if x.department else "N/A"} 
                            for x in subs
                        ])
                        st.dataframe(df, hide_index=True, use_container_width=True)
                    except NameError:
                        st.error("Pandas library (pd) missing.")

                    st.write("---")
                    sel_sub = st.selectbox("Delete Subject", subs, format_func=lambda x: f"{x.code} - {x.name}", key="del_sub_select")
                    st.button("Delete Subject", on_click=delete_subject_callback, args=(sel_sub.id,))
                else:
                    st.info("No subjects found.")

        # --- USERS ---
        elif menu == "👥 Manage Users":
            st.header("Manage Users")
            c1, c2 = st.columns(2)
            with c1:
                with st.form("new_user"):
                    st.subheader("Create User")
                    un = st.text_input("Username")
                    pw = st.text_input("Password")
                    rl = st.selectbox("Role", ["staff", "admin"])
                    sc = st.selectbox("School Access", [None]+session.query(School).all(), format_func=lambda x:x.name if x else "All Schools")
                    
                    if st.form_submit_button("Create") and un and pw:
                        ls = Session()
                        try:
                            ls.add(User(username=un, password=generate_password_hash(pw), role=rl, school_access_id=sc.id if sc else None))
                            ls.commit()
                            st.success("Created"); time.sleep(0.5); safe_rerun()
                        except: st.error("Error creating user"); 
                        finally: ls.close()
            
            with c2:
                st.subheader("Existing Users")
                users = session.query(User).all()
                if users:
                    st.dataframe(pd.DataFrame([{"User":u.username, "Role":u.role} for u in users]), hide_index=True, use_container_width=True)
                    st.write("---")
                    sel_u = st.selectbox("Delete User", users, format_func=lambda x:x.username, key="del_user_select")
                    st.button("Delete User", on_click=delete_user_callback, args=(sel_u.id,))

        # --- DOWNLOADS ---
        elif menu == "📂 Downloads":
            st.header("Files")
            for f in get_recent_files():
                c1, c2 = st.columns([4,1])
                c1.write(f"{f['File Name']} ({f['Created At']})")
                with open(os.path.join(UPLOAD_FOLDER, f['File Name']), "rb") as fl:
                    c2.download_button("Download", fl, file_name=f['File Name'])
                st.divider()

    finally:
        session.close()

if __name__ == "__main__":
    if 'logged_in' not in st.session_state: st.session_state['logged_in'] = False
    main_dashboard()