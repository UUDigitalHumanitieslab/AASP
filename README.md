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
Required software:
- [PostgreSQL](https://www.postgresql.org/)
- [R](https://www.r-project.org/)
- [Java](https://openjdk.java.net/)
- [Python 3.6](https://www.python.org/downloads/release/python-3615/)

Create a PostgreSQL database with the name 'aasp', and a user 'aasp'. To do that, open a command line utility, and enter the following, replacing `/path/to/your/pgsql/data` with the path in which your Postgres data is saved. This is typically `/usr/local/pgsql/data` on a Linux machine. On Mac OS, you may have installed Postgres through the [Postgres App](https://postgresapp.com/). In that case, you can open the app, and find out the location in the `Server Settings...` menu.
```
postgres -D /path/to/your/pgsql/data
create user aasp with createdb password 'aasp';
create database aasp;
grant all on database aasp to aasp;
```


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