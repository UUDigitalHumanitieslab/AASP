# AASP
An app to classify speech prosody types

# Run
To start the app, create a virtual env, install requiremands and initialize the database:
```
pip install -r requirements.txt
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
```

Then you can run on port localhost:8400
```
python manage.py runserver --port 8400
```

Alternatively, with docker-compose:
```
docker-compose up
```
This will take a long time to start up the first time, but restarting at a later time should be fast.

Stop the application with crtl-C. If you added items to the AASP database, these will be retained and available on your next start of the application.

If there is a new version of this software, you should rebuild by running
```
docker-compose up --build
```