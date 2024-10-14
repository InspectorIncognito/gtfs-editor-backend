# Use node 14.17.3 if RUN npm install have problems
FROM node:14.17.3-alpine as build-stage
WORKDIR /app
RUN apk update && apk upgrade && \
    apk add --no-cache git


RUN git clone https://github.com/InspectorIncognito/gtfs-editor-frontend.git && \
    cd gtfs-editor-frontend && git checkout dev && cd .. && \
    mv gtfs-editor-frontend/* . && \
    rm -r gtfs-editor-frontend
RUN sed -i 's|git+ssh://git@github.com|https://github.com|g' package-lock.json
RUN npm install
RUN touch '.env.production' && \
  echo 'NODE_ENV=production' >> '.env.production' && \
  echo 'VUE_APP_MAPBOX_TOKEN=pk.eyJ1Ijoiam9yb21lcm8iLCJhIjoiY2toa2t2NnBjMDJkYTJzcXQyZThhZTNyNSJ9.Wx6qT7xWJ-hhKHyLMNbnAQ' >> '.env.production' && \
  echo 'VUE_APP_BASE_URL=http://localhost:8000/backend' >> '.env.production' && \
  echo 'VUE_APP_I18N_LOCALE=es' >> '.env.production' && \
  echo 'VUE_APP_I18N_FALLBACK_LOCALE=en' >> '.env.production' && \
  echo 'VUE_APP_I18N_SUPPORTED_LOCALE=en,es' >> '.env.production'
RUN npm run build

FROM nginx:1.17 as prod

COPY --from=build-stage /app/dist /usr/share/nginx/html
COPY ./docker/nginx/config/local.conf /etc/nginx/conf.d/local.conf
COPY ./docker/nginx/config/status.conf /etc/nginx/conf.d/status.conf
COPY ./docker/nginx/nginx_entrypoint.sh ./entrypoint.sh

RUN rm /etc/nginx/conf.d/default.conf

ENTRYPOINT ["/bin/bash", "entrypoint.sh"]

FROM nginx:1.17 as dev

COPY --from=build-stage /app/dist /usr/share/nginx/html
COPY ./docker/nginx/config/dev.conf /etc/nginx/conf.d/local.conf
COPY ./docker/nginx/config/status.conf /etc/nginx/conf.d/status.conf
COPY ./docker/nginx/nginx_entrypoint.sh ./entrypoint.sh

RUN rm /etc/nginx/conf.d/default.conf

ENTRYPOINT ["/bin/bash", "entrypoint.sh"]

FROM nginx:1.17 as certbot

COPY ./docker/nginx/config/certbot.conf /etc/nginx/conf.d/local.conf
COPY ./docker/nginx/nginx_entrypoint.sh ./entrypoint.sh

RUN rm /etc/nginx/conf.d/default.conf

ENTRYPOINT ["/bin/bash", "entrypoint.sh"]