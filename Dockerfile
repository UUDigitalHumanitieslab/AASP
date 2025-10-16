FROM python:3.8-slim-bullseye

RUN apt-get update && apt-get install -y openjdk-17-jre-headless r-base r-base-dev libpq-dev
RUN R -e "install.packages('renv', repos = c(CRAN = 'https://cloud.r-project.org'))"

ENV PYTHONUNBUFFERED 1
WORKDIR /code
COPY renv.lock /code/
RUN R -e "renv::restore()"

COPY requirements.txt /code/
RUN pip install -r requirements.txt
RUN mkdir /code/staticfiles
