# EV Stock Manager - Backend

This is the backend for the EV Stock Manager project, built using Django and Django REST Framework. It provides APIs to manage inventory, sales, leads, and core functionalities for an electric vehicle stock management system.

## Tech Stack
- **Framework:** Django 5.2
- **API:** Django REST Framework (DRF)
- **Authentication:** JWT (JSON Web Tokens) via djangorestframework-simplejwt
- **Database:** SQLite (default for development, can be configured for PostgreSQL/MySQL in production)

## Key Features
- **Universal Search**: Instantly search across inventory, models, leads, and sales/invoices globally from the top navigation.
- **Identity & Finance Tracking**: Store and manage optional Aadhar and PAN details (including photo uploads) for leads and sales.
- **Printable Invoices**: Automatically generate professional, printable invoices linked to every completed sale.
- **Asset Tracking**: Powerful asset tracking to look up the complete history, status, and associated sale of any chassis, charger, or battery.
- **Automated Administration**: Automatically generates a default `admin` superuser upon application startup. Hidden administrative signup endpoint for secure access.

## Project Structure
- `core/`: Core application containing shared models, utilities, and user management.
- `inventory/`: Manages EV stock, vehicles, parts, and stock movements.
- `leads/`: Manages potential customer leads and inquiries.
- `sales/`: Manages sales records, transactions, and customer details.
- `core_project/`: Main project configuration directory.

## Local Development Setup

Follow these steps to set up the project locally for development.

### Prerequisites
- Python 3.10+
- pip (Python package installer)

### Installation Steps

1. **Clone the repository** (if you haven't already):
   ```bash
   git clone <repository_url>
   cd backend
   ```

2. **Create a Virtual Environment**:
   ```bash
   python -m venv venv
   ```

3. **Activate the Virtual Environment**:
   - On Windows:
     ```cmd
     venv\Scripts\activate
     ```
   - On macOS/Linux:
     ```bash
     source venv/bin/activate
     ```

4. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

5. **Apply Database Migrations**:
   ```bash
   python manage.py migrate
   ```

6. **Generate Dummy Data** (Optional, for testing purposes):
   ```bash
   python generate_dummy.py
   ```

7. **Create a Superuser** (to access the Django admin panel):
   ```bash
   python manage.py createsuperuser
   ```

8. **Run the Development Server**:
   ```bash
   python manage.py runserver
   ```
   The API will be accessible at `http://127.0.0.1:8000/`.

## Deployment Steps

To deploy this Django application to a production environment (like AWS, DigitalOcean, Heroku, or a VPS), follow these general steps:

### 1. Preparation
- Ensure all your code is pushed to your version control system.
- Change `DEBUG = True` to `DEBUG = False` in `core_project/settings.py`.
- Add your production domain/IP to `ALLOWED_HOSTS` in `core_project/settings.py`.
- Set up a production database (e.g., PostgreSQL). Update the `DATABASES` configuration in `settings.py` to point to it.
- Set a strong, secret `SECRET_KEY` in your environment variables.

### 2. Server Setup (e.g., Ubuntu VPS)
- Install Python, pip, Nginx, and a database server (like PostgreSQL).
- Clone your repository to the server.
- Set up a virtual environment and install dependencies (`pip install -r requirements.txt`). You will also need to install a WSGI server like `gunicorn` (`pip install gunicorn`) and database adapters (e.g., `psycopg2` for PostgreSQL).

### 3. Database and Static Files
- Apply migrations to the production database:
  ```bash
  python manage.py migrate
  ```
- Collect static files (ensure `STATIC_ROOT` is defined in `settings.py`):
  ```bash
  python manage.py collectstatic
  ```

### 4. Running the Application with Gunicorn
- Test Gunicorn to ensure it runs correctly:
  ```bash
  gunicorn --bind 0.0.0.0:8000 core_project.wsgi
  ```
- Create a `systemd` service file for Gunicorn to manage the process and start it automatically on boot.

### 5. Configuring Nginx
- Create an Nginx server block (virtual host) to act as a reverse proxy. It should pass requests to Gunicorn and serve static/media files directly.
- Restart Nginx to apply the configuration.

### 6. Securing with HTTPS (Recommended)
- Use Let's Encrypt and Certbot to obtain a free SSL certificate and configure Nginx to serve your application over HTTPS.

## Authentication
The API uses JWT for authentication. You will typically need to obtain a token via a login endpoint and include it in the `Authorization` header for protected routes:
```
Authorization: Bearer <your_access_token>
```
