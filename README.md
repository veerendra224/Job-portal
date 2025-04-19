This is the web application of a Job Portal web application built using Flask. It supports user registration, login, job posting/searching, password reset, and more. It’s designed for three types of users: Job Seekers, Employers, and Admins.

⚙️ How to Set It Up and Run
✅ Prerequisites
Python 3.8+

PostgreSQL installed and running

pip or pipenv for dependency management

🔧 Setup Instructions
1. Clone the Repository
cd job-portal-flask
2. Set Up a Virtual Environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
3. Install Dependencies
pip install -r requirements.txt
4. Configure Environment Variables
Create a .env file in the project root and add:

env
SECRET_KEY=your-secret-key
MAIL_SERVER=smtp.googlemail.com
MAIL_PORT=587
MAIL_USE_TLS=1
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-email-password
These are loaded by config.py using python-dotenv.

5. Update Your Database URI
In config.py, set your PostgreSQL credentials:

SQLALCHEMY_DATABASE_URI = 'postgresql+psycopg2://username:password@localhost:5432/job_portal'
6. Initialize the Database
python init_db.py
This will create all tables defined in your models.

7. Run the App
python run.py
Visit the app in your browser at http://127.0.0.1:5000

✅ Available Features
Register/Login with email and password

Different user roles: Job Seeker, Employer

Post and search for jobs

Password reset via email

Form validation and error handling

Extensible with models, routes, and templates
