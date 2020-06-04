# if image is running on aws environment (fargate)
if [ -n "$ECS_CONTAINER_METADATA_URI_V4" ];
then
  sed -i 's/server web:8000/server 127.0.0.1:8000/g' /etc/nginx/conf.d/local.conf
fi

nginx -g "daemon off;"