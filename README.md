# GTFS EDITOR

```
Some changes were made in the way the steps were Some changes were made in the way the project documentation. Some sections
were added and others were modified. Also, some typos were fixed. The
following sections were added:

- Table of Contents
- Requirements
- Installations
- Configuration
- Running the project

Also, it was added a section where explains how to run the project when cloning
it the repository in Windows. This is because the entrypoints.sh files have
to be converted to LF line endings. This is not necessary in Linux or Mac.

There were some typos in the README.md file that were fixed. Also, some
sections were modified to make them more clear.

Last version of the README.md did not have sections were the user could
find more information about the installation process. Some tools were also
added to the list of requirements to make the installation process easier.
```

This project is a web application to create, edit and publish static GTFS.

In the current document you will find the necessary information to
install and run the project in a local environment.

## Table of Contents

- [Requirements](#requirements)
- [Installations](#installations)
- [Configuration](#configuration)
- [Running the project](#running-the-project)
- [Running the containers](#running-the-containers)

## Requirements

You need to have the following tools installed in your machine:

- Python 3
- pip package manager
- virtualenv package
- Docker
- Docker Compose
- Docker Desktop

In this repository you will find a file called `requirements.txt` that
contains all the dependencies that you need to install in order to run the
project. 

## Installations

There are some steps that are meant to get done in order to instantiate the
project in a local machine. These will be covered in the following sections.

In this section you will find the steps to install the project in a local
environment. 

### Installing Python 3

First of all, you need to install Python 3. You can download it
[here](https://www.python.org/downloads/).

### Installing pip

After installing Python 3, you need to install pip. Pip is the package
manager for Python and, usually, it comes installed with Python. You can
check if you have it installed by running:

```
pip --version
```

If you don't have it installed, you can install it following the
[instructions](https://pip.pypa.io/en/stable/installing/).

You can learn more about pip [here](https://pip.pypa.io/en/stable/user_guide/).

### Installing virtualenv

It is highly recommended to use a virtual environment to keep dependencies
required by different projects separate by creating isolated python virtual
environments for them.

In order to create a Python virtual environment you need to install it.
You can install it using pip:

```
pip install virtualenv
```

After installing it, you can create a virtual environment:

```
virtualenv venv
```

Make sure that you are in the root directory of the project when you create
the virtual environment.

If you are using Python 2.7 by default is needed to define a Python3 flag:

```
virtualenv -p python3 venv
```

Then you need to activate it for the current shell session:

```
source venv/bin/activate
```

After activating the virtual environment, you can install the dependencies.
You can do it using pip:

```
pip install -r requirements.txt
```

You can learn more about virtual environments
[here](https://docs.python.org/3/tutorial/venv.html).

### Installing Docker

Docker is a tool that allows you to create, deploy and run applications by
using containers. These are isolated environments that contain everything
that an application needs to run. You can learn more about Docker
[here](https://www.docker.com/why-docker).

After installing Docker, you need to create a Docker account. You can create
it [here](https://hub.docker.com/signup).

You can download it [here](https://docs.docker.com/get-docker/).

### Installing Docker Compose

Docker Compose is a tool for defining and running multi-container Docker
applications. You can learn more about Docker Compose
[here](https://docs.docker.com/compose/).

You can download it [here](https://docs.docker.com/compose/install/).

### Installing Docker Desktop

Docker Desktop is a handy tool that allows you to manage Docker containers
and images. You can download it [here](https://www.docker.com/products/docker-desktop).

### Installing Docker Compose

Docker Compose is a tool for defining and running multi-container Docker
applications. You can learn more about Docker Compose [here](https://docs.docker.com/compose/).

You can download it [here](https://docs.docker.com/compose/install/). The
installation steps depend on your operating system.

## Configuration

In this section you will find the steps to configure the project in a local
environment. This will be made using Docker and Docker Compose.

### Setting the environment variables

You will need to create a `.env` file for initializing the project. This
file contains the environment variables for initializing the project in a
local environment.

This file allows you to put your environment variables inside a file. This
is useful because you can keep your environment variables in a single file
and will not have to worry about setting them up every time you run the
project. Also, you will not have to worry about storing sensitive data in
a public repository.

The `.env` file is not included in the repository because it has to be
set up for each environment. You can find a template of this file below:

You need to define the environment keys creating an .env file at root path:

```
SECRET_KEY=key

DEBUG=True

ALLOWED_HOSTS=127.0.0.1,localhost

DB_NAME=db_name
DB_USER=db_user_name
DB_PASS=db_user_pass
DB_HOST=localhost
DB_PORT=5432

REDIS_LOCATION=redis://127.0.0.1:6379 

LOG_PATH=./file.log

CORS_ALLOWED_ORIGINS=http://localhost:8080 # needed in dev mode

```

You will need to replace the values of the variables with the ones that you
need for your local environment.

You can find keys for the `SECRET_KEY` variable 
[here](https://miniwebtool.com/es/django-secret-key-generator/).

### About entrypoints.sh files

The `entrypoints.sh` files are used to run the project in a local environment.
They are used to run the migrations and to start the server.

If you are using Windows, you will need to change the line endings of the
entrypoints.sh files.

In PyCharm or any other IDE, you can change the line endings of the files
to `LF` instead of `CRLF`. This is done by clicking on the `CRLF` button in
the bottom right corner of the editor and selecting `LF`. You can learn more
about this [here for PyCharm](https://www.jetbrains.com/help/pycharm/configuring-line-endings-and-line-separators.html) 
or [here for VSCode](https://code.visualstudio.com/docs/getstarted/settings#_line-ending).

You can also change the line endings using the following command:

```
dos2unix <file>
```

Also, you can get this done by converting the line endings of the files using
a online tool, like [this one](https://www.browserling.com/tools/dos-to-unix).
But this is not recommended because you will have to do it every time you
clone the repository.

## Running the project

Before running the project, you need to make sure that you have the 
environment variables set up. You can find go back to the previous section
[here](#setting-the-environment-variables).

It is important to know learn how Docker works before running the project.
In continuation, you will find a brief explanation about Docker and Docker
Compose.

### About Docker

Docker is a tool that allows you to create, deploy and run applications by
using containers. These are isolated environments that contain everything
that an application needs to run.

Images are templates for creating these containers. You can think of them as
virtual machines. You can create containers from images. These containers
are instances of the images and are isolated from the rest of the system.

Composing is a process that allows you to run multiple containers as a
single service. We will be using this feature to run the project.

You can learn more about Docker [here](https://docs.docker.com/get-started/).

### Running the containers

After setting up the environment variables, you can build the images and
run the containers. You can do it using by building the Docker files and
running the Docker Compose file.

You can build the Docker files using the following command:

```
docker build -f docker\Dockerfile -t gtfseditor .
```

Also, for ECR service we need build two images: the project's and nginx
server, for each of two we have to do the following process:

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

Finally, you can run the Docker Compose file using the following command:

```
# Build docker-compose
docker-compose -p gtfs-editor -f docker\docker-compose.yml build
```

Then, you can run the project using the following command:

```
# Run project:
docker-compose -p gtfs-editor -f docker\docker-compose.yml up
```

For stopping the process, you can use this other command:

```
# Stop execution:
docker-compose -p gtfs-editor -f docker\docker-compose.yml down
```

Sometimes, you will want to update the frontend code without upgrading
everything else, so in these cases you should run the following command:

```
docker-compose -p gtfs-editor -f docker\docker-compose.yml build --no-cache nginx
```

After running the project, you can manage it using the Docker Desktop tool. For
more information about this, you can check the [documentation](https://docs.docker.com/desktop/).