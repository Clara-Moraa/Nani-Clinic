import streamlit as st
from database import DatabaseManager
import pandas as pd
from datetime import datetime, date

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
            st.image("https://via.placeholder.com/150", caption="Nani Health Clinic")
            st.title("Clinic Dashboard")
            page = st.radio(
                "",  # Empty label for cleaner look
                ["🏥 Patient Management", "📅 Appointments", "💰 Financial Records"]
            )

        #  page matching
        page = page.split(" ")[1] + " " + page.split(" ")[2] if len(page.split(" ")) > 2 else page.split(" ")[1]

        if page == "Patient Management":
            self.patient_management_page()
        elif page == "Appointments":
            self.appointments_page()
        elif page == "Financial Records":
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
                submit = st.form_submit_button("Add Patient")
                
                if submit and name and contact:
                    self.db.add_patient(name, contact, email, medical_history)
                    st.success(" Patient added successfully!")

        #  search interface
        st.subheader("🔍 Search Patients")
        search_col1, search_col2 = st.columns([3, 1])
        with search_col1:
            search_term = st.text_input("", placeholder="Search by name or contact...")
        
        if search_term:
            results = self.db.search_patients(search_term)
            st.dataframe(
                results,
                use_container_width=True,
                hide_index=True
            )

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
                
                patient_id = st.selectbox(
                    "Select Patient",
                    options=patients['id'].tolist(),
                    format_func=lambda x: patients[patients['id'] == x]['name'].iloc[0]
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
                        reason
                    )
                    st.success(" Appointment scheduled successfully!")

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
            with cols[1]:
                patient_id = st.selectbox(
                    "Select Patient",
                    options=self.db.get_patients()['id'].tolist(),
                    format_func=lambda x: self.db.get_patients()[
                        self.db.get_patients()['id'] == x
                    ]['name'].iloc[0]
                )
            with cols[2]:
                description = st.text_input("Payment Description")
            
            submit = st.form_submit_button("Record Payment")
            
            if submit and amount > 0:
                self.db.record_income(
                    date.today(),
                    amount,
                    description,
                    patient_id
                )
                st.success(" Payment recorded successfully!")

if __name__ == "__main__":
    app = MedicalPracticeApp()
    app.run()