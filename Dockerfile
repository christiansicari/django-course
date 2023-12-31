FROM python:3.10-alpine
LABEL maintainer="christiansicari"
ENV PYTHONUNBUFFERED=1
COPY ./requirements.txt /tmp/requirements.txt
COPY ./requirements.dev.txt /tmp/requirements.dev.txt
COPY ./scripts /scripts
COPY ./app /app
WORKDIR /app
EXPOSE 8000
ARG DEV=false
RUN pip install --upgrade pip && \
    apk add --update --no-cache postgresql-client jpeg-dev && \
    apk add --update --no-cache --virtual .tmp-build-deps \
    build-base postgresql-dev musl-dev zlib zlib-dev linux-headers && \
    pip install -r /tmp/requirements.txt && \
    adduser --disabled-password --no-create-home django-user && \
    mkdir -p /vol/web/media && mkdir /vol/web/static && \
    chown -R django-user:django-user /vol && \
    chmod -R 755 /vol && \
    chmod -R +x /scripts && \
    if [ $DEV = "true" ]; \
         then pip install -r /tmp/requirements.dev.txt; \
    fi && \
    rm -rf /tmp && \
    apk del .tmp-build-deps

USER django-user

ENV PATH="-/scripts:/py/bin:$PATH"
CMD [ "/scripts/run.sh" ]