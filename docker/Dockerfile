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

RUN set -x \
    && ARCH=$(uname -m) \
    && echo "Architecture: $ARCH" \
    && if [ "$ARCH" = "aarch64" ]; then JAVA_ARCH="aarch64"; else JAVA_ARCH="x64"; fi \
    && echo "Java Architecture: $JAVA_ARCH" \
    && OS_TYPE=$(if [ "${JAVA_ARCH}" = "aarch64" ]; then echo "rpm"; elif [ "${JAVA_ARCH}" = "x64" ]; then echo "deb"; else echo "unknown"; fi) \
    && echo "OS Type: $OS_TYPE" \
    && JAVA_URL="https://download.oracle.com/java/21/latest/jdk-21_linux-${JAVA_ARCH}_bin.${OS_TYPE}" \
    && echo "Java URL: $JAVA_URL" \
    && wget --no-check-certificate -c --header "Cookie: oraclelicense=accept-securebackup-cookie" -O jdk.${OS_TYPE} $JAVA_URL \
    && ls -l jdk.${OS_TYPE} \
    && case "$OS_TYPE" in \
         deb)     dpkg -i jdk.${OS_TYPE} ;; \
         rpm)     apt-get update && apt-get install alient && alien --scripts --to-deb jdk.${OS_TYPE} && dpkg -i jdk*.deb ;; \
         *)       echo "Unsupported package type" && exit 1 ;; \
       esac \
    && rm jdk.${OS_TYPE} \
    && echo "Java installation complete" \
    && java -version

WORKDIR /app
RUN mkdir ./static && \
    mkdir ./media

# copy project files on /app folder
COPY . .

EXPOSE 8000
ENTRYPOINT ["/bin/sh", "docker/entrypoint.sh"]