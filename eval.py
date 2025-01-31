import streamlit as st
import mysql.connector
import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from fpdf import FPDF
import re

# Database configuration
host = "82.180.143.66"
user = "u263681140_students"
passwd = "testStudents@123"
db_name = "u263681140_students"
# Function to check admin credentials
conn = mysql.connector.connect(
    host=host,
    user=user,
    password=passwd,
    database=db_name,
    #pool_name=None  # Disabling connection pooling
)
# Function to connect to MySQL database
def get_db_connection():
    return mysql.connector.connect(
        host= "82.180.143.66",
        user="u263681140_students",
        password="testStudents@123",
        database="u263681140_students"
    )

# Function to fetch data from a table
def fetch_data(table_name):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(f"SELECT * FROM {table_name}")
        data = cursor.fetchall()
        cursor.close()
        conn.close()
        return data
    except Exception as e:
        st.error(f"Database error: {e}")
        return []
def check_admin_login(email, password):
    try:
        conn = mysql.connector.connect(
            host=host,
            user=user,
            password=passwd,
            database=db_name
        )
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM admin WHERE mail = %s AND password = %s",
            (email, password)
        )
        return cursor.fetchone() is not None
    except mysql.connector.Error as err:
        st.error(f"Database error: {err}")
        return False
    finally:
        if 'conn' in locals() and conn.is_connected():
            cursor.close()
            conn.close()
def adminLogin():
    # Initialize session state
    if "page" not in st.session_state:
        st.session_state["page"] = "login"

    if st.session_state["page"] == "login":
        with st.form("admin_form"):
            st.subheader("🧑💼 Administrator Login")
            email = st.text_input("Admin Email")
            password = st.text_input("Admin Password", type="password")
            submit = st.form_submit_button("Login")

            if submit:
                if check_admin_login(email, password):
                    st.session_state.update({"page": "admin_dash", "role": "admin"})
                    st.success("Admin login successful!")
                    st.rerun()
                else:
                    st.error("Invalid admin credentials")

    elif st.session_state["page"] == "admin_dash":
        st.title("Administrator Dashboard")

        # Horizontal radio buttons
        selected_option = st.radio(
            "Select Data to View:",
            ["Students", "Teachers","Check Marks"],
            horizontal=True,
            key="admin_view"
        )

        if selected_option == "Students":
            st.subheader("📚 Student Records")
            student_data = fetch_data("students")
            if student_data:
                df = pd.DataFrame(student_data)
                st.dataframe(df)
            else:
                st.warning("No student data found in the database.")

        elif selected_option == "Teachers":
            st.subheader("👩🏫 Teacher Records")
            teacher_data = fetch_data("teacher")
            if teacher_data:
                df = pd.DataFrame(teacher_data)
                st.dataframe(df)
            else:
                st.warning("No teacher data found in the database.")

        # Add logout button at bottom
        st.markdown("---")
        if st.button("🚪 Logout"):
            st.session_state.clear()
            st.session_state["page"] = "login"
            st.rerun()

def RegisterUser():
    branches = [
        "Computer Science", 
        "Mechanical Engineering", 
        "Electrical Engineering", 
        "Civil Engineering", 
        "Electronics and Communication", 
        "Information Technology",
        "Chemical Engineering", 
        "Aerospace Engineering"
    ]
    st.title("Registration Form")

    registration_type = st.selectbox("Select Registration Type", ["Teacher", "Student"])

    with st.form("registration_form"):
        if registration_type == "Teacher":
            name = st.text_input("Name")
            mail = st.text_input("Email")
            mobile = st.text_input("Mobile Number")
            password = st.text_input("Password", type="password")
            branch = st.selectbox("Branch", branches)  
            submitted = st.form_submit_button("Register")

            if submitted:
                if name and mail and mobile and password and branch:
                    if not is_valid_email(mail):
                        st.warning("Please enter a valid email address!")
                    elif not is_valid_mobile(mobile):
                        st.warning("Mobile number must be 10 digits!")
                    else:
                        insert_teacher(name, mail, mobile, password, branch)
                else:
                    st.warning("Please fill all the fields!")
        
        elif registration_type == "Student":
            name = st.text_input("Name")
            enrolment = st.text_input("Enrolment Number")
            mail = st.text_input("Email")
            mobile = st.text_input("Mobile Number")
            password = st.text_input("Password", type="password")
            branch = st.selectbox("Branch", branches) 
            submitted = st.form_submit_button("Register")

            if submitted:
                if name and enrolment and mail and mobile and password and branch:
                    if not is_valid_email(mail):
                        st.warning("Please enter a valid email address!")
                    elif not is_valid_mobile(mobile):
                        st.warning("Mobile number must be 10 digits!")
                    else:
                        insert_student(name, enrolment, mail, mobile, password, branch)
                else:
                    st.warning("Please fill all the fields!")

