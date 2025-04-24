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
                    
                    try:
                        request = json.loads(data)
                        print(f"Received request: {request}")  # Debug logging
                        response = self.process_request(request, db)
                        print(f"Sending response: {response}")  # Debug logging
                        client_socket.send(json.dumps(response).encode())
                    except json.JSONDecodeError as e:
                        print(f"JSON decode error: {str(e)}")
                        client_socket.send(json.dumps({
                            "status": "error",
                            "message": "Invalid request format"
                        }).encode())
                    except Exception as e:
                        print(f"Error processing request: {str(e)}")
                        client_socket.send(json.dumps({
                            "status": "error",
                            "message": "Internal server error"
                        }).encode())
        except Exception as e:
            print(f"Error handling client {address}: {str(e)}")
        finally:
            client_socket.close()
    def process_request(self, request, db):
        """
        Handle every incoming JSON request and return a JSON‑serialisable dict.
        NOTE: this is now a single if/elif/else ladder so we always hit at most
        one branch and never fall through to the generic "Invalid command".
        """
        try:
            command  = (request.get("command") or "").lower()
            username = request.get("username")
            password = request.get("password")

            # ------------------------------------------------------------------
            # 1) LOGIN  ─────────────────────────────────────────────────────────
            if command == "login":
                role = db.authenticate(username, password)
                return ({"status": "success", "role": role}
                        if role else
                        {"status": "error", "message": "Invalid credentials"})

            # ------------------------------------------------------------------
            # 2) STUDENT COMMANDS  ─────────────────────────────────────────────
            elif command == "list_courses":
                return {"status": "success", "courses": db.get_courses()}

            elif command == "get_registered_courses":
                if not username:
                    return {"status": "error", "message": "Username not provided"}
                courses = db.get_student_courses(username)
                return {"status": "success", "registered_courses": courses}

            elif command == "register_course":
                course_name = request.get("course_name")
                ok = db.register_course(username, course_name)
                return ({"status": "success", "message": "Course registered successfully"}
                        if ok else
                        {"status": "error", "message": "Cannot register for course"})

            elif command == "withdraw_course":
                course_name = request.get("course_name")
                ok = db.withdraw_course(username, course_name)
                return ({"status": "success", "message": "Course withdrawn successfully"}
                        if ok else
                        {"status": "error", "message": "Cannot withdraw from course"})

            # ------------------------------------------------------------------
            # 3) ADMIN COMMANDS  ───────────────────────────────────────────────
            elif command == "create_course":
                ok = db.create_course(request.get("course_name"),
                                      request.get("capacity"),
                                      request.get("schedule"))
                return ({"status": "success", "message": "Course created successfully"}
                        if ok else
                        {"status": "error", "message": "Course already exists"})

            elif command == "update_course":
                ok = db.update_course_capacity(request.get("course_name"),
                                               request.get("new_capacity"))
                return ({"status": "success", "message": "Course capacity updated"}
                        if ok else
                        {"status": "error", "message": "Course does not exist or invalid capacity"})

            elif command == "add_student":
                ok = db.add_student(request.get("student_username"),
                                    request.get("student_password"),
                                    request.get("student_full_name"))
                return ({"status": "success", "message": "Student added successfully"}
                        if ok else
                        {"status": "error", "message": "Student already exists"})

            # ------------------------------------------------------------------
            # 4) UNKNOWN COMMAND  ──────────────────────────────────────────────
            else:
                return {"status": "error", "message": "Invalid command"}

        except Exception as e:
            print(f"Error in process_request: {e}")
            return {"status": "error", "message": "Internal server error"}


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

