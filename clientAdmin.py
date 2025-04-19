import socket
import json
import sys
import getpass

class AUBRegistrarAdminClient:
    def __init__(self, host='localhost', port=5000):
        self.host = host
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connected = False

    def connect(self):
        try:
            self.socket.connect((self.host, self.port))
            self.connected = True
            print("Connected to AUB Registrar Server")
            return True
        except Exception as e:
            print(f"Error connecting to server: {str(e)}")
            return False

    def send_request(self, request):
        try:
            self.socket.send(json.dumps(request).encode())
            response = self.socket.recv(4096).decode()
            return json.loads(response)
        except Exception as e:
            print(f"Error communicating with server: {str(e)}")
            return {"status": "error", "message": "Communication error"}

    def login(self):
        while True:
            username = input("Admin Username: ")
            password = getpass.getpass("Password: ")
            
            response = self.send_request({
                "command": "login",
                "username": username,
                "password": password
            })
            
            if response.get("status") == "success" and response.get("role") == "admin":
                print("Login successful!")
                return True
            else:
                print("Invalid credentials. Please try again.")

    def list_courses(self):
        response = self.send_request({
            "command": "list_courses"
        })
        
        if response.get("status") == "success":
            courses = response.get("courses", [])
            if not courses:
                print("No courses available.")
                return
            
            print("\nAvailable Courses:")
            print("-" * 100)
            print(f"{'Course Name':<20} {'Capacity':<10} {'Remaining':<10} {'Schedule':<20} {'Students':<30}")
            print("-" * 100)
            
            for course in courses:
                students = ", ".join(course['students']) if course['students'] else "None"
                print(f"{course['course_name']:<20} {course['capacity']:<10} {course['remaining']:<10} {course['schedule']:<20} {students:<30}")
        else:
            print("Error listing courses:", response.get("message"))

    def create_course(self):
        course_name = input("Enter course name: ")
        try:
            capacity = int(input("Enter course capacity: "))
            if capacity <= 0:
                print("Capacity must be a positive number")
                return
        except ValueError:
            print("Capacity must be a number")
            return
        
        schedule = input("Enter course schedule: ")
        
        response = self.send_request({
            "command": "create_course",
            "course_name": course_name,
            "capacity": capacity,
            "schedule": schedule
        })
        
        if response.get("status") == "success":
            print("Course created successfully")
        else:
            print("Error:", response.get("message"))

    def update_course_capacity(self):
        course_name = input("Enter course name: ")
        try:
            new_capacity = int(input("Enter new capacity: "))
            if new_capacity <= 0:
                print("Capacity must be a positive number")
                return
        except ValueError:
            print("Capacity must be a number")
            return
        
        response = self.send_request({
            "command": "update_course",
            "course_name": course_name,
            "new_capacity": new_capacity
        })
        
        if response.get("status") == "success":
            print("Course capacity updated successfully")
        else:
            print("Error:", response.get("message"))

    def add_student(self):
        username = input("Enter student username: ")
        password = getpass.getpass("Enter student password: ")
        
        response = self.send_request({
            "command": "add_student",
            "student_username": username,
            "student_password": password
        })
        
        if response.get("status") == "success":
            print("Student added successfully")
        else:
            print("Error:", response.get("message"))

    def show_menu(self):
        print("\nAUB Registrar - Admin Portal")
        print("1. List All Courses")
        print("2. Create New Course")
        print("3. Update Course Capacity")
        print("4. Add New Student")
        print("5. Exit")
        
        choice = input("\nEnter your choice (1-5): ")
        return choice

    def run(self):
        if not self.connect():
            return
        
        if not self.login():
            return
        
        while True:
            choice = self.show_menu()
            
            if choice == "1":
                self.list_courses()
            elif choice == "2":
                self.create_course()
            elif choice == "3":
                self.update_course_capacity()
            elif choice == "4":
                self.add_student()
            elif choice == "5":
                print("Thank you for using AUB Registrar. Goodbye!")
                break
            else:
                print("Invalid choice. Please try again.")
        
        self.socket.close()

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python clientAdmin.py <host> <port>")
        sys.exit(1)
    
    try:
        host = sys.argv[1]
        port = int(sys.argv[2])
        client = AUBRegistrarAdminClient(host, port)
        client.run()
    except ValueError:
        print("Port must be a number")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)

