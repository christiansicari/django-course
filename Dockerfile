FROM python:3.10
LABEL maintainer="christiansicari"
ENV PYTHONUNBUFFERED=1
COPY ./requirements.txt /tmp/requirements.txt
COPY ./requirements.dev.txt /tmp/requirements.dev.txt

COPY ./app /app
WORKDIR /app
EXPOSE 8000
ARG DEV=false
RUN pip3 install -r /tmp/requirements.txt && \
    adduser --disabled-password --no-create-home django-user && \
    if [ $DEV = "true" ]; \
         then pip3 install -r /tmp/requirements.dev.txt; \
    fi && \
    rm -rf /tmp


USER django-user

