FROM python:3.9

RUN apt-get update

RUN apt-get install -y openjdk-17-jre

RUN apt-get -y install r-base r-base-dev
RUN rm -rf /var/lib/apt/lists/*

RUN R -e "install.packages('lattice', repos='http://cran.us.r-project.org')"
RUN R -e "install.packages('Matrix', repos='http://cran.us.r-project.org')"
RUN R -e "install.packages('ggplot2', repos='http://cran.us.r-project.org')"
RUN R -e "install.packages('https://cran.r-project.org/src/contrib/Archive/fda/fda_2.4.0.tar.gz', dependencies=TRUE, repos = NULL, type='source')"

ENV PYTHONUNBUFFERED 1
WORKDIR /code
COPY requirements.txt /code/

RUN pip install -r requirements.txt
RUN mkdir /code/staticfiles