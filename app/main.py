import json, re, os, requests
import datetime, dateutil.parser, humanize
from flask import *
from flask_login import LoginManager, UserMixin, login_required, login_user, logout_user
from dotenv import load_dotenv
from werkzeug.utils import secure_filename

# from urllib import request

# create flask app
app = Flask(__name__)

# manage user sessions
sess = Session()
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# load .env settings from app/.env
APP_ROOT = os.path.join(os.path.dirname(__file__))
dotenv_path = os.path.join(APP_ROOT, '.env')
load_dotenv(dotenv_path)
app.config['KASHFLOW_CONSUMER_KEY'] = os.getenv('KASHFLOW_CONSUMER_KEY')
app.config['ROSSUM_CONSUMER_KEY'] = os.getenv('ROSSUM_CONSUMER_KEY')

# session keys
app.config['APP_KEY'] = os.getenv('APP_SECRET_KEY')

#gettext addon
# translations = get_gettext_translations()
# env = Environment(extensions=['jinja2.ext.i18n'])
# env.install_gettext_translations(translations)


#file uploads
app.config['UPLOAD_FOLDER'] = os.path.join(APP_ROOT, 'uploads')
app.config['ALLOWED_EXTENSIONS'] = set(['pdf', 'png', 'jpg', 'jpeg'])

# routes
@app.route("/")
def main():
    invoices = getInvoices()
    messages = {
        'title': 'Add New',
        'select file': 'Choose a file…',
        'upload': 'Upload',
        'success': 'File Uploaded',
        'error': 'Error',
        'loading': "Uploading"
    }
    return render_template('index.html', invoices=invoices, messages=messages)

@app.route("/test", methods=['POST'])
def test():
    return jsonify(request.files)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

@app.route("/invoices", methods=['GET','POST'])
def invoices():
    invoices = getInvoices()
    if request.method == 'POST':
        #send file to elis server and send back partial response to client

        #on response from elis check cashflow to see if there are any matching purchase orders created

        # check if the post request has the file part
        if 'file' not in request.files:
            response = 'file not in files'

        file = request.files['file']
        if file.filename == '':
            response = 'no selected file'
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            fileurl = url_for('uploaded_file',filename=filename)
            file.save(filepath)

            response = {'data':({'filename':filename,'path':filepath, 'url':fileurl}),'meta':{'title':'add Invoice','status': 'OK'}}
            # return jsonify(response)
            #curl -H "Authorization: secret_key iMfLI3BmbngtHYvYGMUs8LvGn84nJZEmegcRpggG5gRy3yRZl1VPYtozkLxmhNWJ" 
            # -X POST -F file=@upload.pdf 
            rossum_url = 'https://all.rir.rossum.ai/document'
            files = {'file': open(filepath,'rb')}
            values = {'DB': 'photcat', 'OUT': 'csv', 'SHORT': 'short'}
            headers = {'Authorization': 'secret_key '+app.config['ROSSUM_CONSUMER_KEY']}
            r = requests.post(rossum_url, files=files, headers=headers)

            if r.status_code == requests.codes.ok: 
                response = {'data':(),'meta':{'title':'add Invoice','status': 'OK','status_code':r.status_code}}
            else:
                response = {'data':(),'meta':{'title':'add Invoice','status': 'Error','status_code':r.status_code,'requested':rossum_url,'headers':headers}}


    else:
        response = {'data':invoices,'meta':{'title':'get Invoices','raw_file':fileurl}}

    return jsonify(response)


@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        login_user(user)

        next = flask.request.args.get('next')
        if not is_safe_url(next):
            return flask.abort(400)

        return flask.redirect(next or flask.url_for('main'))
        return flask.render_template('login.html', form=form)

@app.route("/logout")
def logout():
    logout_user()
    return redirect(somewhere)

# return svg with left & right text and background colour of colour
@app.route("/shileld/<left>/<right>", defaults={'colour':'ff69b4','url':False})
@app.route("/shileld/<left>/<right>/<colour>", defaults={'url':False})
def shield(left,right,colour,url):
    svg = """<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="90" height="20"><g shape-rendering="crispEdges"><path fill="#555" d="M0 0h45v20H0z"/><path fill="{colour}" d="M45 0h45v20H45z"/></g><g fill="#fff" text-anchor="middle" font-family="DejaVu Sans,Verdana,Geneva,sans-serif" font-size="110"><text x="235" y="140" transform="scale(.1)" textLength="350">{left}</text><text x="665" y="140" transform="scale(.1)" textLength="350">{right}</text></g>{openlink}<path fill="rgba(0,0,0,0)" d="M0 0h45v20H0z"/>{closelink} {openlink}<path fill="rgba(0,0,0,0)" d="M45 0h45v20H45z"/>{closelink}
</svg>
    """.format(
    left = left,
    right = right,
    openlink = '<a target="_blank" xlink:href="%(url)">' if url else '',
    closelink = '</a>' if url else '',
    colour = '#'+colour if re.search(r'^(?:[0-9a-fA-F]{1,2}){3}$', colour) else colour)
    return Response(svg, mimetype='image/svg+xml')


