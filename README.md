# AASP
An app to classify speech prosody types

# Run
Download and extract this repository.

## Using Docker
Using Docker is the easiest way to run this application locally. This will work on Linux, Mac OS, and Windows 10 Professional. Warning: Docker and the images created for this application will take several GBs of disk space.

First, download and install [Docker Desktop](https://docs.docker.com/desktop/). When Docker is running, you can use a command line utilitiy (Terminal on Mac, CMD.exe on Windows) to change to the directory where you extracted this repository:
```
cd /path/to/directory
```

Then you can start the Docker containers by running:
```
docker-compose up
```
This will take a long time to start up the first time, but restarting at a later time should be fast.

Stop the application with crtl-C. If you added items to the AASP database, these will be retained and available on your next start of the application.

If there is a new version of this software, download and extract to the same location again, then run:
```
docker-compose up --build
```

## Without Docker
To start the app, create a virtual environment, install requirements and initialize the database:
```
pip install -r requirements.txt
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
```

To start the application on `localhost:8400`, run:
```
python manage.py runserver --port 8400
```