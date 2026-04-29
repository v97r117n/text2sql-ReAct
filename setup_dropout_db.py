#!/usr/bin/env python
"""
Creates a SQLite database for school dropout prediction with realistic sample data.

Tables:
  - students       — Core student demographics
  - parents        — Parent/guardian info (income, criminal history, etc.)
  - academics      — Academic performance per year
  - socioeconomic  — Financial conditions and aid
  - school_info    — School details (distance, type, location)
  - risk_assessments — Predicted dropout risk scores

Usage:
    python examples/setup_dropout_db.py
"""
import os

from sqlalchemy import create_engine, text

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dropout_prediction.db")
engine = create_engine(f"sqlite:///{DB_PATH}")

with engine.connect() as conn:
    # Drop existing tables in dependency order
    for t in ["risk_assessments", "academics", "socioeconomic", "students", "parents", "school_info"]:
        conn.execute(text(f"DROP TABLE IF EXISTS {t}"))

    # ── Schema ─────────────────────────────────────────────────────────────

    conn.execute(text("""
        CREATE TABLE school_info (
            school_id       INTEGER PRIMARY KEY,
            school_name     TEXT NOT NULL,
            school_type     TEXT NOT NULL,   -- 'government', 'private', 'aided'
            location        TEXT NOT NULL,   -- 'urban', 'semi-urban', 'rural'
            district        TEXT NOT NULL,
            state           TEXT NOT NULL
        )
    """))

    conn.execute(text("""
        CREATE TABLE parents (
            parent_id               INTEGER PRIMARY KEY,
            father_name             TEXT,
            mother_name             TEXT,
            father_education        TEXT,   -- 'none', 'primary', 'secondary', 'graduate', 'postgraduate'
            mother_education        TEXT,
            father_occupation       TEXT,
            mother_occupation       TEXT,
            annual_income           REAL NOT NULL,         -- in INR
            has_criminal_history    INTEGER NOT NULL DEFAULT 0,  -- 0=No, 1=Yes
            marital_status          TEXT NOT NULL DEFAULT 'married'  -- 'married', 'divorced', 'single', 'widowed'
        )
    """))

    conn.execute(text("""
        CREATE TABLE students (
            student_id      INTEGER PRIMARY KEY,
            first_name      TEXT NOT NULL,
            last_name       TEXT NOT NULL,
            gender          TEXT NOT NULL,       -- 'M', 'F'
            date_of_birth   TEXT NOT NULL,
            age             INTEGER NOT NULL,
            grade           INTEGER NOT NULL,    -- current grade (1-12)
            enrollment_year INTEGER NOT NULL,
            school_id       INTEGER NOT NULL,
            parent_id       INTEGER NOT NULL,
            distance_from_school_km  REAL NOT NULL,
            current_status  TEXT NOT NULL DEFAULT 'enrolled',  -- 'enrolled', 'dropped_out', 'graduated', 'transferred'
            FOREIGN KEY (school_id) REFERENCES school_info(school_id),
            FOREIGN KEY (parent_id) REFERENCES parents(parent_id)
        )
    """))

    conn.execute(text("""
        CREATE TABLE academics (
            record_id       INTEGER PRIMARY KEY,
            student_id      INTEGER NOT NULL,
            academic_year   TEXT NOT NULL,       -- e.g. '2024-2025'
            gpa             REAL NOT NULL,       -- 0.0 to 10.0
            attendance_pct  REAL NOT NULL,       -- 0 to 100
            failed_subjects INTEGER NOT NULL DEFAULT 0,
            math_score      REAL,
            science_score   REAL,
            language_score  REAL,
            behavior_grade  TEXT,                -- 'A', 'B', 'C', 'D', 'F'
            FOREIGN KEY (student_id) REFERENCES students(student_id)
        )
    """))

    conn.execute(text("""
        CREATE TABLE socioeconomic (
            record_id               INTEGER PRIMARY KEY,
            student_id              INTEGER NOT NULL,
            family_income_bracket   TEXT NOT NULL,   -- 'below_poverty', 'low', 'middle', 'upper_middle', 'high'
            receives_scholarship    INTEGER NOT NULL DEFAULT 0,
            receives_free_meals     INTEGER NOT NULL DEFAULT 0,
            has_internet_access     INTEGER NOT NULL DEFAULT 0,
            has_private_transport   INTEGER NOT NULL DEFAULT 0,
            number_of_siblings     INTEGER NOT NULL DEFAULT 0,
            lives_with              TEXT NOT NULL DEFAULT 'both_parents',  -- 'both_parents', 'single_parent', 'guardian', 'hostel'
            FOREIGN KEY (student_id) REFERENCES students(student_id)
        )
    """))

    conn.execute(text("""
        CREATE TABLE risk_assessments (
            assessment_id       INTEGER PRIMARY KEY,
            student_id          INTEGER NOT NULL,
            assessment_date     TEXT NOT NULL,
            risk_score          REAL NOT NULL,       -- 0.0 to 1.0
            risk_level          TEXT NOT NULL,        -- 'low', 'medium', 'high', 'critical'
            predicted_dropout_year  INTEGER,
            contributing_factors    TEXT,             -- comma-separated factors
            recommended_intervention TEXT,
            FOREIGN KEY (student_id) REFERENCES students(student_id)
        )
    """))

    # ── Sample Data ────────────────────────────────────────────────────────

    # Schools (6)
    conn.execute(text("""
        INSERT INTO school_info VALUES
        (1, 'Delhi Public School',         'private',     'urban',      'Central Delhi',  'Delhi'),
        (2, 'Govt. Senior Secondary School','government',  'semi-urban', 'Faridabad',      'Haryana'),
        (3, 'St. Mary Convent',            'aided',       'urban',      'Pune',           'Maharashtra'),
        (4, 'Zilla Parishad School',       'government',  'rural',      'Osmanabad',      'Maharashtra'),
        (5, 'Kendriya Vidyalaya',          'government',  'urban',      'Hyderabad',      'Telangana'),
        (6, 'Rural Govt. High School',     'government',  'rural',      'Anantapur',      'Andhra Pradesh')
    """))

    # Parents (30)
    conn.execute(text("""
        INSERT INTO parents VALUES
        (1,  'Rajesh Kumar',    'Sunita Kumar',    'graduate',      'secondary',    'engineer',        'homemaker',     850000,  0, 'married'),
        (2,  'Mahesh Patil',    'Asha Patil',      'secondary',     'primary',      'farmer',          'homemaker',     180000,  0, 'married'),
        (3,  'Suresh Reddy',    'Lakshmi Reddy',   'postgraduate',  'graduate',     'doctor',          'teacher',       1500000, 0, 'married'),
        (4,  'Ramu Naik',       'Savitri Naik',    'none',          'none',         'daily_laborer',   'daily_laborer', 72000,   1, 'married'),
        (5,  'Amit Sharma',     'Priya Sharma',    'graduate',      'graduate',     'software_eng',    'nurse',         1200000, 0, 'married'),
        (6,  'Venkatesh Rao',   'Padma Rao',       'primary',       'none',         'auto_driver',     'homemaker',     144000,  0, 'married'),
        (7,  'Ganesh Jadhav',   'Mangala Jadhav',  'secondary',     'primary',      'shopkeeper',      'homemaker',     300000,  0, 'married'),
        (8,  'Abdul Khan',      'Fatima Khan',     'none',          'none',         'daily_laborer',   'homemaker',     84000,   1, 'married'),
        (9,  'Srinivas Murthy', 'Geetha Murthy',   'graduate',      'secondary',    'govt_employee',   'homemaker',     600000,  0, 'married'),
        (10, 'Prakash Gowda',   'Suma Gowda',      'primary',       'none',         'farmer',          'homemaker',     156000,  1, 'divorced'),
        (11, 'Ramesh Yadav',    'Kamla Yadav',     'none',          'none',         'construction',    'daily_laborer', 96000,   0, 'married'),
        (12, 'Vijay Singh',     'Anita Singh',     'secondary',     'secondary',    'security_guard',  'tailor',        240000,  0, 'married'),
        (13, 'Mohan Das',       'Sita Das',        'primary',       'none',         'fisherman',       'homemaker',     108000,  0, 'married'),
        (14, 'Arjun Nair',      'Deepa Nair',      'postgraduate',  'postgraduate', 'professor',       'lawyer',        2000000, 0, 'married'),
        (15, 'Kishore Babu',    'Rani Babu',       'none',          'none',         'unemployed',      'domestic_help', 60000,   1, 'single'),
        (16, 'Satish Verma',    'Rekha Verma',     'graduate',      'secondary',    'accountant',      'homemaker',     480000,  0, 'married'),
        (17, 'Dinesh Chauhan',  'Kavita Chauhan',  'secondary',     'primary',      'mechanic',        'homemaker',     216000,  0, 'married'),
        (18, 'Jagdish Thakur',  'Parvati Thakur',  'none',          'none',         'daily_laborer',   'daily_laborer', 66000,   1, 'widowed'),
        (19, 'Ashok Pillai',    'Meena Pillai',    'graduate',      'graduate',     'bank_manager',    'teacher',       900000,  0, 'married'),
        (20, 'Balram Sahu',     'Lata Sahu',       'primary',       'none',         'farmer',          'homemaker',     132000,  0, 'married'),
        (21, 'Naresh Gupta',    'Pooja Gupta',     'postgraduate',  'graduate',     'business_owner',  'homemaker',     1800000, 0, 'married'),
        (22, 'Santosh Mali',    'Usha Mali',       'none',          'none',         'daily_laborer',   'daily_laborer', 78000,   0, 'married'),
        (23, 'Manoj Tiwari',    'Sunita Tiwari',   'secondary',     'primary',      'electrician',     'homemaker',     264000,  0, 'married'),
        (24, 'Govind Paswan',   'Radha Paswan',    'none',          'none',         'rag_picker',      'homemaker',     48000,   1, 'married'),
        (25, 'Sunil Joshi',     'Nirmala Joshi',   'graduate',      'secondary',    'teacher',         'homemaker',     420000,  0, 'married'),
        (26, 'Deepak Meena',    'Sushma Meena',    'primary',       'none',         'farmer',          'homemaker',     120000,  0, 'divorced'),
        (27, 'Harish Bhat',     'Vidya Bhat',      'postgraduate',  'graduate',     'IT_manager',      'architect',     1600000, 0, 'married'),
        (28, 'Pappu Manjhi',    'Geeta Manjhi',    'none',          'none',         'boatman',         'homemaker',     54000,   1, 'married'),
        (29, 'Anil Deshmukh',   'Vaishali Deshmukh','graduate',     'graduate',     'police_officer',  'govt_clerk',    720000,  0, 'married'),
        (30, 'Ravi Kori',       'Basanti Kori',    'none',          'none',         'daily_laborer',   'daily_laborer', 72000,   0, 'single')
    """))

    # Students (30)
    conn.execute(text("""
        INSERT INTO students VALUES
        (1,  'Aarav',    'Kumar',    'M', '2010-03-15', 15, 10, 2016, 1, 1,  2.5,  'enrolled'),
        (2,  'Sneha',    'Patil',    'F', '2011-07-22', 14, 9,  2017, 4, 2,  12.0, 'enrolled'),
        (3,  'Rohan',    'Reddy',    'M', '2009-11-08', 16, 11, 2015, 5, 3,  1.0,  'enrolled'),
        (4,  'Priya',    'Naik',     'F', '2010-05-30', 15, 9,  2017, 4, 4,  18.5, 'dropped_out'),
        (5,  'Vikram',   'Sharma',   'M', '2010-01-12', 15, 10, 2016, 1, 5,  3.0,  'enrolled'),
        (6,  'Anjali',   'Rao',      'F', '2011-09-18', 14, 8,  2018, 6, 6,  22.0, 'enrolled'),
        (7,  'Aditya',   'Jadhav',   'M', '2010-12-05', 15, 10, 2016, 3, 7,  4.5,  'enrolled'),
        (8,  'Fatima',   'Khan',     'F', '2011-02-14', 14, 8,  2018, 2, 8,  15.0, 'dropped_out'),
        (9,  'Karthik',  'Murthy',   'M', '2009-08-25', 16, 11, 2015, 5, 9,  2.0,  'enrolled'),
        (10, 'Lakshmi',  'Gowda',    'F', '2010-04-10', 15, 9,  2017, 4, 10, 25.0, 'dropped_out'),
        (11, 'Rahul',    'Yadav',    'M', '2011-06-20', 14, 8,  2018, 6, 11, 20.0, 'enrolled'),
        (12, 'Meera',    'Singh',    'F', '2010-10-03', 15, 10, 2016, 2, 12, 8.5,  'enrolled'),
        (13, 'Arjun',    'Das',      'M', '2011-01-28', 14, 9,  2017, 4, 13, 16.0, 'enrolled'),
        (14, 'Diya',     'Nair',     'F', '2009-12-15', 16, 12, 2014, 1, 14, 1.5,  'graduated'),
        (15, 'Suraj',    'Babu',     'M', '2010-08-07', 15, 8,  2018, 6, 15, 28.0, 'dropped_out'),
        (16, 'Nandini',  'Verma',    'F', '2010-02-23', 15, 10, 2016, 5, 16, 5.0,  'enrolled'),
        (17, 'Sagar',    'Chauhan',  'M', '2011-05-17', 14, 9,  2017, 2, 17, 7.0,  'enrolled'),
        (18, 'Kavya',    'Thakur',   'F', '2010-11-30', 15, 8,  2018, 4, 18, 30.0, 'dropped_out'),
        (19, 'Nikhil',   'Pillai',   'M', '2009-09-12', 16, 12, 2014, 5, 19, 3.5,  'enrolled'),
        (20, 'Pallavi',  'Sahu',     'F', '2011-03-25', 14, 9,  2017, 4, 20, 14.0, 'enrolled'),
        (21, 'Ishaan',   'Gupta',    'M', '2010-07-08', 15, 10, 2016, 1, 21, 2.0,  'enrolled'),
        (22, 'Ananya',   'Mali',     'F', '2011-08-14', 14, 8,  2018, 6, 22, 19.0, 'enrolled'),
        (23, 'Dev',      'Tiwari',   'M', '2010-06-01', 15, 10, 2016, 3, 23, 6.0,  'enrolled'),
        (24, 'Radha',    'Paswan',   'F', '2010-04-22', 15, 7,  2019, 4, 24, 32.0, 'dropped_out'),
        (25, 'Manish',   'Joshi',    'M', '2011-10-09', 14, 9,  2017, 5, 25, 4.0,  'enrolled'),
        (26, 'Swati',    'Meena',    'F', '2010-01-30', 15, 9,  2017, 4, 26, 17.0, 'enrolled'),
        (27, 'Tanmay',   'Bhat',     'M', '2009-06-18', 16, 12, 2014, 1, 27, 1.0,  'enrolled'),
        (28, 'Pooja',    'Manjhi',   'F', '2011-12-05', 14, 7,  2019, 6, 28, 35.0, 'dropped_out'),
        (29, 'Omkar',    'Deshmukh', 'M', '2010-03-20', 15, 10, 2016, 3, 29, 5.5,  'enrolled'),
        (30, 'Deepika',  'Kori',     'F', '2011-07-14', 14, 8,  2018, 4, 30, 21.0, 'enrolled')
    """))

    # Academics (30 records — one per student for current year)
    conn.execute(text("""
        INSERT INTO academics VALUES
        (1,  1,  '2025-2026', 8.5,  95.0, 0, 88, 92, 85, 'A'),
        (2,  2,  '2025-2026', 4.2,  62.0, 3, 35, 40, 55, 'C'),
        (3,  3,  '2025-2026', 9.0,  97.0, 0, 95, 93, 88, 'A'),
        (4,  4,  '2024-2025', 3.1,  45.0, 4, 25, 30, 38, 'D'),
        (5,  5,  '2025-2026', 8.8,  93.0, 0, 90, 88, 92, 'A'),
        (6,  6,  '2025-2026', 5.0,  58.0, 2, 42, 48, 60, 'C'),
        (7,  7,  '2025-2026', 7.2,  85.0, 1, 72, 68, 78, 'B'),
        (8,  8,  '2024-2025', 2.8,  38.0, 5, 20, 22, 35, 'F'),
        (9,  9,  '2025-2026', 8.0,  91.0, 0, 82, 85, 80, 'A'),
        (10, 10, '2024-2025', 3.5,  42.0, 4, 28, 32, 40, 'D'),
        (11, 11, '2025-2026', 4.8,  55.0, 3, 38, 42, 52, 'C'),
        (12, 12, '2025-2026', 7.5,  88.0, 0, 78, 72, 80, 'B'),
        (13, 13, '2025-2026', 5.5,  65.0, 2, 50, 55, 62, 'C'),
        (14, 14, '2024-2025', 9.5,  98.0, 0, 96, 95, 94, 'A'),
        (15, 15, '2024-2025', 2.2,  30.0, 5, 15, 18, 28, 'F'),
        (16, 16, '2025-2026', 7.8,  90.0, 0, 80, 78, 82, 'B'),
        (17, 17, '2025-2026', 6.5,  78.0, 1, 65, 60, 72, 'B'),
        (18, 18, '2024-2025', 2.5,  32.0, 5, 18, 20, 30, 'F'),
        (19, 19, '2025-2026', 8.2,  92.0, 0, 85, 82, 84, 'A'),
        (20, 20, '2025-2026', 5.8,  68.0, 2, 55, 52, 65, 'C'),
        (21, 21, '2025-2026', 9.2,  96.0, 0, 94, 90, 92, 'A'),
        (22, 22, '2025-2026', 4.5,  52.0, 3, 35, 40, 50, 'D'),
        (23, 23, '2025-2026', 7.0,  82.0, 1, 70, 68, 75, 'B'),
        (24, 24, '2024-2025', 1.8,  25.0, 6, 10, 12, 22, 'F'),
        (25, 25, '2025-2026', 7.6,  87.0, 0, 76, 74, 80, 'A'),
        (26, 26, '2025-2026', 5.2,  60.0, 2, 48, 45, 58, 'C'),
        (27, 27, '2025-2026', 9.4,  98.0, 0, 96, 94, 92, 'A'),
        (28, 28, '2024-2025', 2.0,  22.0, 6, 12, 10, 20, 'F'),
        (29, 29, '2025-2026', 7.3,  86.0, 1, 74, 70, 76, 'B'),
        (30, 30, '2025-2026', 4.0,  48.0, 3, 32, 35, 45, 'D')
    """))

    # Socioeconomic (30 records — one per student)
    conn.execute(text("""
        INSERT INTO socioeconomic VALUES
        (1,  1,  'upper_middle',  0, 0, 1, 1, 1, 'both_parents'),
        (2,  2,  'low',           1, 1, 0, 0, 3, 'both_parents'),
        (3,  3,  'high',          0, 0, 1, 1, 0, 'both_parents'),
        (4,  4,  'below_poverty', 1, 1, 0, 0, 4, 'single_parent'),
        (5,  5,  'high',          0, 0, 1, 1, 1, 'both_parents'),
        (6,  6,  'low',           1, 1, 0, 0, 5, 'both_parents'),
        (7,  7,  'middle',        0, 0, 1, 0, 2, 'both_parents'),
        (8,  8,  'below_poverty', 1, 1, 0, 0, 6, 'both_parents'),
        (9,  9,  'middle',        0, 0, 1, 1, 1, 'both_parents'),
        (10, 10, 'low',           1, 1, 0, 0, 3, 'single_parent'),
        (11, 11, 'below_poverty', 1, 1, 0, 0, 4, 'both_parents'),
        (12, 12, 'middle',        0, 0, 1, 0, 2, 'both_parents'),
        (13, 13, 'low',           1, 1, 0, 0, 3, 'both_parents'),
        (14, 14, 'high',          0, 0, 1, 1, 0, 'both_parents'),
        (15, 15, 'below_poverty', 1, 1, 0, 0, 5, 'single_parent'),
        (16, 16, 'middle',        0, 0, 1, 0, 1, 'both_parents'),
        (17, 17, 'middle',        0, 0, 1, 0, 2, 'both_parents'),
        (18, 18, 'below_poverty', 1, 1, 0, 0, 4, 'guardian'),
        (19, 19, 'upper_middle',  0, 0, 1, 1, 1, 'both_parents'),
        (20, 20, 'low',           1, 1, 0, 0, 3, 'both_parents'),
        (21, 21, 'high',          0, 0, 1, 1, 0, 'both_parents'),
        (22, 22, 'below_poverty', 1, 1, 0, 0, 5, 'both_parents'),
        (23, 23, 'middle',        0, 0, 1, 0, 2, 'both_parents'),
        (24, 24, 'below_poverty', 1, 1, 0, 0, 6, 'guardian'),
        (25, 25, 'middle',        0, 0, 1, 0, 1, 'both_parents'),
        (26, 26, 'low',           1, 1, 0, 0, 3, 'single_parent'),
        (27, 27, 'high',          0, 0, 1, 1, 1, 'both_parents'),
        (28, 28, 'below_poverty', 1, 1, 0, 0, 7, 'guardian'),
        (29, 29, 'upper_middle',  0, 0, 1, 1, 1, 'both_parents'),
        (30, 30, 'below_poverty', 1, 1, 0, 0, 4, 'single_parent')
    """))

    # Risk Assessments (30 records — one per student)
    conn.execute(text("""
        INSERT INTO risk_assessments VALUES
        (1,  1,  '2025-04-01', 0.08, 'low',      NULL, 'none',                                        'continue_monitoring'),
        (2,  2,  '2025-04-01', 0.65, 'high',      2026, 'low_attendance,failed_subjects,distance',     'transportation_aid,tutoring'),
        (3,  3,  '2025-04-01', 0.05, 'low',       NULL, 'none',                                        'continue_monitoring'),
        (4,  4,  '2025-01-15', 0.92, 'critical',  2025, 'poverty,criminal_history,distance,low_gpa',   'financial_aid,counseling,transport'),
        (5,  5,  '2025-04-01', 0.06, 'low',       NULL, 'none',                                        'continue_monitoring'),
        (6,  6,  '2025-04-01', 0.72, 'high',      2026, 'distance,low_income,rural_school',            'transportation_aid,scholarship'),
        (7,  7,  '2025-04-01', 0.25, 'medium',    NULL, 'one_failed_subject',                          'tutoring'),
        (8,  8,  '2025-01-15', 0.95, 'critical',  2025, 'poverty,criminal_history,distance,very_low_gpa', 'urgent_intervention,financial_aid'),
        (9,  9,  '2025-04-01', 0.10, 'low',       NULL, 'none',                                        'continue_monitoring'),
        (10, 10, '2025-01-15', 0.88, 'critical',  2025, 'distance,criminal_history,low_gpa,divorced',  'counseling,transport,mentoring'),
        (11, 11, '2025-04-01', 0.70, 'high',      2026, 'poverty,distance,low_attendance',             'financial_aid,transportation_aid'),
        (12, 12, '2025-04-01', 0.15, 'low',       NULL, 'none',                                        'continue_monitoring'),
        (13, 13, '2025-04-01', 0.55, 'medium',    2027, 'distance,low_income,failed_subjects',         'tutoring,scholarship'),
        (14, 14, '2025-04-01', 0.02, 'low',       NULL, 'none',                                        'none_graduated'),
        (15, 15, '2025-01-15', 0.96, 'critical',  2025, 'poverty,criminal_history,distance,very_low_gpa,absent', 'urgent_intervention,all_aid'),
        (16, 16, '2025-04-01', 0.12, 'low',       NULL, 'none',                                        'continue_monitoring'),
        (17, 17, '2025-04-01', 0.20, 'low',       NULL, 'one_failed_subject',                          'tutoring'),
        (18, 18, '2025-01-15', 0.94, 'critical',  2025, 'poverty,criminal_history,distance,orphaned,very_low_gpa', 'urgent_intervention,guardian_support'),
        (19, 19, '2025-04-01', 0.07, 'low',       NULL, 'none',                                        'continue_monitoring'),
        (20, 20, '2025-04-01', 0.48, 'medium',    2027, 'low_income,distance,failed_subjects',         'tutoring,scholarship'),
        (21, 21, '2025-04-01', 0.04, 'low',       NULL, 'none',                                        'continue_monitoring'),
        (22, 22, '2025-04-01', 0.68, 'high',      2026, 'poverty,rural_school,low_attendance',         'scholarship,counseling'),
        (23, 23, '2025-04-01', 0.22, 'medium',    NULL, 'one_failed_subject',                          'tutoring'),
        (24, 24, '2025-01-15', 0.98, 'critical',  2025, 'extreme_poverty,criminal_history,distance,no_education_parents', 'urgent_all_interventions'),
        (25, 25, '2025-04-01', 0.14, 'low',       NULL, 'none',                                        'continue_monitoring'),
        (26, 26, '2025-04-01', 0.52, 'medium',    2027, 'distance,divorced_parents,failed_subjects',   'counseling,tutoring'),
        (27, 27, '2025-04-01', 0.03, 'low',       NULL, 'none',                                        'continue_monitoring'),
        (28, 28, '2025-01-15', 0.97, 'critical',  2025, 'extreme_poverty,criminal_history,max_distance,orphaned', 'urgent_all_interventions'),
        (29, 29, '2025-04-01', 0.11, 'low',       NULL, 'none',                                        'continue_monitoring'),
        (30, 30, '2025-04-01', 0.62, 'high',      2026, 'poverty,distance,single_parent,low_gpa',     'financial_aid,mentoring')
    """))

    conn.commit()

print(f"✅ Dropout prediction database created: {DB_PATH}")
print(f"   Tables: school_info, parents, students, academics, socioeconomic, risk_assessments")
print(f"   Students: 30 records")