def is_valid_email(email):
    pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    return re.match(pattern, email) is not None

def is_valid_mobile(mobile):
    pattern = r'^\d{10}$'
    return re.match(pattern, mobile) is not None
def teacher_email_exists(mail):
    db, cur = None, None
    try:
        db = mysql.connector.connect(host=host, user=user, password=passwd, database=db_name)
        cur = db.cursor()
        cur.execute("SELECT * FROM teacher WHERE mail = %s", (mail,))
        return cur.fetchone() is not None
    finally:
        if cur:
            cur.close()
        if db:
            db.close()

def student_exists(mail, enrolment):
    db, cur = None, None
    try:
        db = mysql.connector.connect(host=host, user=user, password=passwd, database=db_name)
        cur = db.cursor()
        cur.execute("SELECT * FROM students WHERE email = %s OR enrolment = %s", (mail, enrolment))
        return cur.fetchone() is not None
    finally:
        if cur:
            cur.close()
        if db:
            db.close()
def insert_teacher(name, mail, mobile, password, branch):
    db, cur = None, None
    try:
        if teacher_email_exists(mail):
            st.warning("Email already exists for another teacher!")
            return

        db = mysql.connector.connect(host=host, user=user, password=passwd, database=db_name)
        cur = db.cursor()

        insert_query = '''INSERT INTO teacher (name, mail, mobile, password, branch) 
                          VALUES (%s, %s, %s, %s, %s);'''
        cur.execute(insert_query, (name, mail, mobile, password, branch))
        db.commit()
        st.success("Teacher registered successfully!")

    except Exception as e:
        st.error(f"Error: {e}")

    finally:
        if cur:
            cur.close()
        if db:
            db.close()

def insert_student(name, enrolment, mail, mobile, password, branch):
    db, cur = None, None
    try:
        if student_exists(mail, enrolment):
            st.warning("Email or enrolment number already exists for another student!")
            return

        db = mysql.connector.connect(host=host, user=user, password=passwd, database=db_name)
        cur = db.cursor()

        insert_query = '''INSERT INTO students (name, enrolment, email, mobile, password, branch) 
                          VALUES (%s, %s, %s, %s, %s, %s);'''
        cur.execute(insert_query, (name, enrolment, mail, mobile, password, branch))
        db.commit()
        st.success("Student registered successfully!")

    except Exception as e:
        st.error(f"Error: {e}")

    finally:
        if cur:
            cur.close()
        if db:
            db.close()
def evaluate_answers(correct_answers, student_answers):
    vectorizer = TfidfVectorizer()
    marks_obtained = []
    
    for index, row in student_answers.iterrows():
        question_id = row['Question']
        student_answer = row['Answers']

        correct_answer_row = correct_answers[correct_answers['Question'] == question_id]
        if correct_answer_row.empty:
            marks_obtained.append(0)
            continue
        
        correct_answer = correct_answer_row['Answer'].values[0]
        max_marks = correct_answer_row['Marks'].values[0]
        
        combined_text = [correct_answer, student_answer]
        vectors = vectorizer.fit_transform(combined_text)
        similarity = cosine_similarity(vectors[0:1], vectors[1:2])[0][0]
        
        if similarity > 0.9:
            assigned_marks = max_marks
        elif similarity > 0.75:
            assigned_marks = max_marks * 0.9
        elif similarity > 0.5:
            assigned_marks = max_marks * 0.75
        elif similarity > 0.3:
            assigned_marks = max_marks * 0.5
        else:
            assigned_marks = max_marks * similarity

        marks_obtained.append(int(np.ceil(assigned_marks)))
    
    student_answers['Marks_Obtained'] = marks_obtained
    return student_answers

