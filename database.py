import sqlite3
import pandas as pd
from datetime import datetime

class DatabaseManager:
    def __init__(self):
        """Initialize database connection and create tables if they don't exist"""
        self.conn = sqlite3.connect('clinic.db', check_same_thread=False)
        self.create_tables()

    def create_tables(self):
        """Create all necessary database tables if they don't exist"""
        cursor = self.conn.cursor()
        
        # Patients table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS patients (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                contact TEXT NOT NULL,
                email TEXT,
                medical_history TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Appointments table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS appointments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                patient_id INTEGER,
                appointment_date DATETIME NOT NULL,
                reason TEXT,
                status TEXT DEFAULT 'scheduled',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (patient_id) REFERENCES patients (id)
            )
        ''')
        
        # Financial records table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS finances (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date DATE NOT NULL,
                amount REAL NOT NULL,
                description TEXT,
                patient_id INTEGER,
                transaction_type TEXT DEFAULT 'payment',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (patient_id) REFERENCES patients (id)
            )
        ''')
        
        self.conn.commit()

    def add_patient(self, name, contact, email, medical_history):
        """Add a new patient to the database"""
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO patients (name, contact, email, medical_history)
            VALUES (?, ?, ?, ?)
        ''', (name, contact, email, medical_history))
        self.conn.commit()
        return cursor.lastrowid

    def get_patients(self):
        """Retrieve all patients from the database"""
        try:
            return pd.read_sql_query(
                "SELECT * FROM patients ORDER BY name",
                self.conn
            )
        except Exception as e:
            print(f"Error fetching patients: {e}")
            return pd.DataFrame(columns=['id', 'name', 'contact', 'email', 'medical_history'])

    def search_patients(self, search_term):
        """Search for patients by name or contact information"""
        query = """
            SELECT * FROM patients 
            WHERE name LIKE ? OR contact LIKE ? OR email LIKE ?
            ORDER BY name
        """
        pattern = f"%{search_term}%"
        return pd.read_sql_query(query, self.conn, params=(pattern, pattern, pattern))

    def add_appointment(self, patient_id, date, time, reason):
        """Add a new appointment to the database"""
        cursor = self.conn.cursor()
        appointment_datetime = f"{date} {time}"
        cursor.execute('''
            INSERT INTO appointments (patient_id, appointment_date, reason)
            VALUES (?, ?, ?)
        ''', (patient_id, appointment_datetime, reason))
        self.conn.commit()
        return cursor.lastrowid

    def get_appointments(self, date=None):
        """Retrieve appointments, optionally filtered by date"""
        query = """
            SELECT 
                appointments.id,
                patients.name as patient_name,
                appointments.appointment_date,
                appointments.reason,
                appointments.status
            FROM appointments
            JOIN patients ON appointments.patient_id = patients.id
        """
        if date:
            query += " WHERE DATE(appointment_date) = ?"
            return pd.read_sql_query(query, self.conn, params=(date,))
        return pd.read_sql_query(query, self.conn)

    def record_income(self, date, amount, description, patient_id):
        """Record a financial transaction"""
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO finances (date, amount, description, patient_id)
            VALUES (?, ?, ?, ?)
        ''', (date.strftime('%Y-%m-%d'), amount, description, patient_id))
        self.conn.commit()
        return cursor.lastrowid

    def get_financial_records(self, start_date=None, end_date=None):
        """Retrieve financial records within a date range"""
        query = """
            SELECT 
                finances.id,
                finances.date,
                finances.amount,
                finances.description,
                patients.name as patient_name
            FROM finances
            JOIN patients ON finances.patient_id = patients.id
        """
        if start_date and end_date:
            query += " WHERE date BETWEEN ? AND ?"
            return pd.read_sql_query(query, self.conn, params=(start_date, end_date))
        return pd.read_sql_query(query, self.conn)

    def __del__(self):
        """Close the database connection when the object is destroyed"""
        try:
            self.conn.close()
        except:
            pass