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

# --- DATABASE CONNECTION (Using mysql-connector) ---
# NOTE: Ensure your MySQL server is running!
DB_URL = 'mysql+pymysql://root:abiR%403121@localhost/qp_generator'
UPLOAD_FOLDER = 'uploads'

try:
    engine = create_engine(DB_URL)
    with engine.connect() as conn:
        pass
except Exception as e:
    st.error(f"❌ Database Connection Failed. Error: {e}")
    st.stop()

Session = sessionmaker(bind=engine)
Base = declarative_base()

# --- DATABASE MODELS (Matches your screenshots exactly) ---
# See for Department & GridType
# See for Subject

class Department(Base):
    __tablename__ = 'department'
    id = Column(Integer, primary_key=True)
    school_id = Column(Integer)
    name = Column(String(100))
    level = Column(String(20))
    pattern_name = Column(String(50))

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

    department = relationship("Department")
    grid_type = relationship("GridType")

# --- HELPER FUNCTIONS ---
def get_recent_files():
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
    files = []
    for f in os.listdir(UPLOAD_FOLDER):
        if f.endswith('.docx'):
            path = os.path.join(UPLOAD_FOLDER, f)
            stats = os.stat(path)
            files.append({
                "File Name": f,
                "Size (KB)": round(stats.st_size / 1024, 2),
                "Created At": datetime.fromtimestamp(stats.st_mtime).strftime('%Y-%m-%d %H:%M')
            })
    return sorted(files, key=lambda x: x['Created At'], reverse=True)

# --- LOGIN PAGE ---
def login_page():
    st.title("🎓 GURU NANAK COLLEGE (AUTONOMOUS)")
    st.subheader("Question Paper Controller Login")
    with st.form("login"):
        user = st.text_input("Username")
        pwd = st.text_input("Password", type="password")
        if st.form_submit_button("Login"):
            if user == "admin" and pwd == "gnc2026":
                st.session_state['logged_in'] = True
                st.rerun()
            else:
                st.error("Invalid Credentials")

# --- MAIN DASHBOARD ---
def main_dashboard():
    with st.sidebar:
        st.title("Admin Panel")
        menu = st.radio("Menu", ["📊 Overview", "📘 Manage Subjects", "📂 Downloads"])
        if st.button("Logout"):
            st.session_state['logged_in'] = False
            st.rerun()

    if menu == "📘 Manage Subjects":
        st.header("Manage Subjects")
        session = Session()
        
        departments = session.query(Department).all()
        grid_types = session.query(GridType).all()

        col1, col2 = st.columns([1, 2])

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
                        st.rerun()
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
                    st.rerun()
            else:
                st.info("No subjects found.")
        session.close()

    elif menu == "📂 Downloads":
        st.header("Recent Question Papers")
        files = get_recent_files()
        if files:
            for f in files:
                c1, c2, c3 = st.columns([4, 2, 2])
                c1.write(f"📄 **{f['File Name']}**")
                c2.write(f.get("Created At"))
                with c3:
                    with open(os.path.join(UPLOAD_FOLDER, f['File Name']), "rb") as file:
                        st.download_button("Download", file, file_name=f['File Name'])
                st.divider()
        else:
            st.info("No files generated yet.")
    
    elif menu == "📊 Overview":
        session = Session()
        try:
            cnt_sub = session.query(Subject).count()
            cnt_dept = session.query(Department).count()
            c1, c2 = st.columns(2)
            c1.metric("Total Subjects", cnt_sub)
            c2.metric("Total Departments", cnt_dept)
        except Exception as e:
            st.error(f"Error fetching stats: {e}")
        session.close()

# --- APP START ---
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

if st.session_state['logged_in']:
    main_dashboard()
else:
    login_page()