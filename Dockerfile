FROM python:3.6
ENV PYTHONUNBUFFERED 1

RUN apt update && dpkg --configure -a
RUN apt -y install openjdk-11-jdk

RUN apt -y install r-base r-base-dev
RUN R -e "install.packages('lattice', repos='http://cran.us.r-project.org')"
RUN R -e "install.packages('Matrix', repos='http://cran.us.r-project.org')"
RUN R -e "install.packages('https://cran.r-project.org/src/contrib/Archive/fda/fda_2.4.0.tar.gz', dependencies=TRUE, repos = NULL, type='source')"

# # build dependencies for psycopg2
# RUN apk add --virtual .build-deps gcc python3-dev musl-dev postgresql-dev
# # runtime dependency of psycopg2
# RUN apk add --no-cache libpq

RUN mkdir /code
WORKDIR /code
COPY requirements.txt /code/
RUN pip install -r requirements.txt
COPY . /code/
RUN python manage.py migrate

EXPOSE 8000
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]