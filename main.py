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
                ["📊 Dashboard", "🏥 Patient Management", "👨‍⚕️ Staff Management", "📅 Appointments", "💰 Financial Records"]
            )

        #  page matching
        page = page.split(" ")[1]

        if page == "Dashboard":
            self.dashboard_page()
        elif page == "Patient":
            self.patient_management_page()
        elif page == "Staff":
            self.staff_management_page()
        elif page == "Appointments":
            self.appointments_page()
        elif page == "Financial":
            self.financial_records_page()

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
        
        # Get appointment count for today
        today_appointments = self.db.get_appointments(date.today().strftime('%Y-%m-%d'))
        appointment_count = len(today_appointments) if not today_appointments.empty else 0
        
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
            st.metric("Today's Appointments", appointment_count)
        
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
            
        # Today's appointments
        st.subheader("Today's Appointments")
        if not today_appointments.empty:
            # Format the appointment_date column for better display
            today_appointments['appointment_date'] = pd.to_datetime(today_appointments['appointment_date'])
            today_appointments['time'] = today_appointments['appointment_date'].dt.strftime('%I:%M %p')
            
            st.dataframe(
                today_appointments[['patient_name', 'time', 'reason', 'status', 'assigned_to']],
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("No appointments scheduled for today.")

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
            if not results.empty:
                # Display patients with edit and delete buttons
                for index, row in results.iterrows():
                    with st.container():
                        col1, col2, col3 = st.columns([4, 1, 1])
                        with col1:
                            st.write(f"**{row['name']}** - {row['contact']} ({row['email']})")
                        with col2:
                            if st.button("Edit", key=f"edit_{row['id']}"):
                                st.session_state.patient_to_edit = row['id']
                        with col3:
                            if st.button("Delete", key=f"delete_{row['id']}"):
                                self.db.delete_patient(row['id'])
                                st.success(f"Patient {row['name']} deleted successfully!")
                                st.rerun()
                
                # Display patient edit form if selected
                if hasattr(st.session_state, 'patient_to_edit'):
                    patient_id = st.session_state.patient_to_edit
                    patient_data = results[results['id'] == patient_id].iloc[0]
                    
                    st.subheader(f"Edit Patient: {patient_data['name']}")
                    with st.form("edit_patient_form"):
                        cols = st.columns([1, 1])
                        with cols[0]:
                            edit_name = st.text_input("Full Name", value=patient_data['name'])
                            edit_contact = st.text_input("Contact Number", value=patient_data['contact'])
                            edit_email = st.text_input("Email Address", value=patient_data['email'])
                        
                        with cols[1]:
                            edit_medical_history = st.text_area("Medical History", value=patient_data['medical_history'] if 'medical_history' in patient_data else "")
                            
                            # Doctor assignment dropdown
                            doctors = self.db.get_users()
                            if not doctors.empty:
                                # Filter to only doctors
                                doctors = doctors[doctors['role_name'] == 'doctor']
                                if not doctors.empty:
                                    current_doctor_id = patient_data['doctor_id'] if 'doctor_id' in patient_data else None
                                    edit_doctor_id = st.selectbox(
                                        "Assign Doctor",
                                        options=doctors['id'].tolist(),
                                        format_func=lambda x: doctors[doctors['id'] == x]['full_name'].iloc[0],
                                        index=doctors['id'].tolist().index(current_doctor_id) if current_doctor_id in doctors['id'].tolist() else 0
                                    )
                                else:
                                    edit_doctor_id = None
                            else:
                                edit_doctor_id = None
                        
                        save_changes = st.form_submit_button("Save Changes")
                        cancel = st.form_submit_button("Cancel")
                        
                        if save_changes:
                            self.db.update_patient(
                                patient_id, 
                                edit_name, 
                                edit_contact, 
                                edit_email, 
                                edit_medical_history, 
                                edit_doctor_id
                            )
                            st.success("✅ Patient updated successfully!")
                            del st.session_state.patient_to_edit
                            st.rerun()
                        
                        if cancel:
                            del st.session_state.patient_to_edit
                            st.rerun()
                
                # Generate patient report
                st.download_button(
                    label="📄 Generate Patient Report",
                    data=results.to_csv().encode('utf-8'),
                    file_name=f'patient_report_{date.today()}.csv',
                    mime='text/csv',
                )
            else:
                st.info("No patients found matching your search.")
        
        # Display all patients if no search term
        else:
            all_patients = self.db.get_patients()
            if not all_patients.empty:
                st.subheader("All Patients")
                
                # Display patients with edit and delete buttons
                for index, row in all_patients.iterrows():
                    with st.container():
                        col1, col2, col3 = st.columns([4, 1, 1])
                        with col1:
                            st.write(f"**{row['name']}** - {row['contact']} ({row['email']})")
                        with col2:
                            if st.button("Edit", key=f"edit_all_{row['id']}"):
                                st.session_state.patient_to_edit = row['id']
                        with col3:
                            if st.button("Delete", key=f"delete_all_{row['id']}"):
                                self.db.delete_patient(row['id'])
                                st.success(f"Patient {row['name']} deleted successfully!")
                                st.rerun()
                
                # Generate report button
                st.download_button(
                    label="📄 Generate All Patients Report",
                    data=all_patients.to_csv().encode('utf-8'),
                    file_name=f'all_patients_report_{date.today()}.csv',
                    mime='text/csv',
                )
            else:
                st.warning("No patients found in the system.")
        
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
                for index, record in records.iterrows():
                    with st.container():
                        col1, col2, col3 = st.columns([4, 1, 1])
                        with col1:
                            st.write(f"**Visit Date:** {record['visit_date']} - **Dr.** {record['doctor_name']}")
                            st.write(f"**Diagnosis:** {record['diagnosis']}")
                            with st.expander("Treatment and Notes"):
                                st.write(f"**Treatment:** {record['treatment']}")
                                st.write(f"**Notes:** {record['notes']}")
                        with col2:
                            if st.button("Edit", key=f"edit_record_{record['id']}"):
                                st.session_state.record_to_edit = record['id']
                        with col3:
                            if st.button("Delete", key=f"delete_record_{record['id']}"):
                                self.db.delete_medical_record(record['id'])
                                st.success("Medical record deleted successfully!")
                                st.rerun()
                
                # Edit medical record form if a record is selected
                if hasattr(st.session_state, 'record_to_edit'):
                    record_id = st.session_state.record_to_edit
                    record_data = records[records['id'] == record_id].iloc[0]
                    
                    st.subheader(f"Edit Medical Record")
                    with st.form("edit_medical_record_form"):
                        cols = st.columns([1, 1])
                        with cols[0]:
                            doctors = self.db.get_users()
                            doctors = doctors[doctors['role_name'] == 'doctor']
                            
                            edit_doctor_id = st.selectbox(
                                "Doctor",
                                options=doctors['id'].tolist(),
                                format_func=lambda x: doctors[doctors['id'] == x]['full_name'].iloc[0],
                                index=doctors['id'].tolist().index(record_data['doctor_id']) if record_data['doctor_id'] in doctors['id'].tolist() else 0
                            )
                            
                            edit_visit_date = st.date_input("Visit Date", value=pd.to_datetime(record_data['visit_date']).date())
                        
                        with cols[1]:
                            edit_diagnosis = st.text_area("Diagnosis", value=record_data['diagnosis'])
                            
                        edit_treatment = st.text_area("Treatment", value=record_data['treatment'])
                        edit_notes = st.text_area("Additional Notes", value=record_data['notes'])
                        
                        save_changes = st.form_submit_button("Save Changes")
                        cancel = st.form_submit_button("Cancel")
                        
                        if save_changes:
                            self.db.update_medical_record(
                                record_id,
                                record_data['patient_id'],
                                edit_doctor_id,
                                edit_visit_date,
                                edit_diagnosis,
                                edit_treatment,
                                edit_notes
                            )
                            st.success("✅ Medical record updated successfully!")
                            del st.session_state.record_to_edit
                            st.rerun()
                        
                        if cancel:
                            del st.session_state.record_to_edit
                            st.rerun()
                
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
                # Display staff with edit and delete buttons
                for index, row in results.iterrows():
                    with st.container():
                        col1, col2, col3 = st.columns([4, 1, 1])
                        with col1:
                            st.write(f"**{row['full_name']}** - {row['role_name']} ({row['email']})")
                        with col2:
                            if st.button("Edit", key=f"edit_staff_{row['id']}"):
                                st.session_state.staff_to_edit = row['id']
                        with col3:
                            if st.button("Delete", key=f"delete_staff_{row['id']}"):
                                self.db.delete_user(row['id'])
                                st.success(f"Staff member {row['full_name']} deleted successfully!")
                                st.rerun()
                
                # Display staff edit form if selected
                if hasattr(st.session_state, 'staff_to_edit'):
                    staff_id = st.session_state.staff_to_edit
                    staff_data = results[results['id'] == staff_id].iloc[0]
                    
                    st.subheader(f"Edit Staff Member: {staff_data['full_name']}")
                    with st.form("edit_staff_form"):
                        cols = st.columns([1, 1])
                        with cols[0]:
                            edit_username = st.text_input("Username", value=staff_data['username'])
                            edit_password = st.text_input("Password (leave blank to keep current)", type="password")
                            edit_full_name = st.text_input("Full Name", value=staff_data['full_name'])
                            
                            # Get roles for dropdown
                            roles = self.db.get_roles()
                            if not roles.empty:
                                edit_role_id = st.selectbox(
                                    "Role",
                                    options=roles['id'].tolist(),
                                    format_func=lambda x: roles[roles['id'] == x]['role_name'].iloc[0],
                                    index=roles['id'].tolist().index(staff_data['role_id']) if staff_data['role_id'] in roles['id'].tolist() else 0
                                )
                            else:
                                edit_role_id = None
                        
                        with cols[1]:
                            edit_email = st.text_input("Email", value=staff_data['email'])
                            edit_phone = st.text_input("Phone", value=staff_data['phone'])
                            edit_specialty = st.text_input("Specialty", value=staff_data['specialty'] if 'specialty' in staff_data else "")
                        
                        save_changes = st.form_submit_button("Save Changes")
                        cancel = st.form_submit_button("Cancel")
                        
                        if save_changes:
                            self.db.update_user(
                                staff_id,
                                edit_username,
                                edit_password,
                                edit_full_name,
                                edit_role_id,
                                edit_email,
                                edit_phone,
                                edit_specialty
                            )
                            st.success("✅ Staff member updated successfully!")
                            del st.session_state.staff_to_edit
                            st.rerun()
                        
                        if cancel:
                            del st.session_state.staff_to_edit
                            st.rerun()
                
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
                        for index, row in group.iterrows():
                            with st.container():
                                col1, col2, col3 = st.columns([4, 1, 1])
                                with col1:
                                    st.write(f"**{row['full_name']}** - {row['email']} ({row['phone']})")
                                    if row['specialty']:
                                        st.write(f"*Specialty: {row['specialty']}*")
                                with col2:
                                    if st.button("Edit", key=f"edit_all_staff_{row['id']}"):
                                        st.session_state.staff_to_edit = row['id']
                                with col3:
                                    if st.button("Delete", key=f"delete_all_staff_{row['id']}"):
                                        self.db.delete_user(row['id'])
                                        st.success(f"Staff member {row['full_name']} deleted successfully!")
                                        st.rerun()
                
                st.download_button(
                    label="📄 Generate Complete Staff Report",
                    data=all_users.to_csv().encode('utf-8'),
                    file_name=f'all_staff_report_{date.today()}.csv',
                    mime='text/csv',
                )
            else:
                st.warning("No staff members found in the system.")

    def appointments_page(self):
        """
         Appointments Page 
        """
        st.title("Appointments")
        
        # appointment scheduling form
        cols = st.columns([2, 1])
        with cols[0]:
            with st.form("new_appointment_form"):
                st.subheader("Schedule New Appointment")
                patients = self.db.get_patients()
                staff = self.db.get_users()
                
                if not patients.empty and not staff.empty:
                    # Filter to only doctors and nurses
                    medical_staff = staff[(staff['role_name'] == 'doctor') | (staff['role_name'] == 'nurse')]
                    
                    patient_id = st.selectbox(
                        "Select Patient",
                        options=patients['id'].tolist(),
                        format_func=lambda x: patients[patients['id'] == x]['name'].iloc[0]
                    )
                    
                    assigned_to = st.selectbox(
                        "Assign to Staff Member",
                        options=medical_staff['id'].tolist(),
                        format_func=lambda x: f"{medical_staff[medical_staff['id'] == x]['full_name'].iloc[0]} ({medical_staff[medical_staff['id'] == x]['role_name'].iloc[0]})"
                    )
                    
                    date_col, time_col = st.columns(2)
                    with date_col:
                        appointment_date = st.date_input("Date")
                    with time_col:
                        appointment_time = st.time_input("Time")
                    
                    reason = st.text_area("Reason for Visit")
                    submit = st.form_submit_button("Schedule Appointment")
                    
                    if submit:
                        self.db.add_appointment(
                            patient_id,
                            appointment_date,
                            appointment_time,
                            reason,
                            assigned_to
                        )
                        st.success("✅ Appointment scheduled successfully!")
                else:
                    st.warning("No patients or staff available. Please add them first.")
                    submit = st.form_submit_button("Schedule Appointment", disabled=True)
        
        # View appointments
        st.subheader("View Appointments")
        
        # Date filter
        col1, col2 = st.columns(2)
        with col1:
            view_date = st.date_input("Select Date", key="view_appointment_date")
        
        # Staff filter
        with col2:
            staff = self.db.get_users()
            if not staff.empty:
                medical_staff = staff[(staff['role_name'] == 'doctor') | (staff['role_name'] == 'nurse')]
                
                # Add 'All Staff' option
                all_staff_option = pd.DataFrame([{'id': -1, 'full_name': 'All Staff', 'role_name': ''}])
                filter_staff = pd.concat([all_staff_option, medical_staff], ignore_index=True)
                
                staff_filter = st.selectbox(
                    "Filter by Staff",
                    options=filter_staff['id'].tolist(),
                    format_func=lambda x: filter_staff[filter_staff['id'] == x]['full_name'].iloc[0] if x != -1 else "All Staff"
                )
        
        # Get appointments based on filters
        if staff_filter == -1:  # All staff
            appointments = self.db.get_appointments(view_date.strftime('%Y-%m-%d'))
        else:
            appointments = self.db.get_appointments(view_date.strftime('%Y-%m-%d'), staff_filter)
            if not appointments.empty:
            # Format the appointment_date column for better display
                appointments['appointment_date'] = pd.to_datetime(appointments['appointment_date'])
            appointments['time'] = appointments['appointment_date'].dt.strftime('%I:%M %p')
            appointments['date'] = appointments['appointment_date'].dt.strftime('%Y-%m-%d')
            
            # Display appointments with edit and delete buttons
            for index, row in appointments.iterrows():
                with st.container():
                    col1, col2, col3 = st.columns([4, 1, 1])
                    with col1:
                        st.write(f"**{row['time']}** - {row['patient_name']}")
                        st.write(f"**Reason:** {row['reason']}")
                        st.write(f"**Assigned to:** {row['assigned_to']}")
                        st.write(f"**Status:** {row['status']}")
                    with col2:
                        if st.button("Edit", key=f"edit_appt_{row['id']}"):
                            st.session_state.appointment_to_edit = row['id']
                    with col3:
                        if st.button("Delete", key=f"delete_appt_{row['id']}"):
                            self.db.delete_appointment(row['id'])
                            st.success(f"Appointment deleted successfully!")
                            st.rerun()
            
            # Edit appointment form if an appointment is selected
            if hasattr(st.session_state, 'appointment_to_edit'):
                appt_id = st.session_state.appointment_to_edit
                appt_data = appointments[appointments['id'] == appt_id].iloc[0]
                
                st.subheader(f"Edit Appointment")
                with st.form("edit_appointment_form"):
                    patients = self.db.get_patients()
                    staff = self.db.get_users()
                    medical_staff = staff[(staff['role_name'] == 'doctor') | (staff['role_name'] == 'nurse')]
                    
                    edit_patient_id = st.selectbox(
                        "Select Patient",
                        options=patients['id'].tolist(),
                        format_func=lambda x: patients[patients['id'] == x]['name'].iloc[0],
                        index=patients['id'].tolist().index(appt_data['patient_id']) if appt_data['patient_id'] in patients['id'].tolist() else 0
                    )
                    
                    edit_assigned_to = st.selectbox(
                        "Assign to Staff Member",
                        options=medical_staff['id'].tolist(),
                        format_func=lambda x: f"{medical_staff[medical_staff['id'] == x]['full_name'].iloc[0]} ({medical_staff[medical_staff['id'] == x]['role_name'].iloc[0]})",
                        index=medical_staff['id'].tolist().index(appt_data['assigned_to_id']) if 'assigned_to_id' in appt_data and appt_data['assigned_to_id'] in medical_staff['id'].tolist() else 0
                    )
                    
                    edit_date_col, edit_time_col, edit_status_col = st.columns(3)
                    with edit_date_col:
                        edit_appointment_date = st.date_input("Date", value=pd.to_datetime(appt_data['date']).date())
                    with edit_time_col:
                        edit_appointment_time = st.time_input("Time", value=pd.to_datetime(appt_data['time']).time())
                    with edit_status_col:
                        edit_status = st.selectbox(
                            "Status",
                            options=["Scheduled", "Completed", "Cancelled", "No-show"],
                            index=["Scheduled", "Completed", "Cancelled", "No-show"].index(appt_data['status']) if appt_data['status'] in ["Scheduled", "Completed", "Cancelled", "No-show"] else 0
                        )
                    
                    edit_reason = st.text_area("Reason for Visit", value=appt_data['reason'])
                    
                    save_changes = st.form_submit_button("Save Changes")
                    cancel = st.form_submit_button("Cancel")
                    
                    if save_changes:
                        self.db.update_appointment(
                            appt_id,
                            edit_patient_id,
                            edit_appointment_date,
                            edit_appointment_time,
                            edit_reason,
                            edit_status,
                            edit_assigned_to
                        )
                        st.success("✅ Appointment updated successfully!")
                        del st.session_state.appointment_to_edit
                        st.rerun()
                    
                    if cancel:
                        del st.session_state.appointment_to_edit
                        st.rerun()
            
            # Generate appointment report
            st.download_button(
                label="📄 Generate Appointments Report",
                data=appointments.to_csv().encode('utf-8'),
                file_name=f'appointments_report_{view_date}.csv',
                mime='text/csv',
            )
        
            st.info(f"No appointments found for {view_date}.")
            
        # Weekly calendar view
        st.subheader("Weekly Calendar")
        
        # Calculate start and end of week
        today = date.today()
        start_of_week = today - timedelta(days=today.weekday())
        end_of_week = start_of_week + timedelta(days=6)
        
        # Get appointments for the week
        weekly_appointments = self.db.get_appointments_range(
            start_of_week.strftime('%Y-%m-%d'),
            end_of_week.strftime('%Y-%m-%d')
        )
        
        if not weekly_appointments.empty:
            # Group appointments by date
            weekly_appointments['appointment_date'] = pd.to_datetime(weekly_appointments['appointment_date'])
            weekly_appointments['date_str'] = weekly_appointments['appointment_date'].dt.strftime('%Y-%m-%d')
            weekly_appointments['time'] = weekly_appointments['appointment_date'].dt.strftime('%I:%M %p')
            
            date_groups = weekly_appointments.groupby('date_str')
            
            # Create a 7-column layout for the week
            weekdays = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
            cols = st.columns(7)
            
            for i, day in enumerate(weekdays):
                current_date = start_of_week + timedelta(days=i)
                date_str = current_date.strftime('%Y-%m-%d')
                
                with cols[i]:
                    st.write(f"**{day}**")
                    st.write(f"{current_date.strftime('%m/%d')}")
                    
                    if date_str in date_groups.groups:
                        day_appointments = date_groups.get_group(date_str)
                        for _, appt in day_appointments.iterrows():
                            st.write(f"**{appt['time']}**")
                            st.write(f"{appt['patient_name']}")
                            st.write(f"*{appt['assigned_to']}*")
        else:
            st.info("No appointments scheduled for this week.")

    def financial_records_page(self):
        """
         Financial Records Page 
        """
        st.title("Financial Records")
        
        # Record income form with columns
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
        st.subheader("Financial Records Search")
        
        # Search form for financial records
        with st.form("financial_search_form"):
            col1, col2 = st.columns(2)
            with col1:
                start_date = st.date_input("Start Date", value=date.today() - timedelta(days=30))
            with col2:
                end_date = st.date_input("End Date", value=date.today())
            
            # Additional search options
            search_col1, search_col2 = st.columns(2)
            with search_col1:
                patient_filter = st.selectbox(
                    "Filter by Patient",
                    options=["All Patients"] + patients['name'].tolist() if not patients.empty else ["All Patients"]
                )
            
            with search_col2:
                staff = self.db.get_users()
                if not staff.empty:
                    staff_filter = st.selectbox(
                        "Filter by Staff",
                        options=["All Staff"] + staff['full_name'].tolist()
                    )
                else:
                    staff_filter = "All Staff"
            
            search_button = st.form_submit_button("Search Records")
        
        if search_button and start_date <= end_date:
            # Get financial records filtered by date
            records = self.db.get_financial_records(
                start_date.strftime('%Y-%m-%d'),
                end_date.strftime('%Y-%m-%d')
            )
            
            # Apply additional filters if selected
            if not records.empty:
                if patient_filter != "All Patients":
                    records = records[records['patient_name'] == patient_filter]
                
                if staff_filter != "All Staff":
                    records = records[records['recorded_by'] == staff_filter]
                
                # Display total income
                total_income = records['amount'].sum()
                st.metric("Total Income", f"${total_income:.2f}")
                
                # Display financial records with edit and delete buttons
                for index, row in records.iterrows():
                    with st.container():
                        col1, col2, col3 = st.columns([4, 1, 1])
                        with col1:
                            st.write(f"**${row['amount']:.2f}** - {row['date']} - {row['patient_name']}")
                            st.write(f"**Description:** {row['description']}")
                            if 'recorded_by' in row and row['recorded_by']:
                                st.write(f"*Recorded by: {row['recorded_by']}*")
                        with col2:
                            if st.button("Edit", key=f"edit_finance_{row['id']}"):
                                st.session_state.finance_to_edit = row['id']
                        with col3:
                            if st.button("Delete", key=f"delete_finance_{row['id']}"):
                                self.db.delete_financial_record(row['id'])
                                st.success("Financial record deleted successfully!")
                                st.rerun()
                
                # Edit financial record form if a record is selected
                if hasattr(st.session_state, 'finance_to_edit'):
                    finance_id = st.session_state.finance_to_edit
                    finance_data = records[records['id'] == finance_id].iloc[0]
                    
                    st.subheader(f"Edit Financial Record")
                    with st.form("edit_finance_form"):
                        cols = st.columns([1, 1, 1])
                        with cols[0]:
                            edit_amount = st.number_input("Amount ($)", min_value=0.0, format="%.2f", value=finance_data['amount'])
                            edit_date = st.date_input("Date", value=pd.to_datetime(finance_data['date']).date())
                        
                        with cols[1]:
                            patients = self.db.get_patients()
                            edit_patient_id = st.selectbox(
                                "Select Patient",
                                options=patients['id'].tolist(),
                                format_func=lambda x: patients[patients['id'] == x]['name'].iloc[0],
                                index=patients['id'].tolist().index(finance_data['patient_id']) if finance_data['patient_id'] in patients['id'].tolist() else 0
                            )
                        
                        with cols[2]:
                            edit_description = st.text_input("Payment Description", value=finance_data['description'])
                            
                            # Staff who recorded the payment
                            staff = self.db.get_users()
                            if not staff.empty and 'recorded_by_id' in finance_data:
                                edit_recorded_by_id = st.selectbox(
                                    "Recorded By",
                                    options=staff['id'].tolist(),
                                    format_func=lambda x: staff[staff['id'] == x]['full_name'].iloc[0],
                                    index=staff['id'].tolist().index(finance_data['recorded_by_id']) if finance_data['recorded_by_id'] in staff['id'].tolist() else 0
                                )
                            else:
                                edit_recorded_by_id = None
                        
                        save_changes = st.form_submit_button("Save Changes")
                        cancel = st.form_submit_button("Cancel")
                        
                        if save_changes:
                            self.db.update_financial_record(
                                finance_id,
                                edit_date,
                                edit_amount,
                                edit_description,
                                edit_patient_id,
                                edit_recorded_by_id
                            )
                            st.success("✅ Financial record updated successfully!")
                            del st.session_state.finance_to_edit
                            st.rerun()
                        
                        if cancel:
                            del st.session_state.finance_to_edit
                            st.rerun()
                
                # Generate financial report
                st.download_button(
                    label="📄 Generate Financial Report",
                    data=records.to_csv().encode('utf-8'),
                    file_name=f'financial_report_{start_date}_to_{end_date}.csv',
                    mime='text/csv',
                )
            else:
                st.info(f"No financial records found between {start_date} and {end_date}.")
        elif search_button:
            st.error("Start date must be before end date.")
        
        # Financial analysis section
        st.subheader("Financial Analysis")
        
        # Date range for analysis
        col1, col2 = st.columns(2)
        with col1:
            analysis_start_date = st.date_input("Analysis Start Date", value=date.today().replace(day=1))
        with col2:
            analysis_end_date = st.date_input("Analysis End Date", value=date.today())
        
        if analysis_start_date <= analysis_end_date:
            # Get data for analysis
            analysis_data = self.db.get_financial_records(
                analysis_start_date.strftime('%Y-%m-%d'),
                analysis_end_date.strftime('%Y-%m-%d')
            )
            
            if not analysis_data.empty:
                # Convert date strings to datetime objects
                analysis_data['date'] = pd.to_datetime(analysis_data['date'])
                
                # Display key metrics
                total_income = analysis_data['amount'].sum()
                avg_daily_income = total_income / max((analysis_end_date - analysis_start_date).days, 1)
                
                metric_col1, metric_col2, metric_col3 = st.columns(3)
                with metric_col1:
                    st.metric("Total Income", f"${total_income:.2f}")
                with metric_col2:
                    st.metric("Avg. Daily Income", f"${avg_daily_income:.2f}")
                with metric_col3:
                    st.metric("Transaction Count", f"{len(analysis_data)}")
                
                # Charts row
                chart_col1, chart_col2 = st.columns(2)
                
                with chart_col1:
                    # Group by date and sum amounts
                    daily_income = analysis_data.groupby(analysis_data['date'].dt.date)['amount'].sum().reset_index()
                    
                    # Create a bar chart of daily income
                    fig1 = px.bar(
                        daily_income, 
                        x='date', 
                        y='amount',
                        labels={'date': 'Date', 'amount': 'Income ($)'},
                        title='Daily Income'
                    )
                    
                    st.plotly_chart(fig1, use_container_width=True)
                
                with chart_col2:
                    # Patient distribution pie chart
                    patient_distribution = analysis_data.groupby('patient_name')['amount'].sum().reset_index()
                    patient_distribution = patient_distribution.sort_values('amount', ascending=False).head(10)
                    
                    fig2 = px.pie(
                        patient_distribution, 
                        values='amount', 
                        names='patient_name',
                        title='Income by Patient'
                    )
                    
                    st.plotly_chart(fig2, use_container_width=True)
                
                # Staff performance if recorded_by data is available
                if 'recorded_by' in analysis_data.columns and analysis_data['recorded_by'].notna().any():
                    staff_performance = analysis_data.groupby('recorded_by')['amount'].sum().reset_index()
                    staff_performance = staff_performance.sort_values('amount', ascending=False)
                    
                    fig3 = px.bar(
                        staff_performance,
                        x='recorded_by',
                        y='amount',
                        title='Revenue by Staff Member'
                    )
                    
                    st.plotly_chart(fig3, use_container_width=True)
            else:
                st.info(f"No financial data available between {analysis_start_date} and {analysis_end_date}.")
        else:
            st.error("Analysis start date must be before end date.")

    # Additional methods for database operations

    def get_db(self):
        """
        Return the database manager
        """
        return self.db

if __name__ == "__main__":
    app = MedicalPracticeApp()
    app.run()