# user managment

@login_manager.unauthorized_handler
def unauthorized():
    # do stuff
    return 'a response'

@login_manager.request_loader
def load_user_from_request(request):

    # first, try to login using the api_key url arg
    api_key = request.args.get('api_key')
    if api_key:
        user = User.query.filter_by(api_key=api_key).first()
        if user:
            return user

    # next, try to login using Basic Auth
    api_key = request.headers.get('Authorization')
    if api_key:
        api_key = api_key.replace('Basic ', '', 1)
        try:
            api_key = base64.b64decode(api_key)
        except TypeError:
            pass
        user = User.query.filter_by(api_key=api_key).first()
        if user:
            return user

    # finally, return None if both methods did not login the user
    return None


# static files

# Everything not declared before (not a Flask route / API endpoint)...
@app.route('/<path:path>')
def route_frontend(path):
    # ...could be a static file needed by the front end that
    # doesn't use the `static` path (like in `<script src="bundle.js">`)
    file_path = os.path.join(app.static_folder, path)
    if os.path.isfile(file_path):
        return send_file(file_path)
    # ...or should be handled by the SPA's "router" in front end
    else:
        index_path = os.path.join(app.static_folder, 'index.html')
        return send_file(index_path)



# properties
@property
def serialize(self):
    #return object as json
    return {
        'title' : self.name,
        'url' : self.url,
        'status' : self.status,
        'id' : self.id
    }


# methods
def getInvoices():
    # invoices = {
    #     'title' : 'this is one',
    #     'url' : 'https://url.com',
    #     'status' : 'success',
    #     'elis_id' : 'ab223asavsdfawcassdd',
    #     'kashflow_id' : 'ab223asavsdfawcassdd'
    # }
    elis = [
        {'id':'9pdijf9s', 'title':'val1', 'url':'val2', 'date':'2018-06-12','status':1,'state':'OK','ready':True,'sent':False,'sentdate':False},
        {'id':'0987yhj', 'title':'val3', 'url':'val4', 'date':'2018-06-11','status':1,'state':'OK','ready':True,'sent':False,'sentdate':False},
        {'id':'s8sfjosd', 'title':'val4', 'url':'val2', 'date':'2018-06-10','status':0,'state':'processing','ready':False,'sent':False,'sentdate':False},
        {'id':'opia9011', 'title':'val9', 'url':'val1', 'date':'2018-06-09','status':2,'state':'sent','ready':True,'sent':True,'sentdate':'2018-06-09'}
    ]
    kashflow = [
        {'id':'lksdislsdlfms', 'custom_field':'opia9011'}
    ]
    invoices = []
    for invoice in elis:
        for item in kashflow:
            invoice['kashflowid'] = item['id'] if item['custom_field'] == invoice['id'] else ''
        invoice['elis_id'] = invoice['id']
        del invoice['id'] 
        invoices.append(invoice)

    return invoices
    # for invoice in data:
    #     invoices.append({
    #         "uploaddate": invoice.date,
    #         "id": invoice.id,
    #         "ready": invoice.state == 'OK',
    #         "sent": False,
    #         "sentdate": False,
    #         "state": invoice.state,
    #         "status": invoice.status,
    #         "title": invoice.title,
    #         "url": invoice.url
    #     })

    # return invoices


# template filters
@app.template_filter('strftime')
def _jinja2_filter_datetime(date, fmt=None):
    date = dateutil.parser.parse(date)
    native = date.replace(tzinfo=None)
    format=fmt if fmt else '%b %d, %Y'
    return native.strftime(format)

@app.template_filter('timesince')
def _jinja2_filter_datetime(strdate, fmt=None):
    date = dateutil.parser.parse(strdate)
    return humanize.naturaltime(datetime.datetime.now()-date)


# host the app
if __name__ == "__main__":
    app.secret_key = app.config['APP_KEY']
    app.config['SESSION_TYPE'] = 'filesystem'

    sess.init_app(app)

    app.debug = True
    app.host = '0.0.0.0'
    app.port = 80

    app.run()