def check_teacher_login(email, password):
    try:
        db = mysql.connector.connect(host=host, user=user, password=passwd, database=db_name)
        cur = db.cursor()
        cur.execute("SELECT * FROM teacher WHERE mail = %s AND password = %s", (email, password))
        return cur.fetchone() is not None
    except Exception as e:
        st.error(f"Database error: {e}")
        return False
    finally:
        if 'db' in locals(): db.close()
def check_student_login(email, password):
    try:
        db = mysql.connector.connect(host=host, user=user, password=passwd, database=db_name)
        cur = db.cursor()
        cur.execute("SELECT * FROM students WHERE email = %s AND password = %s", (email, password))
        return cur.fetchone() is not None
    except Exception as e:
        st.error(f"Database error: {e}")
        return False
    finally:
        if 'db' in locals(): db.close()
def check_admin_login(email, password):
    try:
        db = mysql.connector.connect(host=host, user=user, password=passwd, database=db_name)
        cur = db.cursor()
        cur.execute("SELECT * FROM admin WHERE mail = %s AND password = %s", (email, password))
        return cur.fetchone() is not None
    except Exception as e:
        st.error(f"Database error: {e}")
        return False
    finally:
        if 'db' in locals(): db.close()

# -------------------- DASHBOARDS --------------------
def teacher_dashboard():
    st.title("📊 Teacher Dashboard")
    if st.button("🔴 Logout"):
        st.session_state.update({"page": "login", "logged_in": False})
        st.rerun()

    correct_file = st.file_uploader("Upload Correct Answers CSV", type=["csv"])
    student_file = st.file_uploader("Upload Student Answers CSV", type=["csv"])
    
    if correct_file and student_file:
        correct_answers = pd.read_csv(correct_file)
        student_answers = pd.read_csv(student_file)
        
        results = evaluate_answers(correct_answers, student_answers)
        total_marks = results['Marks_Obtained'].sum()
        max_marks = correct_answers['Marks'].sum()
        
        st.subheader("Evaluation Results")
        st.dataframe(results[['Question', 'Answers', 'Marks_Obtained']])
        st.markdown(f"**Total Marks: {total_marks}/{max_marks}**")
        
        csv = results.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Download Results", csv, "results.csv", "text/csv")
def fetch_student_info(email):

    """Fetch student information from database using email"""
    conn = None
    cursor = None
    try:
        # Use existing database configuration
        conn = mysql.connector.connect(
            host=host,
            user=user,
            password=passwd,
            database=db_name
        )
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT name, enrolment, email, mobile, branch FROM students WHERE email = %s", 
            (email,)
        )
        return cursor.fetchone()
    except Exception as e:
        st.error(f"Database error: {e}")
        return None
    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()
def adminDashboard():
    #st.title("👑 Administrator Dashboard")

    # Horizontal radio buttons for navigation
    selected_option = st.radio(
        "Select Data to View:",
        ["Result Details", "Teacher Details", "Student Details"],
        horizontal=True,
        key="admin_view"
    )

    if selected_option == "Result Details":
        st.subheader("📊 Result Records")
        result_data =0
        #result_data = fetch_data("results")  # Assuming you have a 'results' table
        if result_data:
            df = pd.DataFrame(result_data)
            st.dataframe(df)
        else:
            st.warning("No result data found in the database.")

    elif selected_option == "Teacher Details":
        st.subheader("👩🏫 Teacher Records")
        teacher_data = fetch_data("teacher")
        if teacher_data:
            df = pd.DataFrame(teacher_data)
            st.dataframe(df)
        else:
            st.warning("No teacher data found in the database.")

    elif selected_option == "Student Details":
        st.subheader("📚 Student Records")
        student_data = fetch_data("students")
        if student_data:
            df = pd.DataFrame(student_data)
            st.dataframe(df)
        else:
            st.warning("No student data found in the database.")

