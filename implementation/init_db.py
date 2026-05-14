from __future__ import annotations

import sqlite3
from pathlib import Path


DEFAULT_DB_PATH = Path(__file__).resolve().parent / "sqlite_lab.db"

SCHEMA_SQL = """
DROP TABLE IF EXISTS enrollments;
DROP TABLE IF EXISTS courses;
DROP TABLE IF EXISTS students;

CREATE TABLE students (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    full_name TEXT NOT NULL,
    cohort TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    age INTEGER NOT NULL,
    score REAL NOT NULL
);

CREATE TABLE courses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    course_code TEXT NOT NULL UNIQUE,
    title TEXT NOT NULL,
    credits INTEGER NOT NULL
);

CREATE TABLE enrollments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER NOT NULL,
    course_id INTEGER NOT NULL,
    semester TEXT NOT NULL,
    status TEXT NOT NULL,
    final_score REAL,
    FOREIGN KEY (student_id) REFERENCES students(id),
    FOREIGN KEY (course_id) REFERENCES courses(id)
);
"""

SEED_SQL = """
INSERT INTO students (full_name, cohort, email, age, score) VALUES
('Nguyen Van An', 'A1', 'an.nguyen@example.com', 20, 8.6),
('Tran Minh Chau', 'A1', 'chau.tran@example.com', 21, 7.9),
('Le Hoang Giang', 'B2', 'giang.le@example.com', 22, 9.1),
('Pham Thu Ha', 'B2', 'ha.pham@example.com', 20, 8.3),
('Do Quoc Khang', 'C3', 'khang.do@example.com', 23, 7.2);

INSERT INTO courses (course_code, title, credits) VALUES
('AI101', 'Introduction to AI', 3),
('DB201', 'Database Systems', 4),
('PY301', 'Applied Python', 3);

INSERT INTO enrollments (student_id, course_id, semester, status, final_score) VALUES
(1, 1, '2026S1', 'active', 8.8),
(1, 2, '2026S1', 'active', 8.2),
(2, 1, '2026S1', 'active', 7.8),
(3, 2, '2026S1', 'active', 9.4),
(4, 3, '2026S1', 'completed', 8.7),
(5, 3, '2026S1', 'completed', 7.0);
"""


def create_database(db_path: str | Path = DEFAULT_DB_PATH) -> str:
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(path) as connection:
        connection.executescript(SCHEMA_SQL)
        connection.executescript(SEED_SQL)
        connection.commit()
    return str(path)


if __name__ == "__main__":
    created_path = create_database()
    print(f"Database initialized at {created_path}")
