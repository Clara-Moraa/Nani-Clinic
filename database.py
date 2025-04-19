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
        
        # Roles table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS roles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                role_name TEXT NOT NULL UNIQUE,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Insert default roles if they don't exist
        default_roles = [
            ('doctor', 'Medical doctor with full patient access'),
            ('nurse', 'Nursing staff with limited patient data access'),
            ('admin', 'Administrative staff with financial access'),
            ('receptionist', 'Front desk staff')
        ]
        
        for role in default_roles:
            cursor.execute('''
                INSERT OR IGNORE INTO roles (role_name, description)
                VALUES (?, ?)
            ''', role)
        
        # Users table (medical staff)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password TEXT NOT NULL,
                full_name TEXT NOT NULL,
                role_id INTEGER,
                email TEXT,
                phone TEXT,
                specialty TEXT,
                active INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (role_id) REFERENCES roles (id)
            )
        ''')
        
        # Patients table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS patients (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                contact TEXT NOT NULL,
                email TEXT,
                medical_history TEXT,
                assigned_doctor_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (assigned_doctor_id) REFERENCES users (id)
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
                recorded_by_id INTEGER,
                transaction_type TEXT DEFAULT 'payment',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (patient_id) REFERENCES patients (id),
                FOREIGN KEY (recorded_by_id) REFERENCES users (id)
            )
        ''')
        
        # Medical records table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS medical_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                patient_id INTEGER,
                doctor_id INTEGER,
                visit_date DATE NOT NULL,
                diagnosis TEXT,
                treatment TEXT,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (patient_id) REFERENCES patients (id),
                FOREIGN KEY (doctor_id) REFERENCES users (id)
            )
        ''')
        # Appointments table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS appointments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                patient_id INTEGER,
                appointment_date DATETIME NOT NULL,
                reason TEXT,
                status TEXT DEFAULT 'Scheduled',
                assigned_to INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (patient_id) REFERENCES patients (id),
                FOREIGN KEY (assigned_to) REFERENCES users (id)
            )
        ''')
        
        self.conn.commit()

    # User and role management methods
    def add_user(self, username, password, full_name, role_id, email=None, phone=None, specialty=None):
        """Add a new user (medical staff) to the database"""
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO users (username, password, full_name, role_id, email, phone, specialty)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (username, password, full_name, role_id, email, phone, specialty))
        self.conn.commit()
        return cursor.lastrowid
    
    def get_users(self):
        """Retrieve all users from the database"""
        try:
            return pd.read_sql_query(
                '''
                SELECT users.*, roles.role_name 
                FROM users 
                JOIN roles ON users.role_id = roles.id
                WHERE users.active = 1
                ORDER BY users.full_name
                ''',
                self.conn
            )
        except Exception as e:
            print(f"Error fetching users: {e}")
            return pd.DataFrame(columns=['id', 'username', 'full_name', 'role_name', 'email', 'phone', 'specialty'])
    
    def get_roles(self):
        """Retrieve all roles from the database"""
        try:
            return pd.read_sql_query("SELECT * FROM roles", self.conn)
        except Exception as e:
            print(f"Error fetching roles: {e}")
            return pd.DataFrame(columns=['id', 'role_name', 'description'])
    
    def search_users(self, search_term):
        """Search for users by name, username, or role"""
        query = """
            SELECT users.*, roles.role_name 
            FROM users 
            JOIN roles ON users.role_id = roles.id
            WHERE users.full_name LIKE ? OR users.username LIKE ? OR 
                  users.email LIKE ? OR roles.role_name LIKE ?
            ORDER BY users.full_name
        """
        pattern = f"%{search_term}%"
        return pd.read_sql_query(query, self.conn, params=(pattern, pattern, pattern, pattern))

    # Patient management methods
    def add_patient(self, name, contact, email, medical_history, assigned_doctor_id=None):
        """Add a new patient to the database"""
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO patients (name, contact, email, medical_history, assigned_doctor_id)
            VALUES (?, ?, ?, ?, ?)
        ''', (name, contact, email, medical_history, assigned_doctor_id))
        self.conn.commit()
        return cursor.lastrowid

    def get_patients(self):
        """Retrieve all patients from the database"""
        try:
            return pd.read_sql_query(
                '''
                SELECT patients.*, users.full_name as doctor_name
                FROM patients
                LEFT JOIN users ON patients.assigned_doctor_id = users.id
                ORDER BY patients.name
                ''',
                self.conn
            )
        except Exception as e:
            print(f"Error fetching patients: {e}")
            return pd.DataFrame(columns=['id', 'name', 'contact', 'email', 'medical_history', 'doctor_name'])

    def search_patients(self, search_term):
        """Search for patients by name or contact information"""
        query = """
            SELECT patients.*, users.full_name as doctor_name
            FROM patients
            LEFT JOIN users ON patients.assigned_doctor_id = users.id
            WHERE patients.name LIKE ? OR patients.contact LIKE ? OR patients.email LIKE ?
            ORDER BY patients.name
        """
        pattern = f"%{search_term}%"
        return pd.read_sql_query(query, self.conn, params=(pattern, pattern, pattern))

    # Medical records methods
    def add_medical_record(self, patient_id, doctor_id, visit_date, diagnosis, treatment, notes):
        """Add a new medical record"""
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO medical_records (patient_id, doctor_id, visit_date, diagnosis, treatment, notes)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (patient_id, doctor_id, visit_date, diagnosis, treatment, notes))
        self.conn.commit()
        return cursor.lastrowid
    
    def get_medical_records(self, patient_id=None):
        """Retrieve medical records, optionally filtered by patient"""
        query = """
            SELECT 
                medical_records.id,
                patients.name as patient_name,
                users.full_name as doctor_name,
                medical_records.visit_date,
                medical_records.diagnosis,
                medical_records.treatment,
                medical_records.notes
            FROM medical_records
            JOIN patients ON medical_records.patient_id = patients.id
            JOIN users ON medical_records.doctor_id = users.id
        """
        if patient_id:
            query += " WHERE patient_id = ?"
            return pd.read_sql_query(query, self.conn, params=(patient_id,))
        return pd.read_sql_query(query, self.conn)
    
    # Appointment
    def get_appointments(self, date=None, staff_id=None):
        """Retrieve appointments, optionally filtered by date and staff"""
        query = """
            SELECT 
                appointments.id,
                appointments.appointment_date,
                appointments.reason,
                appointments.status,
                patients.name as patient_name,
                patients.id as patient_id,
                users.full_name as assigned_to,
                users.id as assigned_to_id
            FROM appointments
            JOIN patients ON appointments.patient_id = patients.id
            LEFT JOIN users ON appointments.assigned_to = users.id
        """
        
        if date and staff_id:
            query += " WHERE DATE(appointments.appointment_date) = ? AND appointments.assigned_to = ?"
            return pd.read_sql_query(query, self.conn, params=(date, staff_id))
        elif date:
            query += " WHERE DATE(appointments.appointment_date) = ?"
            return pd.read_sql_query(query, self.conn, params=(date,))
        elif staff_id:
            query += " WHERE appointments.assigned_to = ?"
            return pd.read_sql_query(query, self.conn, params=(staff_id,))
        
        return pd.read_sql_query(query, self.conn)

    # Financial methods
    def record_income(self, date, amount, description, patient_id, recorded_by_id=None):
        """Record a financial transaction"""
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO finances (date, amount, description, patient_id, recorded_by_id)
            VALUES (?, ?, ?, ?, ?)
        ''', (date.strftime('%Y-%m-%d'), amount, description, patient_id, recorded_by_id))
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
                patients.name as patient_name,
                users.full_name as recorded_by
            FROM finances
            JOIN patients ON finances.patient_id = patients.id
            LEFT JOIN users ON finances.recorded_by_id = users.id
        """
        if start_date and end_date:
            query += " WHERE finances.date BETWEEN ? AND ?"
            return pd.read_sql_query(query, self.conn, params=(start_date, end_date))
        return pd.read_sql_query(query, self.conn)

    def __del__(self):
        """Close the database connection when the object is destroyed"""
        try:
            self.conn.close()
        except:
            pass