# Transappp GTFS EDITOR

Web app to create, edit, validate and publish static GTFS

## 1. Requirements

- Python 3.11
- Docker
- Dependencies:
    - requirements.txt
    - requirements-dev.txt

## 2. Configuration

It's recommended to use a virtual environment to keep dependencies required by different projects separate by creating
isolated python virtual environments for them.

To create a virtual environment:

```
virtualenv venv
```

If you are using Python 2.7, by default is needed to define a Python3 flag:

```
virtualenv -p python3 venv
```

Activate virtual env and install dependencies:

```
source venv/bin/activate
 
pip install -r requirements.txt
```

### 2.1. `.env` file

The env files allow you to put your environment variables inside a file, it is recommended to only have to worry once
about the setup and configuration of application and to not store passwords and sensitive data in public repository.

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

LOG_PATH=./file.log
# needed in dev mode
CORS_ALLOWED_ORIGINS=http://localhost:8080

# mailgun user to send emails
EMAIL_USER=
EMAIL_PASSWORD=
```

## 3. Run tests in dev environment

Run test with:

```
python manage.py test
```

*: it's crucial to run the django command `python manage.py compilemessages` before test to generate translations used
by the platform.

## 4. Docker

### 4.1. Build image in local

```
docker build -f docker\Dockerfile -t gtfseditor .
```

### 4.2. AWS

for ECR service we need to build two images, project and nginx server, for each of two we have to do the following
process:

```
# build gtfseditor project
docker build -f docker\Dockerfile -t gtfseditor:latest .

# create tag
docker tag gtfseditor:latest 992591977826.dkr.ecr.sa-east-1.amazonaws.com/gtfseditor:latest

# push to aws repository
docker push 992591977826.dkr.ecr.sa-east-1.amazonaws.com/gtfseditor:latest
```

```
# build nginx server
docker build -f docker\nginx\NginxDockerfile -t nginx-gtfseditor:latest .

# create tag
docker tag nginx-gtfseditor:latest 992591977826.dkr.ecr.sa-east-1.amazonaws.com/nginx-gtfseditor:latest

# push to aws repository
docker push 992591977826.dkr.ecr.sa-east-1.amazonaws.com/nginx-gtfseditor:latest
```

### 4.3. Build and run docker-compose

#### 4.3.1. production environment

Build command:

```
docker-compose -p gtfs-editor -f docker\docker-compose.yml build
```

Run command:

```
docker-compose -p gtfs-editor -f docker\docker-compose.yml up -d
```

Stop command:

```
docker-compose -p gtfs-editor -f docker\docker-compose.yml down
```

Sometimes you want to update frontend code without upgrading everything else, so in these cases you should call:

```
docker-compose -p gtfs-editor -f docker\docker-compose.yml build --no-cache nginx
```

#### 4.3.2. development environment

Development environment publishes in the host machine the ports to communicate with database, cache and web server.

Build command:

```
docker-compose -p gtfs-editor -f docker\docker-compose.yml -f docker\docker-compose-dev.yml build
```

Run command:

```
docker-compose -p gtfs-editor -f docker\docker-compose.yml -f docker\docker-compose-dev.yml up -d
```

Stop command:

```
docker-compose -p gtfs-editor -f docker\docker-compose.yml -f docker\docker-compose-dev.yml down
```

Sometimes you want to update frontend code without upgrading everything else, so in these cases you should call:

```
docker-compose -p gtfs-editor -f docker\docker-compose.yml -f docker\docker-compose-dev.yml build --no-cache nginx
```

## 5. Install install GNU gettext toolset

You should only install it if you need to generate .po or .mo files for translation reasons

### 5.1. Windows

1- Go to this link: https://mlocati.github.io/articles/gettext-iconv-windows.html

2- Download the appropriate version (32-bit or 64-bit) of gettext. We recommend the static windows installation file

3- Extract the downloaded ZIP file to a folder of your choice on your computer

4- Add the bin folder to your system's PATH environment variable

5- check if your terminal recognizes the new commands, open a terminal and run the command `msgfmt --version`. If the
command fails, you may need to restart your terminal or the PyCharm instance to apply the changes

### 5.2. Linux & Unix-like

Run the following command on terminal:

```
apt-get update
apt-get install gettext
```

### 5.3. macOS

Installing gettext package on macOS via brew:

```
brew install gettext
```

## 6. Updating or adding new translations

To improve existing translations or add new ones, follow these steps:

1. Ensure the new text strings are wrapped inside the `gettext` or `gettext_lazy` functions.
2. Run the following command to update `.po` files: `python manage.py makemessages -l <language> -i venv3.11/*`
3. Locate the updated `.po` file in the respective app directory where the new text was added. It can be found
   in `app_name/locale/<language>/django.po`
4. Add the necessary translations for the new text strings
5. Commit your changes

### 6.1. Available languages

1. en: English (default)
2. es: Spanish