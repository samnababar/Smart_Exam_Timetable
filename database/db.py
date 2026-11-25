import json
import os
import shutil
import sqlite3
import tempfile
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
LOCAL_DB_PATH = BASE_DIR / "database" / "smart_exam.db"
configured_db_path = os.environ.get("SMART_EXAM_DB_PATH")

if configured_db_path:
    DB_PATH = Path(configured_db_path)
elif os.environ.get("VERCEL"):
    DB_PATH = Path(tempfile.gettempdir()) / "smart_exam.db"
    if LOCAL_DB_PATH.is_file() and not DB_PATH.exists():
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(LOCAL_DB_PATH, DB_PATH)
else:
    DB_PATH = LOCAL_DB_PATH


def get_connection():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS subjects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT NOT NULL UNIQUE,
            name TEXT NOT NULL,
            department TEXT NOT NULL,
            semester INTEGER NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id TEXT NOT NULL UNIQUE,
            name TEXT NOT NULL,
            program TEXT NOT NULL,
            year INTEGER NOT NULL,
            email TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS enrollments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            subject_id INTEGER NOT NULL,
            UNIQUE(student_id, subject_id),
            FOREIGN KEY(student_id) REFERENCES students(id),
            FOREIGN KEY(subject_id) REFERENCES subjects(id)
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS generated_timetable (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subject_id INTEGER NOT NULL,
            slot_index INTEGER NOT NULL,
            slot_name TEXT NOT NULL,
            UNIQUE(subject_id),
            FOREIGN KEY(subject_id) REFERENCES subjects(id)
        )
        """
    )
    conn.commit()
    conn.close()

    ensure_default_settings()


def ensure_default_settings():
    defaults = {
        "school_name": "Smart Exam Timetable",
        "slot_prefix": "Exam Slot",
        "slot_count": "6",
        "slot_start_time": "09:00",
        "slot_duration_minutes": "120",
        "exam_day": "Monday",
    }
    conn = get_connection()
    for key, value in defaults.items():
        conn.execute(
            "INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)",
            (key, value),
        )
    conn.commit()
    conn.close()


def get_settings():
    conn = get_connection()
    rows = conn.execute("SELECT key, value FROM settings").fetchall()
    conn.close()
    settings = {row["key"]: row["value"] for row in rows}
    return settings


def set_setting(key, value):
    conn = get_connection()
    conn.execute(
        "INSERT INTO settings (key, value) VALUES (?, ?) "
        "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
        (key, str(value)),
    )
    conn.commit()
    conn.close()


def fetch_subjects():
    conn = get_connection()
    rows = conn.execute(
        """
        SELECT s.id, s.code, s.name, s.department, s.semester,
               COUNT(DISTINCT e.student_id) AS student_count
        FROM subjects s
        LEFT JOIN enrollments e ON e.subject_id = s.id
        GROUP BY s.id, s.code, s.name, s.department, s.semester
        ORDER BY s.code ASC
        """
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def fetch_students():
    conn = get_connection()
    rows = conn.execute(
        """
        SELECT st.id, st.student_id, st.name, st.program, st.year, st.email,
               COUNT(e.subject_id) AS enrolled_subjects
        FROM students st
        LEFT JOIN enrollments e ON e.student_id = st.id
        GROUP BY st.id, st.student_id, st.name, st.program, st.year, st.email
        ORDER BY st.name ASC
        """
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def fetch_enrollments():
    conn = get_connection()
    rows = conn.execute(
        """
        SELECT e.id, e.student_id, e.subject_id, s.name AS subject_name,
               st.name AS student_name, st.student_id AS student_code,
               sb.code AS subject_code
        FROM enrollments e
        JOIN students st ON st.id = e.student_id
        JOIN subjects s ON s.id = e.subject_id
        JOIN subjects sb ON sb.id = e.subject_id
        ORDER BY st.name, s.name
        """
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def add_subject(code, name, department, semester):
    conn = get_connection()
    conn.execute(
        "INSERT INTO subjects (code, name, department, semester) VALUES (?, ?, ?, ?)",
        (code.strip(), name.strip(), department.strip(), int(semester)),
    )
    conn.commit()
    conn.close()


def update_subject(subject_id, code, name, department, semester):
    conn = get_connection()
    conn.execute(
        "UPDATE subjects SET code = ?, name = ?, department = ?, semester = ? WHERE id = ?",
        (code.strip(), name.strip(), department.strip(), int(semester), int(subject_id)),
    )
    conn.commit()
    conn.close()


def delete_subject(subject_id):
    conn = get_connection()
    conn.execute("DELETE FROM enrollments WHERE subject_id = ?", (int(subject_id),))
    conn.execute("DELETE FROM subjects WHERE id = ?", (int(subject_id),))
    conn.execute("DELETE FROM generated_timetable WHERE subject_id = ?", (int(subject_id),))
    conn.commit()
    conn.close()


def add_student(student_id, name, program, year, email):
    conn = get_connection()
    conn.execute(
        "INSERT INTO students (student_id, name, program, year, email) VALUES (?, ?, ?, ?, ?)",
        (student_id.strip(), name.strip(), program.strip(), int(year), email.strip() if email else None),
    )
    conn.commit()
    conn.close()


def update_student(student_id, student_code, name, program, year, email):
    conn = get_connection()
    conn.execute(
        "UPDATE students SET student_id = ?, name = ?, program = ?, year = ?, email = ? WHERE id = ?",
        (student_code.strip(), name.strip(), program.strip(), int(year), email.strip() if email else None, int(student_id)),
    )
    conn.commit()
    conn.close()


def delete_student(student_id):
    conn = get_connection()
    conn.execute("DELETE FROM enrollments WHERE student_id = ?", (int(student_id),))
    conn.execute("DELETE FROM students WHERE id = ?", (int(student_id),))
    conn.commit()
    conn.close()


def add_enrollment(student_id, subject_ids):
    conn = get_connection()
    for subject_id in subject_ids:
        conn.execute(
            "INSERT OR IGNORE INTO enrollments (student_id, subject_id) VALUES (?, ?)",
            (int(student_id), int(subject_id)),
        )
    conn.commit()
    conn.close()


def delete_enrollment(student_id, subject_id):
    conn = get_connection()
    conn.execute(
        "DELETE FROM enrollments WHERE student_id = ? AND subject_id = ?",
        (int(student_id), int(subject_id)),
    )
    conn.commit()
    conn.close()


def fetch_conflicts():
    subjects = fetch_subjects()
    enrollments = fetch_enrollments()
    conflicts = []
    subject_map = {subject["id"]: subject for subject in subjects}
    student_to_subjects = {}
    for enrollment in enrollments:
        student_to_subjects.setdefault(enrollment["student_id"], set()).add(enrollment["subject_id"])

    for related_subjects in student_to_subjects.values():
        related_subjects = sorted(related_subjects)
        for i in range(len(related_subjects)):
            for j in range(i + 1, len(related_subjects)):
                left = related_subjects[i]
                right = related_subjects[j]
                conflicts.append({
                    "subject_a": subject_map[left]["code"],
                    "subject_b": subject_map[right]["code"],
                    "subject_a_name": subject_map[left]["name"],
                    "subject_b_name": subject_map[right]["name"],
                })

    return conflicts


def seed_sample_data():
    conn = get_connection()
    if conn.execute("SELECT COUNT(*) FROM subjects").fetchone()[0] > 0:
        conn.close()
        return

    sample_subjects = [
        ("CSC-201", "Discrete Structures", "Computer Science", 2),
        ("CSC-202", "Data Structures", "Computer Science", 2),
        ("CSC-203", "Database Systems", "Computer Science", 2),
        ("CSC-204", "Operating Systems", "Computer Science", 2),
        ("CSC-205", "Computer Networks", "Computer Science", 2),
        ("CSC-206", "Algorithms", "Computer Science", 2),
    ]
    conn.executemany(
        "INSERT INTO subjects (code, name, department, semester) VALUES (?, ?, ?, ?)",
        sample_subjects,
    )

    sample_students = [
        ("2024-CS-001", "Ayesha Khan", "CS", 2, "ayesha@example.com"),
        ("2024-CS-002", "Bilal Ahmed", "CS", 2, "bilal@example.com"),
        ("2024-CS-003", "Hina Noor", "CS", 2, "hina@example.com"),
        ("2024-CS-004", "Ali Hassan", "CS", 2, "ali@example.com"),
        ("2024-CS-005", "Sana Ali", "CS", 2, "sana@example.com"),
        ("2024-CS-006", "Hamza Tariq", "CS", 2, "hamza@example.com"),
        ("2024-CS-007", "Faisal Raza", "CS", 2, "faisal@example.com"),
        ("2024-CS-008", "Zoya Shah", "CS", 2, "zoya@example.com"),
        ("2024-CS-009", "Usman Malik", "CS", 2, "usman@example.com"),
        ("2024-CS-010", "Areeba Javed", "CS", 2, "areeba@example.com"),
    ]
    conn.executemany(
        "INSERT INTO students (student_id, name, program, year, email) VALUES (?, ?, ?, ?, ?)",
        sample_students,
    )

    subject_map = {code: id for code, _, _, _ in sample_subjects for id in [None]}
    # Use row ids directly in the database.
    subject_rows = conn.execute("SELECT id, code FROM subjects ORDER BY id").fetchall()
    subject_map = {row["code"]: row["id"] for row in subject_rows}

    enrollment_groups = [
        ("2024-CS-001", ["CSC-201", "CSC-202", "CSC-203"]),
        ("2024-CS-002", ["CSC-201", "CSC-205", "CSC-206"]),
        ("2024-CS-003", ["CSC-202", "CSC-203", "CSC-204"]),
        ("2024-CS-004", ["CSC-201", "CSC-204", "CSC-205"]),
        ("2024-CS-005", ["CSC-202", "CSC-205", "CSC-206"]),
        ("2024-CS-006", ["CSC-203", "CSC-204", "CSC-206"]),
        ("2024-CS-007", ["CSC-201", "CSC-203", "CSC-205"]),
        ("2024-CS-008", ["CSC-202", "CSC-204", "CSC-206"]),
        ("2024-CS-009", ["CSC-201", "CSC-205", "CSC-206"]),
        ("2024-CS-010", ["CSC-202", "CSC-203", "CSC-204"]),
    ]

    for student_id_code, subject_codes in enrollment_groups:
        student_row = conn.execute("SELECT id FROM students WHERE student_id = ?", (student_id_code,)).fetchone()
        student_id = student_row["id"]
        for subject_code in subject_codes:
            subject_id = subject_map[subject_code]
            conn.execute(
                "INSERT OR IGNORE INTO enrollments (student_id, subject_id) VALUES (?, ?)",
                (student_id, subject_id),
            )

    conn.commit()
    conn.close()
