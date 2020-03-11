FROM python:3.6-alpine

ENV PYTHONUNBUFFERED 1

RUN apk update \
    && apk add --no-cache openjdk11

RUN apk add --no-cache R
RUN -e "install.packages('textgRid', repos = 'http://cran.us.r-project.org')"

RUN mkdir /code
WORKDIR /code
COPY requirements.txt /code/
RUN pip install -r requirements.txt
# RUN python manage.py migrate
COPY . /code/

EXPOSE 8000
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]