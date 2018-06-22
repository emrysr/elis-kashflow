# elis-kashflow
## automated invoice entry to kashflow
python flask application running on nginx via uwsgi on a single docker container. no database

![Screenshot 1](/static/img/screenshot1.png?raw=true "22/06/2018")

this currently only works if you've got a kashflow.com account. other bookeeping services could be added if their apis are available.
https://www.kashflow.com/

a pdf is sent to rossum's elis document scanning service. the relevant information scraped from the document is then submitted into kashflow's api as a purchase
https://rossum.ai/elis

## docker
uses this docker image to base the build on:
https://hub.docker.com/r/tiangolo/uwsgi-nginx-flask/
**loads of work done by [@tiangolo](https://github.com/tiangolo/uwsgi-nginx-flask-docker) to get this to work so well**. thanks

## frontend
bulma is used to style the html. vuejs is used to keep state in the browser.

the frontend scripts dont access the 3rd party apis directly. the requests are proxied via the running python script.
## backend
flask (and jinja templates) are used to return json,files or html to the browser via these routes
- /
- /login
- /logout
- /static/[filename]
- /invoices
- /uploads/[filename]
- /shield/[text]/[text]/[colour]
- /test
**further documentation is required for the route parameters and return data**
## python3 script auto run
the Dockerfile will build an image with the required settings. when ran the resulting container will run main.py as it starts. when you first build the docker image all the python includes should also be installed via pip - see app/requirements.txt 
see [@tiangolo](https://github.com/tiangolo/uwsgi-nginx-flask-docker)'s docs for configuration options
```pip install --trusted-host pypi.python.org -r requirements.txt```
## port mapping
localhost:8080 is mapped to container:80

## create image from docker file
go to directory with Dockerfile. run:
``` docker build -t megni/elis-kashflow . ```

## create container
this is not for a packaged project. just a single script running stand alone.

*remove the FLASK_DEBUG flag in production*
``` docker run -d --name elis-kashflow -p 8080:80 -v $(pwd)/app:/app -e FLASK_APP=main.py -e FLASK_DEBUG=1 megni/elis-kashflow flask run --host=0.0.0.0 --port=80 ```