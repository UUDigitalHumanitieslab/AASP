FROM python:3.6
ENV PYTHONUNBUFFERED 1

RUN apt-get update \
&& apt-get -y install openjdk-11-jdk r-base r-base-dev \
&& rm -rf /var/lib/apt/lists/*
RUN R -e "install.packages('lattice', repos='http://cran.us.r-project.org')"
RUN R -e "install.packages('Matrix', repos='http://cran.us.r-project.org')"
RUN R -e "intall.packages('ggplot2', repos='http://cran.us.r-project.org')"
RUN R -e "install.packages('https://cran.r-project.org/src/contrib/Archive/fda/fda_2.4.0.tar.gz', dependencies=TRUE, repos = NULL, type='source')"

WORKDIR /code
COPY requirements.txt /code/
RUN pip install -r requirements.txt