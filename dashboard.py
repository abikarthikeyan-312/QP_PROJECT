import streamlit as st
import sys
import subprocess
import time

# --- IMPORTS ---
import pandas as pd
import os
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey
from sqlalchemy.orm import sessionmaker, declarative_base, relationship

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="GNC Admin Dashboard", page_icon="🎓", layout="wide")

# --- COLLEGE / AUTH CONFIG ---
COLLEGE_NAME = "Guru Nanak College"
# WARNING: change these for production or load from env
ADMIN_USERNAME = "admin"
# do not hardcode passwords in source; load from environment
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "")

# --- CUSTOM CSS (DARK CARDS) ---
st.markdown("""
<style>
    .dept-card {
        background-color: #262730;
        color: white;
        padding: 20px;
        border-radius: 8px;
        text-align: center;
        height: 180px;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        margin-bottom: 15px;
        border: 1px solid #3d3d3d;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
        transition: transform 0.2s;
    }
    .dept-card:hover {
        transform: scale(1.02);
        border-color: #ff4b4b;
    }
    .dept-name {
        font-size: 18px;
        font-weight: 600;
        margin-bottom: 12px;
    }
    .dept-badge {
        background-color: #444;
        color: #ddd;
        padding: 4px 10px;
        border-radius: 12px;
        font-size: 12px;
    }
</style>
""", unsafe_allow_html=True)

# --- DATABASE CONNECTION ---
DB_URL = 'mysql+pymysql://root:abiR%403121@localhost/qp_generator'
UPLOAD_FOLDER = 'uploads'

try:
    engine = create_engine(DB_URL)
    with engine.connect() as conn: pass
except Exception as e:
    st.error(f"❌ Database Error: {e}")
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
    level = Column(String(20)) # Values: 'UG', 'PG', 'Ph.D'
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

# --- HELPER: GET FILES ---
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


# --- UTILS ---
def safe_rerun():
    """Attempt to rerun the Streamlit script using available APIs.

    Tries `st.experimental_rerun`, then `st.rerun`. If neither exists or
    raises, toggles a session flag and stops execution as a fallback.
    """
    for fn in ("experimental_rerun", "rerun"):
        if hasattr(st, fn):
            try:
                getattr(st, fn)()
                return
            except Exception:
                pass
    # Fallback: toggle a session flag so UI updates, then stop execution
    st.session_state['_refresh_flag'] = not st.session_state.get('_refresh_flag', False)
    try:
        st.stop()
    except Exception:
        pass

# --- LOGIN PAGE ---
def login_page():
    # Centered, simple login UI
    st.markdown(f"<h1 style='text-align:center'>{COLLEGE_NAME}</h1>", unsafe_allow_html=True)
    st.subheader("Admin Login")
    st.write("Enter your admin credentials to access the dashboard.")

    if not ADMIN_PASSWORD:
        st.warning("Admin password is not configured. Set the ADMIN_PASSWORD environment variable to enable login.")

    left, center, right = st.columns([1, 2, 1])
    with center:
        with st.form("login_form"):
            username = st.text_input("Username", placeholder="admin")
            password = st.text_input("Password", type="password")
            remember = st.checkbox("Remember me")
            submitted = st.form_submit_button("Login")
            if submitted:
                if username == ADMIN_USERNAME and ADMIN_PASSWORD and password == ADMIN_PASSWORD:
                    st.session_state['logged_in'] = True
                    st.session_state['user'] = username
                    if remember:
                        st.session_state['remembered_user'] = username
                    st.success("Logged in successfully")
                    time.sleep(0.6)
                    safe_rerun()
                else:
                    st.error("Invalid username or password")