def admin_dashboard():
    st.title("👑 Admin Dashboard")
    adminDashboard()
    if st.button("🔴 Logout"):
        st.session_state.update({"page": "login", "logged_in": False})
        st.rerun()

    #st.write("Admin functionality for answer evaluation")
def HomePage():
    st.image("background.jpg", use_container_width=True, caption="Automated Answer Evaluation System")
    background_image_url = "https://www.freepik.com/free-vector/abstract-blue-circle-black-background-technology_34386132.htm#fromView=keyword&page=1&position=12&uuid=dc1355a0-023d-44c3-987d-ba1e0a8270b6&new_detail=true&query=Dark+Website+Background"  # Update with your image URL
 
    # Footer
    st.markdown("""
        <div style="text-align: center; margin-top: 50px; font-size: 14px; color: white;">
            &copy; 2025 Automated Answer Evaluation System. All Rights Reserved.
        </div>
    """, unsafe_allow_html=True)
# -------------------- MAIN PAGE TABS --------------------
def login_page():
    st.title("📚 Automated Answer Evaluation System")
    tab1, tab2, tab3, tab4 = st.tabs(["Home","Login", "Signup", "Admin Login"])
    with tab1:
        HomePage()
    with tab2:
        col1, col2 = st.columns([2, 3])
        with col1:
            # Display the image
            st.markdown("<br><br><br>", unsafe_allow_html=True)
            st.image("nlp2.jpg", use_container_width=True, caption="Automated Answer Evaluation System")
        
        with col2:
            st.header("User Login")
            login_type = st.selectbox("Select Role", ["Teacher", "Student"], key="login_role")
            
            with st.form("login_form"):
                global global_var
                email = st.text_input("Email")
                password = st.text_input("Password", type="password")
                submit = st.form_submit_button("Login")
                if submit:
                    if login_type == "Teacher":
                        if check_teacher_login(email, password):
                            st.session_state.update({"page": "teacher_dash", "role": "teacher"})
                            st.success("Login successful!")
                            st.rerun()
                        else:
                            st.error("Invalid credentials")
                    elif login_type == "Student":
                        if check_student_login(email, password):
                            st.session_state["email"] = email 
                            st.session_state.update({"page": "student_dash", "role": "student"})
                            st.success("Login successful!")
                            st.rerun()
                        else:
                            st.error("Invalid credentials")

                    else:
                        st.warning("Student login not implemented yet")

    with tab3:
        RegisterUser()
    with tab4:
        #st.header("Administrator Login")
        adminLogin()
# -------------------- APP FLOW CONTROL --------------------
if "page" not in st.session_state:
    st.session_state.update({
        "page": "login",
        "logged_in": False,
        "role": None
    })

if(__name__ == "__main__"):
    #login_page()
    if st.session_state.page == "login":
        login_page()
    elif st.session_state.page == "teacher_dash":
        teacher_dashboard()
    elif st.session_state.get("page") == "student_dash":
        st.header("Student Dashboard")
        email = st.session_state.get("email")
        #st.write("Well Come:", email)
        student_info = fetch_student_info(email)
        if student_info:
            st.subheader("Student Dashboard")
            
            # Create radio buttons for navigation
            selected_tab = st.radio("Select View", ["Profile", "Marks"], horizontal=True)
            
            if selected_tab == "Profile":
                # Convert student info to DataFrame and display in table format
                profile_df = pd.DataFrame([{
                    "Name": student_info['name'],
                    "Enrolment": student_info['enrolment'],
                    "Email": student_info['email'],
                    "Mobile": student_info['mobile'],
                    "Branch": student_info['branch']
                }])
                
                st.write("### Student Profile")
                st.dataframe(profile_df,
                            use_container_width=True,
                            hide_index=True,
                            column_config={
                                "Name": "Student Name",
                                "Enrolment": "Enrollment Number"
                            })
                
            else:
                st.write("### Marks Information")
                st.info("Marks details will be displayed here once available")
            if st.button("🔴 Logout"):
                st.session_state.update({"page": "login", "logged_in": False})
                st.rerun()

        else:
            st.error("Student information not found")
    elif st.session_state.page == "admin_dash":
        admin_dashboard()
