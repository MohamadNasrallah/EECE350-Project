import socket
import threading
import json
import sys
from database import AUBRegistrarDatabase

class AUBRegistrarServer:
    def __init__(self, port):
        self.port = port
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.db_name = "aub_registrar.db"
        
        # Initialize database schema
        with AUBRegistrarDatabase(self.db_name) as db:
            pass  # The database will create tables in its __init__
        
        # Start server
        self.server_socket.bind(('', self.port))
        self.server_socket.listen(5)
        print(f"Server started on port {self.port}")

    def handle_client(self, client_socket, address):
        try:
            with AUBRegistrarDatabase(self.db_name) as db:
                while True:
                    data = client_socket.recv(4096).decode()
                    if not data:
                        break
                    
                    request = json.loads(data)
                    response = self.process_request(request, db)
                    client_socket.send(json.dumps(response).encode())
        except Exception as e:
            print(f"Error handling client {address}: {str(e)}")
        finally:
            client_socket.close()

    def process_request(self, request, db):
        command = request.get("command")
        username = request.get("username")
        password = request.get("password")
        
        # Authentication
        if command == "login":
            role = db.authenticate(username, password)
            if role:
                return {"status": "success", "role": role}
            else:
                return {"status": "error", "message": "Invalid credentials"}
        
        # Admin commands
        if command == "create_course":
            course_name = request.get("course_name")
            capacity = request.get("capacity")
            schedule = request.get("schedule")
            
            if db.create_course(course_name, capacity, schedule):
                return {"status": "success", "message": "Course created successfully"}
            else:
                return {"status": "error", "message": "Course already exists"}
        
        if command == "update_course":
            course_name = request.get("course_name")
            new_capacity = request.get("new_capacity")
            
            if db.update_course_capacity(course_name, new_capacity):
                return {"status": "success", "message": "Course capacity updated"}
            else:
                return {"status": "error", "message": "Course does not exist or invalid capacity"}
        
        if command == "add_student":
            username = request.get("student_username")
            password = request.get("student_password")
            
            if db.add_student(username, password):
                return {"status": "success", "message": "Student added successfully"}
            else:
                return {"status": "error", "message": "Student already exists"}
        
        # Student commands
        if command == "list_courses":
            courses = db.get_courses()
            return {"status": "success", "courses": courses}
        
        if command == "register_course":
            course_name = request.get("course_name")
            
            if db.register_course(username, course_name):
                return {"status": "success", "message": "Course registered successfully"}
            else:
                return {"status": "error", "message": "Cannot register for course"}
        
        if command == "withdraw_course":
            course_name = request.get("course_name")
            
            if db.withdraw_course(username, course_name):
                return {"status": "success", "message": "Course withdrawn successfully"}
            else:
                return {"status": "error", "message": "Cannot withdraw from course"}
        
        return {"status": "error", "message": "Invalid command"}

    def start(self):
        try:
            while True:
                client_socket, address = self.server_socket.accept()
                print(f"New connection from {address}")
                client_thread = threading.Thread(target=self.handle_client, args=(client_socket, address))
                client_thread.start()
        except KeyboardInterrupt:
            print("Server shutting down...")
        finally:
            self.server_socket.close()

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python server.py <port>")
        sys.exit(1)
    
    try:
        port = int(sys.argv[1])
        server = AUBRegistrarServer(port)
        server.start()
    except ValueError:
        print("Port must be a number")
        sys.exit(1)

