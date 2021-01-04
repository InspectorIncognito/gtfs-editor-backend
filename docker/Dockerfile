FROM python:3.7.7-alpine3.11 as base

FROM base as builder

RUN mkdir /install
RUN apk add postgresql-dev=9.6.10-r0 --repository=http://dl-cdn.alpinelinux.org/alpine/v3.5/main
RUN /bin/sh -c 'apk update && apk add --no-cache gcc musl-dev geos-dev'
COPY requirements.txt /install/requirements.txt
RUN /bin/sh -c 'pip3 install --no-cache-dir --upgrade pip'
RUN /bin/sh -c 'pip3 install --no-cache-dir --no-warn-script-location --prefix /install -r /install/requirements.txt'

FROM base

# Prevents Python from writing pyc files to disc
ENV PYTHONDONTWRITEBYTECODE 1
# Prevents Python from buffering stdout and stderr
ENV PYTHONUNBUFFERED 1

COPY --from=builder /install /usr/local

RUN /bin/sh -c 'apk update && apk add --no-cache openjdk11 postgresql-dev geos'

WORKDIR /app
RUN mkdir ./static && \
    mkdir ./media

# copy project files on /app folder
COPY . .

EXPOSE 8000
ENTRYPOINT ["/bin/sh", "docker/entrypoint.sh"]