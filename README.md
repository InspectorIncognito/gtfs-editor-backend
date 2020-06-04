# GTFS EDITOR 

Web app to create, edit and publish static GTFS

## Dev environment

### Requirements

- Python 3
- Dependencies: requirements.txt

## Configuration

It's recommended to use a virtual environment to keep dependencies required by different projects separate by creating isolated python virtual environments for them.

To create a virtual environment:

```
virtualenv venv
```
If you are using Python 2.7 by default is needed to define a Python3 flag:

```
virtualenv -p python3 venv
```

Activate virtual env and install dependencies:
```
source venv/bin/activate
 
pip install -r requirements.txt
```

### .env file
The env files allow you to put your environment variables inside a file, it is recommended to only have to worry once about the setup and configuration of application and to not store passwords and sensitive data in public repository.
 
You need to define the environment keys creating an .env file at root path:

```
# you can create a key here: https://miniwebtool.com/es/django-secret-key-generator/
SECRET_KEY=key

DEBUG=True

ALLOWED_HOSTS=127.0.0.1,localhost

# Postgres parameters
DB_NAME=db_name
DB_USER=db_user_name
DB_PASS=db_user_pass
DB_HOST=localhost
DB_PORT=5432

# Redis location to connect to it. For instance redis://127.0.0.1:6379 
REDIS_LOCATION=
```

## Test

Run test with:
```
python manage.py test
```

# Docker

## Build image

```
docker build -f docker\Dockerfile -t gtfseditor .
```

### DockerHub

for DockerHub we need build two images, project and nginx server, for each of two we have to do the following process:

```
# build gtfseditor project
docker build -f docker\Dockerfile -t gtfseditor:latest .

# create tag
docker tag gtfseditor:latest sidermit/gtfseditor:latest

# push to aws repository
docker push sidermit/gtfseditor:latest
```

```
# build nginx server
docker build -f docker\nginx\NginxDockerfile -t nginx-gtfseditor:latest .

# create tag
docker tag nginx-gtfseditor:latest sidermit/nginx-gtfseditor:latest

# push to aws repository
docker push sidermit/nginx-gtfseditor:latest
```

## Build and run docker-compose

Build commad:
```
docker-compose -f docker\docker-compose.yml build
```

Run command:
```
docker-compose -f docker\docker-compose.yml up
```

Stop command:
```
docker-compose -f docker\docker-compose.yml down
```
