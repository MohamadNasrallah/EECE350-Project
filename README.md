# AUB Registrar

An online client‑server platform for AUB ECE students to register for courses.  
Built for EECE 350 – Computer Networks (Spring 2025).

## Features

- **Admin portal**  
  - List all courses with capacity, remaining seats, schedule, and enrolled students  
  - Create new courses  
  - Increase course capacity  
  - Add new student accounts  

- **Student portal**  
  - Secure login with immediate display of registered courses  
  - List all available courses (with capacity, remaining seats, schedule)  
  - Register for a course (max 5, no duplicates, no schedule conflicts, seats available)  
  - Withdraw from a course  

## Architecture

- **Transport:** TCP sockets  
- **Message format:** JSON  
- **Concurrency:** One thread per client on server side  
- **Persistence:** SQLite via `database.py`

## Getting Started

### Prerequisites

- Python 3.7+  
- `sqlite3` (standard with Python)  

### Installation

1. Clone this repo:  
   ```bash
   git clone https://github.com/<your‑username>/aub‑registrar.git
   cd aub-registrar
