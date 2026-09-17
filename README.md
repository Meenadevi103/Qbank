# Question Paper Management System

A production-ready Question Paper Management System built with Django and Bootstrap 5. 
Designed for academic institutions to manage previous year question papers.

## Features
- **Student Portal:** Browse Departments, Semesters, Subjects, and Question Papers.
- **Search:** Global search across subjects, years, and exam types.
- **Admin Dashboard:** Comprehensive dashboard for managing all entities.

## Tech Stack
- **Backend:** Django (Python)
- **Frontend:** HTML5, CSS3, Bootstrap 5, Vanilla JS, Chart.js
- **Database:** PostgreSQL (Production) / SQLite (Development)
- **Deployment:** Gunicorn, Nginx

## Installation

### 1. Clone & Set Up Virtual Environment
```bash
git clone <repository_url>
cd Qbank
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Environment Variables
Copy the `.env.example` file to `.env` and configure your settings:
```bash
cp .env.example .env
```

### 4. Database Setup
```bash
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
```

### 5. Run Server
```bash
python manage.py runserver
```

## Production Deployment (Gunicorn + Nginx)

1. **Collect Static Files:**
```bash
python manage.py collectstatic
```

2. **Run Gunicorn:**
```bash
gunicorn --bind 0.0.0.0:8000 qbank.wsgi:application
```

3. **Nginx Configuration:**
Create an Nginx server block:
```nginx
server {
    listen 80;
    server_name yourdomain.com;

    location = /favicon.ico { access_log off; log_not_found off; }
    
    location /static/ {
        root /path/to/qbank/staticfiles;
    }

    location /media/ {
        root /path/to/qbank/media;
    }

    location / {
        proxy_set_header Host $http_host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_pass http://127.0.0.1:8000;
    }
}
```

## Architecture Notes
- The OCR processing avoids duplicates by maintaining an `ExtractedText` model mapping 1:1 with `QuestionPaper`.
- The UI follows a professional academic theme with `#004E89` primary color.
