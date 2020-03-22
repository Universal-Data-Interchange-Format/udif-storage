FROM python:3

LABEL author="Robert Howe <rc@rchowe.com>"

RUN apt-get update -y && \
    apt-get install -y libpq-dev

COPY ./requirements.txt /app/requirements.txt

WORKDIR /app

RUN pip install -r requirements.txt

COPY . /app

EXPOSE 5000

ENTRYPOINT ["python"]
CMD ["application.py"]