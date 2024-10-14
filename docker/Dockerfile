FROM python:3.11-slim-buster AS base

FROM base AS builder

RUN mkdir /install
RUN apt-get update &&  \
    apt-get upgrade -y
COPY requirements.txt /install/requirements.txt
RUN pip3 install --no-cache-dir --upgrade pip && \
    pip3 install --no-warn-script-location --no-cache-dir --prefix /install -r /install/requirements.txt

FROM base

# Prevents Python from writing pyc files to disc
ENV PYTHONDONTWRITEBYTECODE=1
# Prevents Python from buffering stdout and stderr
ENV PYTHONUNBUFFERED=1

COPY --from=builder /install /usr/local

RUN apt-get update &&  \
    apt-get upgrade -y &&  \
    apt-get install -y netcat gettext wget

RUN apt-get update &&  \
    apt-get upgrade -y && \
    apt-get install -y netcat default-jre

WORKDIR /app
RUN mkdir ./static && \
    mkdir ./media

# copy project files on /app folder
COPY . .

EXPOSE 8000
ENTRYPOINT ["/bin/sh", "docker/entrypoint.sh"]