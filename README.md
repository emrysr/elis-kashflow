# elis-kashflow
## automated invoice entry to kashflow
python flask application running on nginx via uwsgi.

this currently only works if you've got a kashflow.com account. other bookeeping services could be added if their apis are available.
https://www.kashflow.com/

a pdf is sent to rossum's elis document scanning service. the relevant information scraped from the document is then submitted into kashflow's api as a purchase
https://rossum.ai/elis


uses this docker image to base the build on:
https://hub.docker.com/r/tiangolo/uwsgi-nginx-flask/
**loads of work done by (@tiangolo)[https://github.com/tiangolo/uwsgi-nginx-flask-docker] to get this to work so well. thanks

bulma is used to style the html. vuejs is used to keep state in the browser and flask (and jinja templates) is then used to return json data to the browser.

the frontend scripts dont access the 3rd party apis directly. the requests are proxied via the running python script.

## python script auto run
this will run an image in a container and then run the main.py in the container.
## port mapping
localhost:8080 is mapped to container:80

## create image from docker file
go to directory with Dockerfile. run:
``` docker build -t megni/elis-kashflow . ```

## create container
this is not for a packaged project. just a single script running stand alone.
*remove the FLASK_DEBUG flag in production*
``` docker run -d --name elis-kashflow -p 8080:80 -v $(pwd)/app:/app -e FLASK_APP=main.py -e FLASK_DEBUG=1 megni/elis-kashflow flask run --host=0.0.0.0 --port=80 ```