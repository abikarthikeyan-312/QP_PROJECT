# QP_PROJECT - Guru Nanak College Admin Dashboard

A comprehensive Streamlit-based admin dashboard for managing question papers, departments, subjects, and schools at Guru Nanak College.

## 📋 Features

- **User Authentication**: Secure login system with admin credentials
- **School Management**: Create and manage schools/institutions
- **Department Management**: Organize departments with levels (UG, PG, Ph.D)
- **Subject Management**: Add, view, and manage subjects with codes, semesters, and grid types
- **Visual Overview**: Interactive department cards with filtering by level
- **File Management**: Upload and download .docx question papers from the uploads folder
- **Database Integration**: MySQL backend with SQLAlchemy ORM for reliable data management

## 🛠 Tech Stack

- **Frontend**: Streamlit (Python web framework)
- **Backend**: Python 3.8+
- **Database**: MySQL
- **ORM**: SQLAlchemy
- **Data Processing**: Pandas

## 📦 Prerequisites

- Python 3.8 or higher
- MySQL Server (local or remote)
- Virtual environment (recommended)

## 🚀 Installation

1. **Clone the repository**:
   ```bash
   git clone <your-github-repo-url>
   cd qp_project
   ```

2. **Create and activate virtual environment**:
   ```bash
   # Windows (PowerShell)
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   
   # macOS/Linux
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**:
   Create a `.env` file in the project root or set via system environment variables:
   ```
   ADMIN_PASSWORD=your_secure_password_here
   ```

5. **Configure database**:
   - Ensure MySQL is running
   - Update the database URL in `dashboard.py` if using a remote database:
     ```python
     DB_URL = 'mysql+pymysql://username:password@host/database_name'
     ```
   - Default: `mysql+pymysql://root:abiR%403121@localhost/qp_generator`

## 🎯 Running the Application

```bash
# Ensure virtual environment is activated
streamlit run dashboard.py
```

The application will launch at `http://localhost:8501`

## 🔐 Login Credentials

- **Username**: `admin`
- **Password**: Set via the `ADMIN_PASSWORD` environment variable
- **Suggested Password**: `GNC!x7R3p#q2Z9mL6`

## 📁 Project Structure

```
qp_project/
├── dashboard.py           # Main application file
├── requirements.txt       # Python dependencies
├── README.md             # Project documentation
├── .gitignore            # Git ignore rules
└── uploads/              # Question paper uploads folder
```

## 🗂️ Database Models

### School
- id (Primary Key)
- name: School/Institution name
- departments: Related departments (one-to-many)

### Department
- id (Primary Key)
- school_id (Foreign Key)
- name: Department name
- level: 'UG', 'PG', or 'Ph.D'
- pattern_name: Curriculum pattern
- subjects: Related subjects (one-to-many)

### Subject
- id (Primary Key)
- dept_id (Foreign Key)
- name: Subject name
- code: Subject code
- semester: Semester number
- pattern_name: Curriculum pattern
- grid_type_id: Related grid type

### GridType
- id (Primary Key)
- name: Grid type name
- has_problem_column: Boolean flag

## 🎨 UI Sections

### Home Page
- Visual overview of departments with filtering options
- Filter by: All, UG, PG, or Ph.D levels
- Interactive department cards with hover effects

### Schools & Departments
- **Manage Schools**: Add, view, and delete schools
- **Manage Departments**: Create departments, manage department-school relationships
- Dependency checks prevent deletion of schools with linked departments

### Manage Subjects
- Add new subjects with department, code, semester, and grid type
- View all subjects in a data table
- Delete subjects with confirmation

### Downloads
- List recent uploaded question papers
- Download .docx files directly from the interface

## 🔧 Configuration

### Streamlit Settings
The app is configured with:
- Page title: "GNC Admin Dashboard"
- Page icon: 🎓
- Layout: Wide

### Dark Theme
Custom CSS provides dark-themed department cards with:
- Dark background (#262730)
- Hover animations
- Responsive grid layout

## ⚠️ Important Notes

1. **Security**: Never commit `.env` files or passwords to version control
2. **Database**: Ensure your MySQL database is running before starting the application
3. **Cascade Deletes**: Deleting a school cascades to related departments and subjects
4. **Password Management**: Always set the `ADMIN_PASSWORD` environment variable before deployment
5. **Upload Folder**: The `uploads/` folder will be created automatically if it doesn't exist

## 📝 License

This project is created for Guru Nanak College. Contact the admin for usage permissions.

## 👥 Support

For issues or feature requests, please contact the development team or create an issue in the repository.

---

**Last Updated**: January 2026