# --- MAIN DASHBOARD ---
def main_dashboard():
    # If not logged in, show login page
    if 'logged_in' not in st.session_state or not st.session_state.get('logged_in'):
        login_page()
        return

    with st.sidebar:
        st.title("Admin Panel")
        # logout button
        if st.button("Logout"):
            st.session_state['logged_in'] = False
            st.session_state.pop('user', None)
            safe_rerun()
        menu = st.radio("Menu", ["🏠 Home", "🏫 Schools & Departments", "📘 Manage Subjects", "📂 Downloads"])

    session = Session()

    # --- HOME VIEW (Visual Overview + Filter) ---
    if menu == "🏠 Home":
        st.header("Home — Visual Overview")
        st.subheader("Visual Overview")

        # Filter dropdown moved to Home
        filter_option = st.selectbox(
            "Filter View:",
            ["All", "UG", "PG", "Ph.D"],
            index=0
        )

        # Query departments with optional filter
        query = session.query(Department)
        if filter_option != "All":
            query = query.filter(Department.level == filter_option)
        filtered_depts = query.all()

        # Render department cards
        if filtered_depts:
            cols = st.columns(3)
            for i, dept in enumerate(filtered_depts):
                with cols[i % 3]:
                    st.markdown(f"""
                    <div class="dept-card">
                        <div class="dept-name">{dept.name}</div>
                        <div class="dept-badge">{dept.school.name if dept.school else 'No School'}</div>
                        <div style="margin-top:5px; font-size:10px; color:#aaa;">{dept.level}</div>
                    </div>
                    """, unsafe_allow_html=True)
        else:
            st.info(f"No departments found for filter: '{filter_option}'")

    # =========================================================
    # 1. SCHOOLS & DEPARTMENTS (FILTER LOGIC HERE)
    # =========================================================
    if menu == "🏫 Schools & Departments":
        tab1, tab2 = st.tabs(["🏛 Manage Schools", "🎓 Manage Departments"])

        # TAB 1: SCHOOLS
        # --- TAB 1: MANAGE SCHOOLS ---
        with tab1:
            c1, c2 = st.columns([1, 2])
            with c1:
                with st.form("add_sch"):
                    st.subheader("Add School")
                    name = st.text_input("School Name")
                    if st.form_submit_button("Save"):
                        session.add(School(name=name))
                        session.commit()
                        safe_rerun()
            with c2:
                st.subheader("Current Schools")
                for s in session.query(School).all():
                    col_a, col_b = st.columns([4, 1])
                    col_a.markdown(f"**{s.name}**")
                    
                    if col_b.button("🗑", key=f"del_{s.id}"):
                        try:
                            # 1. CHECK FOR DEPENDENCIES FIRST
                            dept_count = session.query(Department).filter(Department.school_id == s.id).count()
                            
                            if dept_count > 0:
                                # Show error if school has departments
                                st.error(f"❌ Cannot delete '{s.name}' because it has {dept_count} departments linked to it. Delete departments first!")
                            else:
                                # Safe to delete
                                session.delete(s)
                                session.commit()
                                st.success("✅ School deleted!")
                                time.sleep(1)
                                safe_rerun()
                        except Exception as e:
                            session.rollback()
                            st.error(f"❌ Error deleting school: {str(e)}")

        # TAB 2: DEPARTMENTS (VISUAL OVERVIEW WITH FILTER)
        with tab2:
            st.header("Department Management")
            
            # --- FILTER SECTION ---
            st.subheader("Visual Overview")
            st.caption("Filter controls are available on the Home page.")

            # 2. Add / Delete Panel
            with st.expander("🛠 Add / Delete Controls"):
                c_add, c_del = st.columns(2)
                with c_add: 
                    with st.form("add_dept"):
                        dn = st.text_input("Dept Name")
                        dl = st.selectbox("Level", ["UG", "PG", "Ph.D"]) # Saves as 'UG' or 'PG'
                        ds = st.selectbox("School", session.query(School).all(), format_func=lambda x: x.name) if session.query(School).count() else None
                        if st.form_submit_button("Create"):
                            if dn and ds:
                                session.add(Department(name=dn, level=dl, school_id=ds.id, pattern_name="Pattern_1"))
                                session.commit()
                                safe_rerun()
                with c_del:
                    depts = session.query(Department).all()
                    if depts:
                        to_del = st.selectbox("Delete Dept", depts, format_func=lambda x: f"{x.name} ({x.level})")
                        if st.button("Confirm Delete"):
                            try:
                                session.delete(to_del)
                                session.commit()
                                st.success("✅ Department deleted!")
                                time.sleep(1)
                                safe_rerun()
                            except Exception as e:
                                session.rollback()
                                st.error(f"❌ Error deleting department: {str(e)}")

            st.divider()

            # 3. QUERY LOGIC (unfiltered on this tab)
            filtered_depts = session.query(Department).all()

            # 4. RENDER CARDS
            if filtered_depts:
                # Dynamic Grid
                cols = st.columns(3)
                for i, dept in enumerate(filtered_depts):
                    with cols[i % 3]:
                        st.markdown(f"""
                        <div class="dept-card">
                            <div class="dept-name">{dept.name}</div>
                            <div class="dept-badge">{dept.school.name if dept.school else 'No School'}</div>
                            <div style="margin-top:5px; font-size:10px; color:#aaa;">{dept.level}</div>
                        </div>
                        """, unsafe_allow_html=True)
            else:
                st.info("No departments found.")

    # =========================================================
    # 2. SUBJECTS
    # =========================================================
    elif menu == "📘 Manage Subjects":
        st.header("Subject Management")
        
        # Fetch data from database
        departments = session.query(Department).all()
        grid_types = session.query(GridType).all()
        
        col1, col2 = st.columns(2)
        
        # --- ADD SUBJECT ---
        with col1:
            with st.form("add_sub"):
                st.subheader("Add New Subject")
                name = st.text_input("Subject Name")
                code = st.text_input("Subject Code")
                sem = st.number_input("Semester", 1, 6)
                
                # Check if data exists before creating dropdowns
                if departments and grid_types:
                    dept_choice = st.selectbox("Department", departments, format_func=lambda x: x.name)
                    grid_choice = st.selectbox("Grid Type", grid_types, format_func=lambda x: x.name)
                    pattern_txt = st.text_input("Pattern Name", value="Pattern_1")
                else:
                    st.warning("⚠️ No Departments or Grid Types found in DB.")
                    dept_choice, grid_choice = None, None

                if st.form_submit_button("Save Subject"):
                    if dept_choice and grid_choice:
                        new_sub = Subject(
                            name=name, 
                            code=code, 
                            semester=sem, 
                            dept_id=dept_choice.id,
                            grid_type_id=grid_choice.id,
                            pattern_name=pattern_txt
                        )
                        session.add(new_sub)
                        session.commit()
                        st.success(f"Added {name}")
                        time.sleep(1)
                        safe_rerun()
                    else:
                        st.error("Cannot save: Missing Department or Grid Type.")

        # --- VIEW SUBJECTS ---
        with col2:
            st.subheader("Existing Subjects")
            subjects = session.query(Subject).all()
            if subjects:
                data = [{
                    "Code": s.code, 
                    "Name": s.name, 
                    "Sem": s.semester,
                    "Dept": s.department.name if s.department else "N/A"
                } for s in subjects]
                st.dataframe(pd.DataFrame(data), hide_index=True)

                to_delete = st.selectbox("Select to Delete", subjects, format_func=lambda x: f"{x.code} - {x.name}")
                if st.button("❌ Delete Subject"):
                    session.delete(to_delete)
                    session.commit()
                    st.warning("Deleted!")
                    time.sleep(1)
                    safe_rerun()
            else:
                st.info("No subjects found.")
    # =========================================================
    # 3. DOWNLOADS
    # =========================================================
    elif menu == "📂 Downloads":
        st.header("Recent Files")
        for f in get_recent_files():
            c1, c2 = st.columns([4, 1])
            c1.write(f"📄 {f['File Name']} ({f['Created At']})")
            with open(os.path.join(UPLOAD_FOLDER, f['File Name']), "rb") as file:
                c2.download_button("Download", file, file_name=f['File Name'])
            st.divider()

    session.close()

if __name__ == "__main__":
    if 'logged_in' not in st.session_state: st.session_state['logged_in'] = False
    main_dashboard()