import socket
import json
import sys
import getpass

class AUBRegistrarStudentClient:
    def __init__(self, host='localhost', port=5000):
        self.host = host
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.username = None
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
        """Authenticate the student and immediately show their current schedule."""
        while True:
            username = input("Username: ")
            password = getpass.getpass("Password: ")

            response = self.send_request({
                "command": "login",
                "username": username,
                "password": password
            })

            if response.get("status") == "success" and response.get("role") == "student":
                self.username = username
                print("Login successful!\n")
                # NEW ➜ display the list (or 'No courses registered yet')
                self.view_registered_courses()
                return True
            else:
                print("Invalid credentials. Please try again.\n")
                
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
            print("-" * 80)
            print(f"{'Course Name':<20} {'Capacity':<10} {'Remaining':<10} {'Schedule':<20}")
            print("-" * 80)
            
            for course in courses:
                print(f"{course['course_name']:<20} {course['capacity']:<10} {course['remaining']:<10} {course['schedule']:<20}")
        else:
            print("Error listing courses:", response.get("message"))

    def view_registered_courses(self):
        response = self.send_request({
            "command": "get_registered_courses",
            "username": self.username
        })
        
        if response.get("status") == "success":
            registered_courses = response.get("registered_courses", [])
            if not registered_courses:
                print("\nNo courses registered yet")
                return
            
            print("\nYour Registered Courses:")
            print("-" * 80)
            print(f"{'Course Name':<20}")
            print("-" * 80)
            
            for course in registered_courses:
                print(f"{course:<20}")
        else:
            print("Error getting registered courses:", response.get("message"))

    def register_course(self):
        course_name = input("Enter course name to register: ")
        
        response = self.send_request({
            "command": "register_course",
            "username": self.username,
            "course_name": course_name
        })
        
        if response.get("status") == "success":
            print("Successfully registered for", course_name)
        else:
            print("Error:", response.get("message"))

    def withdraw_course(self):
        course_name = input("Enter course name to withdraw from: ")
        
        response = self.send_request({
            "command": "withdraw_course",
            "username": self.username,
            "course_name": course_name
        })
        
        if response.get("status") == "success":
            print("Successfully withdrawn from", course_name)
        else:
            print("Error:", response.get("message"))

    def show_menu(self):
        print("\nAUB Registrar - Student Portal")
        print("1. List Available Courses")
        print("2. Register for a Course")
        print("3. Withdraw from a Course")
        print("4. View My Registered Courses")
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
                self.register_course()
            elif choice == "3":
                self.withdraw_course()
            elif choice == "4":
                self.view_registered_courses()
            elif choice == "5":
                print("Thank you for using AUB Registrar. Goodbye!")
                break
            else:
                print("Invalid choice. Please try again.")
        
        self.socket.close()

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python clientStudent.py <host> <port>")
        sys.exit(1)
    
    try:
        host = sys.argv[1]
        port = int(sys.argv[2])
        client = AUBRegistrarStudentClient(host, port)
        client.run()
    except ValueError:
        print("Port must be a number")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)

