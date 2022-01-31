# Automatic Annotation of Speech Prosody
An application to annotate speech prosody, especially suited to the Dutch language, using two approaches:
- AuToDI (Automatic ToDI)
- FDA (Functional Discriminative Analysis)

For a description of the system, see Hu (2020).

Hu, N., Janssen, B., Hanssen, J., Gussenhoven, C., & Chen, A. (2020). Automatic Analysis of Speech Prosody in Dutch. In Proc. Interspeech 2020 (pp. 155–159). https://doi.org/10.21437/Interspeech.2020-2142

## Usage
Add a selection of files from your computer to the analysis set. These files should be pairs of .TextGrid and .wav files of the same name. Add a label (called "Speaker name", but it can be any label which helps to distinguish files), and click "Upload".

In the next step, select files for analysis, and whether to apply AuToDI or FDA. After that, you will be asked which tier in the .TextGrid files should be used for analysis.

In the final step, the results of the analysis can be downloaded as a .zip file.

## AuToDI
This part of the code reuses [AuToBI](https://github.com/AndrewRosenberg/AuToBI) (Rosenberg, 2010), a Java application to automatically annotate prosody with ToBI labels. The Java applciation is used for generating descriptors of the frequency development only; custom classifiers were trained for the ToDI annotation system for the Dutch language. These classifiers can be found in `/AuToDI/classifiers`. They are pickled `sklearn` models.

Rosenberg, A. (2010). Autobi-a tool for automatic tobi annotation. In Eleventh Annual Conference of the International Speech Communication Association.

## FDA
This part of the application extracts f0, f1 and f2 from the audio files with the Python wrapper around Praat, Parselmouth. Then it uses R scripts modified from the [FDA R scripts](https://github.com/uasolo/FDA-DH) by Gubian (cf. Gubian, 2014), which fit [B-splines](https://en.wikipedia.org/wiki/B-spline) to the frequency shapes, and list their principal components.

In order to use FDA, you need to specify how many knots (i.e., how many different curves are "attached" to each other) and which smoothing factor lambda should be used.

Gubian, M., Torreira, F., & Boves, L. (2015). Using functional data analysis for investigating multidimensional dynamic phonetic contrasts. Journal of Phonetics, 49, 16-40.

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
