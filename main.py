import streamlit as st
from database import DatabaseManager
import pandas as pd
from datetime import datetime, date, timedelta
import plotly.express as px
import os

class MedicalPracticeApp:
    def __init__(self):
        """
        Initialize the application with database connection and styling
        """
        self.db = DatabaseManager()
        self.setup_streamlit()
        

    def setup_streamlit(self):
        """
        Configure Streamlit page settings 
        """
        st.set_page_config(
            page_title="Nani Health Clinic",
            layout="wide",
            initial_sidebar_state="expanded"
        )

    def run(self):
        """
        Run the main application
        """
        #  sidebar navigation
        with st.sidebar:
            st.title("Nani Health Clinic")
            st.subheader("Clinic Dashboard")
            page = st.radio(
                "",  # Empty label for cleaner look
                ["📊 Dashboard", "🏥 Patient Management", "👨‍⚕️ Staff Management", "💰 Financial Records"]
            )

        #  page matching
        page = page.split(" ")[1]

        if page == "Dashboard":
            self.dashboard_page()
        elif page == "Patient":
            self.patient_management_page()
        elif page == "Staff":
            self.staff_management_page()
        elif page == "Financial":
            self.financial_records_page()

    def patient_management_page(self):
        """
        Patient Management Page 
        """
        st.title("Patient Management")
        
        # Modern card layout for new patient form
        with st.expander("➕ Add New Patient"):
            cols = st.columns([1, 1])
            with st.form("new_patient_form"):
                with cols[0]:
                    name = st.text_input("Full Name")
                    contact = st.text_input("Contact Number")
                    email = st.text_input("Email Address")
                
                with cols[1]:
                    medical_history = st.text_area("Medical History")
                    
                    # Add doctor assignment dropdown
                    doctors = self.db.get_users()
                    if not doctors.empty:
                        # Filter to only doctors
                        doctors = doctors[doctors['role_name'] == 'doctor']
                        if not doctors.empty:
                            doctor_id = st.selectbox(
                                "Assign Doctor",
                                options=doctors['id'].tolist(),
                                format_func=lambda x: doctors[doctors['id'] == x]['full_name'].iloc[0]
                            )
                        else:
                            doctor_id = None
                            st.info("No doctors available in the system.")
                    else:
                        doctor_id = None
                
                submit = st.form_submit_button("Add Patient")
                
                if submit and name and contact:
                    self.db.add_patient(name, contact, email, medical_history, doctor_id)
                    st.success("✅ Patient added successfully!")

        #  search interface
        st.subheader("🔍 Search Patients")
        search_col1, search_col2 = st.columns([3, 1])
        with search_col1:
            search_term = st.text_input("", placeholder="Search by name or contact...", key="patient_search")
        
        if search_term:
            results = self.db.search_patients(search_term)
            st.dataframe(
                results,
                use_container_width=True,
                hide_index=True
            )
            
            # Generate patient report
            if not results.empty:
                st.download_button(
                    label="📄 Generate Patient Report",
                    data=results.to_csv().encode('utf-8'),
                    file_name=f'patient_report_{date.today()}.csv',
                    mime='text/csv',
                )
        
        # Display all patients if no search term
        else:
            all_patients = self.db.get_patients()
            if not all_patients.empty:
                st.subheader("All Patients")
                st.dataframe(
                    all_patients,
                    use_container_width=True,
                    hide_index=True
                )
                
                st.download_button(
                    label="📄 Generate All Patients Report",
                    data=all_patients.to_csv().encode('utf-8'),
                    file_name=f'all_patients_report_{date.today()}.csv',
                    mime='text/csv',
                )
        
        # Medical Records Section
        st.subheader("Medical Records")
        
        # Add medical record form
        with st.expander("➕ Add Medical Record"):
            with st.form("new_medical_record_form"):
                patients = self.db.get_patients()
                doctors = self.db.get_users()
                
                if not patients.empty and not doctors.empty:
                    # Filter to only doctors
                    doctors = doctors[doctors['role_name'] == 'doctor']
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        patient_id = st.selectbox(
                            "Select Patient",
                            options=patients['id'].tolist(),
                            format_func=lambda x: patients[patients['id'] == x]['name'].iloc[0]
                        )
                        
                        visit_date = st.date_input("Visit Date", value=date.today())
                    
                    with col2:
                        doctor_id = st.selectbox(
                            "Doctor",
                            options=doctors['id'].tolist(),
                            format_func=lambda x: doctors[doctors['id'] == x]['full_name'].iloc[0]
                        )
                    
                    diagnosis = st.text_area("Diagnosis")
                    treatment = st.text_area("Treatment")
                    notes = st.text_area("Additional Notes")
                    
                    submit = st.form_submit_button("Add Medical Record")
                    
                    if submit:
                        self.db.add_medical_record(
                            patient_id,
                            doctor_id,
                            visit_date,
                            diagnosis,
                            treatment,
                            notes
                        )
                        st.success("✅ Medical record added successfully!")
                else:
                    st.warning("No patients or doctors available. Please add them first.")
                    submit = st.form_submit_button("Add Medical Record", disabled=True)
                    
        # View medical records
        patients = self.db.get_patients()
        if not patients.empty:
            selected_patient = st.selectbox(
                "Select Patient to View Records",
                options=patients['id'].tolist(),
                format_func=lambda x: patients[patients['id'] == x]['name'].iloc[0]
            )
            
            records = self.db.get_medical_records(selected_patient)
            if not records.empty:
                st.dataframe(
                    records,
                    use_container_width=True,
                    hide_index=True
                )
                
                st.download_button(
                    label="📄 Generate Medical Records Report",
                    data=records.to_csv().encode('utf-8'),
                    file_name=f'medical_records_{patients[patients.id == selected_patient].name.iloc[0]}_{date.today()}.csv',
                    mime='text/csv',
                )
            else:
                st.info("No medical records found for this patient.")
        else:
            st.warning("No patients available. Please add patients first.")

    def staff_management_page(self):
        """
        Staff Management Page for managing medical staff (users)
        """
        st.title("Staff Management")
        
        # Add new staff form
        with st.expander("➕ Add New Staff Member"):
            cols = st.columns([1, 1])
            with st.form("new_staff_form"):
                with cols[0]:
                    username = st.text_input("Username")
                    password = st.text_input("Password", type="password")
                    full_name = st.text_input("Full Name")
                    
                    # Get roles for dropdown
                    roles = self.db.get_roles()
                    if not roles.empty:
                        role_id = st.selectbox(
                            "Role",
                            options=roles['id'].tolist(),
                            format_func=lambda x: roles[roles['id'] == x]['role_name'].iloc[0]
                        )
                    else:
                        role_id = None
                        st.error("No roles found in database.")
                
                with cols[1]:
                    email = st.text_input("Email")
                    phone = st.text_input("Phone")
                    specialty = st.text_input("Specialty (for doctors)")
                
                submit = st.form_submit_button("Add Staff Member")
                
                if submit and username and password and full_name and role_id:
                    self.db.add_user(username, password, full_name, role_id, email, phone, specialty)
                    st.success("✅ Staff member added successfully!")
        
        # Search staff
        st.subheader("🔍 Search Staff")
        search_col1, search_col2 = st.columns([3, 1])
        with search_col1:
            search_term = st.text_input("", placeholder="Search by name, username, or role...", key="staff_search")
        
        if search_term:
            results = self.db.search_users(search_term)
            if not results.empty:
                st.dataframe(
                    results[['id', 'username', 'full_name', 'role_name', 'email', 'phone', 'specialty']],
                    use_container_width=True,
                    hide_index=True
                )
                
                st.download_button(
                    label="📄 Generate Staff Report",
                    data=results.to_csv().encode('utf-8'),
                    file_name=f'staff_report_{date.today()}.csv',
                    mime='text/csv',
                )
            else:
                st.info("No staff members found matching your search.")
        
        # Display all staff if no search term
        else:
            all_users = self.db.get_users()
            if not all_users.empty:
                st.subheader("All Staff Members")
                
                # Group staff by role
                role_groups = all_users.groupby('role_name')
                
                for role_name, group in role_groups:
                    with st.expander(f"{role_name.capitalize()} ({len(group)})"):
                        st.dataframe(
                            group[['id', 'username', 'full_name', 'email', 'phone', 'specialty']],
                            use_container_width=True,
                            hide_index=True
                        )
                
                st.download_button(
                    label="📄 Generate Complete Staff Report",
                    data=all_users.to_csv().encode('utf-8'),
                    file_name=f'all_staff_report_{date.today()}.csv',
                    mime='text/csv',
                )
            else:
                st.warning("No staff members found in the system.")

    def financial_records_page(self):
        """
         Financial Records Page 
        """
        st.title("Financial Records")
        
        #  financial form with columns
        with st.form("income_form"):
            st.subheader("Record Payment")
            cols = st.columns([1, 1, 1])
            
            with cols[0]:
                amount = st.number_input("Amount ($)", min_value=0.0, format="%.2f")
            
            patients = self.db.get_patients()
            if not patients.empty:
                with cols[1]:
                    patient_id = st.selectbox(
                        "Select Patient",
                        options=patients['id'].tolist(),
                        format_func=lambda x: patients[patients['id'] == x]['name'].iloc[0]
                    )
                with cols[2]:
                    description = st.text_input("Payment Description")
                    
                    # Add staff who recorded the payment
                    staff = self.db.get_users()
                    if not staff.empty:
                        recorded_by_id = st.selectbox(
                            "Recorded By",
                            options=staff['id'].tolist(),
                            format_func=lambda x: staff[staff['id'] == x]['full_name'].iloc[0]
                        )
                    else:
                        recorded_by_id = None
                
                submit = st.form_submit_button("Record Payment")
                
                if submit and amount > 0:
                    self.db.record_income(
                        date.today(),
                        amount,
                        description,
                        patient_id,
                        recorded_by_id
                    )
                    st.success("✅ Payment recorded successfully!")
            else:
                st.warning("No patients available. Please add patients first.")
                submit = st.form_submit_button("Record Payment", disabled=True)
        
        # View financial records
        st.subheader("View Financial Records")
        
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("Start Date", value=date.today() - timedelta(days=30))
        with col2:
            end_date = st.date_input("End Date", value=date.today())
        
        if start_date <= end_date:
            records = self.db.get_financial_records(
                start_date.strftime('%Y-%m-%d'),
                end_date.strftime('%Y-%m-%d')
            )
            
            if not records.empty:
                # Display total income
                total_income = records['amount'].sum()
                st.metric("Total Income", f"${total_income:.2f}")
                
                # Display financial records
                st.dataframe(
                    records,
                    use_container_width=True,
                    hide_index=True
                )
                
                # Generate financial report
                st.download_button(
                    label="📄 Generate Financial Report",
                    data=records.to_csv().encode('utf-8'),
                    file_name=f'financial_report_{start_date}_to_{end_date}.csv',
                    mime='text/csv',
                )
            else:
                st.info(f"No financial records found between {start_date} and {end_date}.")
        else:
            st.error("Start date must be before end date.")

    def dashboard_page(self):
        """
        Dashboard Page with summary metrics and visualizations
        """
        st.title("Clinic Dashboard")
        
        # Summary metrics
        st.subheader("Summary Metrics")
        col1, col2, col3, col4 = st.columns(4)
        
        # Get patient count
        patients = self.db.get_patients()
        patient_count = len(patients) if not patients.empty else 0
        
        # Get staff count
        staff = self.db.get_users()
        staff_count = len(staff) if not staff.empty else 0
        
        # Get doctor count
        doctors_count = len(staff[staff['role_name'] == 'doctor']) if not staff.empty else 0
        
        # Get financial data for the current month
        first_day = date.today().replace(day=1)
        monthly_finances = self.db.get_financial_records(
            first_day.strftime('%Y-%m-%d'),
            date.today().strftime('%Y-%m-%d')
        )
        
        monthly_income = monthly_finances['amount'].sum() if not monthly_finances.empty else 0
        
        with col1:
            st.metric("Total Patients", patient_count)
        
        with col2:
            st.metric("Medical Staff", staff_count)
            
        with col3:
            st.metric("Doctors", doctors_count)
        
        with col4:
            st.metric("Monthly Income", f"${monthly_income:.2f}")
        
        # Charts and visualizations
        st.subheader("Financial Overview")
        
        # Get data for the last 30 days
        thirty_days_ago = date.today() - timedelta(days=30)
        financial_data = self.db.get_financial_records(
            thirty_days_ago.strftime('%Y-%m-%d'),
            date.today().strftime('%Y-%m-%d')
        )
        
        if not financial_data.empty:
            # Convert date strings to datetime objects
            financial_data['date'] = pd.to_datetime(financial_data['date'])
            
            # Group by date and sum amounts
            daily_income = financial_data.groupby('date')['amount'].sum().reset_index()
            
            # Create a bar chart of daily income
            fig = px.bar(
                daily_income, 
                x='date', 
                y='amount',
                labels={'date': 'Date', 'amount': 'Amount ($)'},
                title='Daily Income (Last 30 Days)'
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Staff efficiency
            col1, col2 = st.columns(2)
            
            with col1:
                # Patient distribution pie chart
                patient_distribution = financial_data.groupby('patient_name')['amount'].sum().reset_index()
                patient_distribution = patient_distribution.sort_values('amount', ascending=False).head(10)
                
                fig2 = px.pie(
                    patient_distribution, 
                    values='amount', 
                    names='patient_name',
                    title='Top 10 Patients by Revenue'
                )
                
                st.plotly_chart(fig2, use_container_width=True)
            
            with col2:
                # Staff performance if recorded_by data is available
                if 'recorded_by' in financial_data.columns and financial_data['recorded_by'].notna().any():
                    staff_performance = financial_data.groupby('recorded_by')['amount'].sum().reset_index()
                    staff_performance = staff_performance.sort_values('amount', ascending=False)
                    
                    fig3 = px.bar(
                        staff_performance,
                        x='recorded_by',
                        y='amount',
                        title='Staff Performance (Revenue Recorded)'
                    )
                    
                    st.plotly_chart(fig3, use_container_width=True)
        else:
            st.info("No financial data available for the last 30 days.")
            
        # Recent patients
        st.subheader("Recent Patients")
        if not patients.empty:
            # Sort by most recently added
            recent_patients = patients.sort_values('id', ascending=False).head(5)
            st.dataframe(
                recent_patients[['name', 'contact', 'email', 'doctor_name']],
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("No patients in the system yet.")

if __name__ == "__main__":
    app = MedicalPracticeApp()
    app.run()