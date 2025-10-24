# College Bus Management System

## Overview
College Bus Management System ek **Django-based web application** hai jo college students ke liye bus routes, registration, feedback aur reporting manage karta hai. Ye system **student registration, bus allotment, route management, and feedback collection** ko streamline karta hai.

- Built with **Django 5.1**
- Frontend uses **HTML, CSS (Glassmorphism style), Django templates**
- Backend database: **SQLite (development)**, can be switched to PostgreSQL/MySQL in production
- User authentication and middleware based access control
- Responsive design and interactive admin panel

---

## Features

### 1. Student Features
- **Student Registration**: Students apne details register kar sakte hain.
- **Login Protection**: Middleware ensures only logged-in users can access protected pages.
- **Feedback Submission**: Students can submit feedback for buses via dropdown selection.
- **About & Choice Pages**: Students can view “About Us” page, then choose between registration or feedback forms.

### 2. Admin Features
- **Bus & Route Management**: Add, edit, delete buses and routes.
- **Driver Management**: Assign drivers to buses and manage driver info.
- **Reporting Dashboard**:
  - Total buses, students, routes
  - Students per bus and per route
  - Gender distribution
  - Top contributing schools/programs
  - Interactive charts with Chart.js
- **Feedback Overview**: View all submitted feedbacks

### 3. Security
- **LoginRequiredMiddleware**: Ensures pages cannot be accessed without login.
- **CSRF Protection**: All forms include CSRF tokens.
- **Environment Safety**: Sensitive info like emails and passwords stored via environment variables or settings.py (for development).

---

## Installation & Setup

### Prerequisites
- Python 3.11+
- Virtual environment (`venv`)
- Git
- Django 5.1+

### Steps
1. **Clone the repository**
```bash
git clone https://github.com/Prakharbajpai17414/transportation-system.git
cd college_bus_management
Create virtual environment

bash
Copy code
python -m venv venv
# Activate environment
source venv/bin/activate   # Linux/macOS
venv\Scripts\activate      # Windows
Install dependencies

bash
Copy code
pip install -r requirements.txt
Apply migrations

bash
Copy code
python manage.py migrate
Create superuser (for admin panel)

bash
Copy code
python manage.py createsuperuser
Run the development server

bash
Copy code
python manage.py runserver
Visit http://127.0.0.1:8000/login/ to access login page

Notes
Static files: bus_app/static/ contains logos, CSS, JS.

Collected static files: staticfiles/ is ignored in GitHub (.gitignore).

DEBUG:

Development: DEBUG=True → all static files served automatically

Production: DEBUG=False → run python manage.py collectstatic and serve via web server

Email settings: Configured for Gmail SMTP. For production, use environment variables for security.

Contribution
Pull requests are welcome

Ensure venv/ and staticfiles/ are not pushed

Use requirements.txt to manage Python packages
