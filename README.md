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

Alternatively, with docker: run
```
# build from this directory, tag image as aasp
docker build . -t aasp
# run a countainer with name aasp from image aasp:latest
# expose container port 8000 as port 8400 on localhost
docker run --name aasp -p 8400:8000 --rm aasp
```
This will copy over the local database to the container. This may be changed at a later stage.

# Authentication
At the moment, authentication is required. There is a file called `auto_auth.py`, which is work in progress to override authentication (should be registered with middleweare, but doesn't work yet).