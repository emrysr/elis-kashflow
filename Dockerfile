FROM tiangolo/uwsgi-nginx-flask:python3.6
ENV LISTEN_PORT 80
ENV STATIC_INDEX 1
ENV NGINX_MAX_UPLOAD 4m
EXPOSE 8080
COPY ./app /app
# Install any needed packages specified in requirements.txt
RUN pip install --trusted-host pypi.python.org -r requirements.txt
