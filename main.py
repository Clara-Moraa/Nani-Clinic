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
                ["🏥 Patient Management", "📅 Appointments", "💰 Financial Records", "📊 Dashboard"]
            )

        #  page matching
        page = page.split(" ")[1] + " " + page.split(" ")[2] if len(page.split(" ")) > 2 else page.split(" ")[1]

        if page == "Patient Management":
            self.patient_management_page()
        elif page == "Appointments":
            self.appointments_page()
        elif page == "Financial Records":
            self.financial_records_page()
        elif page == "Dashboard":
            self.dashboard_page()

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
                    st.success("✅ Patient added successfully!")

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
                
                if not patients.empty:
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
                        st.success("✅ Appointment scheduled successfully!")
                else:
                    st.warning("No patients available. Please add patients first.")
                    submit = st.form_submit_button("Schedule Appointment", disabled=True)
        
        # View appointments
        st.subheader("View Appointments")
        appointment_date = st.date_input("Select Date", key="view_appointment_date")
        
        appointments = self.db.get_appointments(appointment_date.strftime('%Y-%m-%d'))
        if not appointments.empty:
            # Format the appointment_date column for better display
            appointments['appointment_date'] = pd.to_datetime(appointments['appointment_date'])
            appointments['time'] = appointments['appointment_date'].dt.strftime('%I:%M %p')
            appointments['date'] = appointments['appointment_date'].dt.strftime('%Y-%m-%d')
            
            # Display appointments for the selected date
            st.dataframe(
                appointments[['patient_name', 'time', 'reason', 'status']],
                use_container_width=True,
                hide_index=True
            )
            
            # Generate appointment report
            st.download_button(
                label="📄 Generate Appointments Report",
                data=appointments.to_csv().encode('utf-8'),
                file_name=f'appointments_report_{appointment_date}.csv',
                mime='text/csv',
            )
        else:
            st.info(f"No appointments scheduled for {appointment_date}.")

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
                
                submit = st.form_submit_button("Record Payment")
                
                if submit and amount > 0:
                    self.db.record_income(
                        date.today(),
                        amount,
                        description,
                        patient_id
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
        col1, col2, col3 = st.columns(3)
        
        # Get patient count
        patients = self.db.get_patients()
        patient_count = len(patients) if not patients.empty else 0
        
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
            st.metric("Today's Appointments", appointment_count)
        
        with col3:
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
        else:
            st.info("No financial data available for the last 30 days.")

if __name__ == "__main__":
    app = MedicalPracticeApp()
    app.run()