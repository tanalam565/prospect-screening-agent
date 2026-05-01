1. Create the project
2. Create the app
3. Register the app 'residents' in the ApplicationScreener/settings.py
4. Define Models - residents/models.py
5. Add app name in 'INSTALLED_APPS' in settings.py
6. Register the models in the admin.py
7. Run migrations:
    python3 manage.py makemigrations (Generates migration files from model changes)
    python3 manage.py migrate (Apply the changes in the database - Do not add data)
8. Create views - residents/views.py
9. Configure URLs - ressidents/urls.py
   Update - ApplicationScreener/urls.py
10. Run the dev server:
    python3 manage.py runserver
11. python3 manage.py createsuperuser