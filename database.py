import sqlite3
import json
from typing import List, Dict, Set, Optional

class AUBRegistrarDatabase:
    def __init__(self, db_name: str = "aub_registrar.db"):
        self.db_name = db_name
        self.conn = None
        self._create_tables()

    def __enter__(self):
        self.conn = sqlite3.connect(self.db_name)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.conn:
            self.conn.close()
            self.conn = None

    def _create_tables(self):
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            
            # Create courses table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS courses (
                course_name TEXT PRIMARY KEY,
                capacity INTEGER NOT NULL,
                remaining INTEGER NOT NULL,
                schedule TEXT NOT NULL,
                students TEXT DEFAULT '[]'  -- JSON array of student usernames
            )
            ''')
            
            # Create students table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS students (
                username TEXT PRIMARY KEY,
                password TEXT NOT NULL,
                registered_courses TEXT DEFAULT '[]'  -- JSON array of course names
            )
            ''')
            
            # Create admin table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS admin (
                username TEXT PRIMARY KEY,
                password TEXT NOT NULL
            )
            ''')
            
            # Insert default admin if not exists
            cursor.execute('''
            INSERT OR IGNORE INTO admin (username, password)
            VALUES ('admin', 'admin123')
            ''')
            
            conn.commit()

    def add_student(self, username: str, password: str) -> bool:
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
            INSERT INTO students (username, password)
            VALUES (?, ?)
            ''', (username, password))
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False

    def create_course(self, course_name: str, capacity: int, schedule: str) -> bool:
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
            INSERT INTO courses (course_name, capacity, remaining, schedule)
            VALUES (?, ?, ?, ?)
            ''', (course_name, capacity, capacity, schedule))
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False

    def update_course_capacity(self, course_name: str, new_capacity: int) -> bool:
        cursor = self.conn.cursor()
        cursor.execute('''
        SELECT capacity, students FROM courses WHERE course_name = ?
        ''', (course_name,))
        result = cursor.fetchone()
        
        if not result:
            return False
        
        current_capacity, students_json = result
        if new_capacity < current_capacity:
            return False
        
        # Update capacity and remaining seats
        students = json.loads(students_json)
        remaining = new_capacity - len(students)
        
        cursor.execute('''
        UPDATE courses
        SET capacity = ?, remaining = ?
        WHERE course_name = ?
        ''', (new_capacity, remaining, course_name))
        self.conn.commit()
        return True

    def register_course(self, username: str, course_name: str) -> bool:
        cursor = self.conn.cursor()
        
        # Check if course exists and has available seats
        cursor.execute('''
        SELECT remaining, schedule, students FROM courses WHERE course_name = ?
        ''', (course_name,))
        course_result = cursor.fetchone()
        
        if not course_result or course_result[0] <= 0:
            return False
        
        # Get student's registered courses
        cursor.execute('''
        SELECT registered_courses FROM students WHERE username = ?
        ''', (username,))
        student_result = cursor.fetchone()
        
        if not student_result:
            return False
        
        registered_courses = json.loads(student_result[0])
        if len(registered_courses) >= 5:
            return False
        
        # Check for schedule conflicts
        if registered_courses:
            placeholders = ','.join(['?' for _ in registered_courses])
            cursor.execute(f'''
            SELECT schedule FROM courses WHERE course_name IN ({placeholders})
            ''', registered_courses)
            
            for existing_schedule in cursor.fetchall():
                if existing_schedule[0] == course_result[1]:
                    return False
        
        # Update course
        students = json.loads(course_result[2])
        students.append(username)
        cursor.execute('''
        UPDATE courses
        SET remaining = ?, students = ?
        WHERE course_name = ?
        ''', (course_result[0] - 1, json.dumps(students), course_name))
        
        # Update student
        registered_courses.append(course_name)
        cursor.execute('''
        UPDATE students
        SET registered_courses = ?
        WHERE username = ?
        ''', (json.dumps(registered_courses), username))
        
        self.conn.commit()
        return True

    def withdraw_course(self, username: str, course_name: str) -> bool:
        cursor = self.conn.cursor()
        
        # Get course details
        cursor.execute('''
        SELECT remaining, students FROM courses WHERE course_name = ?
        ''', (course_name,))
        course_result = cursor.fetchone()
        
        if not course_result:
            return False
        
        # Get student's registered courses
        cursor.execute('''
        SELECT registered_courses FROM students WHERE username = ?
        ''', (username,))
        student_result = cursor.fetchone()
        
        if not student_result:
            return False
        
        registered_courses = json.loads(student_result[0])
        if course_name not in registered_courses:
            return False
        
        # Update course
        students = json.loads(course_result[1])
        students.remove(username)
        cursor.execute('''
        UPDATE courses
        SET remaining = ?, students = ?
        WHERE course_name = ?
        ''', (course_result[0] + 1, json.dumps(students), course_name))
        
        # Update student
        registered_courses.remove(course_name)
        cursor.execute('''
        UPDATE students
        SET registered_courses = ?
        WHERE username = ?
        ''', (json.dumps(registered_courses), username))
        
        self.conn.commit()
        return True

    def get_courses(self) -> List[Dict]:
        cursor = self.conn.cursor()
        cursor.execute('''
        SELECT course_name, capacity, remaining, schedule, students
        FROM courses
        ''')
        
        courses = []
        for row in cursor.fetchall():
            courses.append({
                "course_name": row[0],
                "capacity": row[1],
                "remaining": row[2],
                "schedule": row[3],
                "students": json.loads(row[4])
            })
        return courses

    def get_student_courses(self, username: str) -> List[str]:
        cursor = self.conn.cursor()
        cursor.execute('''
        SELECT registered_courses FROM students WHERE username = ?
        ''', (username,))
        result = cursor.fetchone()
        return json.loads(result[0]) if result else []

    def authenticate(self, username: str, password: str) -> Optional[str]:
        cursor = self.conn.cursor()
        
        # Check admin
        cursor.execute('''
        SELECT 1 FROM admin WHERE username = ? AND password = ?
        ''', (username, password))
        if cursor.fetchone():
            return "admin"
        
        # Check student
        cursor.execute('''
        SELECT 1 FROM students WHERE username = ? AND password = ?
        ''', (username, password))
        if cursor.fetchone():
            return "student"
        
        return None


