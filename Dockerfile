FROM python:3.6

ENV PYTHONUNBUFFERED 1

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        postgresql-client \
    && rm -rf /var/lib/apt/lists/*

RUN mkdir /code
WORKDIR /code
COPY requirements.txt /code/
RUN pip install -r requirements.txt
# RUN python manage.py migrate
COPY . /code/

EXPOSE 8000
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]