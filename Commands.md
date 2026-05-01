# Create the environment
pip3 install virtualenv
virtualenv venv
source venv/bin/activate

# Create the project
pip3 install django
django-admin startproject ApplicantScreener

# Create the app
cd ApplicantScreener # Inside the Project
python3 manage.py startapp residents