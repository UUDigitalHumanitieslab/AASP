FROM python:3.6-alpine

ENV PYTHONUNBUFFERED 1

RUN apk update \
    && apk add --no-cache openjdk11

RUN apk add --no-cache R R-dev libc-dev
RUN R -e "install.packages('lattice', repos='http://cran.us.r-project.org')"
RUN R -e "install.packages('Matrix', repos='http://cran.us.r-project.org')"
RUN R -e "install.packages('https://cran.r-project.org/src/contrib/Archive/fda/fda_2.4.0.tar.gz', dependencies=TRUE, repos = NULL, type='source')"


RUN mkdir /code
WORKDIR /code
COPY requirements.txt /code/
RUN pip install -r requirements.txt
COPY . /code/
RUN python manage.py migrate

EXPOSE 8000
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]