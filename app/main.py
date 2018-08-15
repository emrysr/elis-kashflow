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
app.config['KASHFLOW_API_URL'] = os.getenv('KASHFLOW_API_URL')
app.config['KASHFLOW_API_MEMORABLE_WORD'] = os.getenv('KASHFLOW_API_MEMORABLE_WORD')
app.config['KASHFLOW_API_PASSWORD'] = os.getenv('KASHFLOW_API_PASSWORD')
app.config['KASHFLOW_API_USERNAME'] = os.getenv('KASHFLOW_API_USERNAME')
app.config['KASHFLOW_API_DUMMY_SUPPLIER_CODE'] = os.getenv('KASHFLOW_API_DUMMY_SUPPLIER_CODE')
app.config['ROSSUM_CONSUMER_KEY'] = os.getenv('ROSSUM_CONSUMER_KEY')
app.config['ROSSUM_ENDPOINT'] = os.getenv('ROSSUM_ENDPOINT')

# session keys
app.secret_key = os.getenv('APP_SECRET_KEY')
app.config['SESSION_TYPE'] = 'filesystem'

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



def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']



@app.route("/documents", methods=['POST'])
def documents():
    """send file to elis rossum server and return json response with document id"""
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
        files = {'file': open(filepath,'rb')}
        # values = {'DB': 'photcat', 'OUT': 'csv', 'SHORT': 'short'}
        jsonBody = postRossum(files)
        if r.status_code == requests.codes.ok:
            #@todo: send file and note with the document_id to kashflow as a new purchase under the provider specified in the .env file
            response = {
                'data': {
                    'invoices': [{'id': jsonBody['id']}]
                },
                'meta': {
                    'title':'add Invoice',
                    'status': 'Success',
                    'status_code': r.status_code,
                    'response': jsonBody
                }
            }
        else:
            response = {
                'data': {
                    'invoices': []
                },
                'meta': {
                    'title':'add Invoice',
                    'status': 'Error',
                    'status_code': r.status_code,
                    'response': jsonBody
                }
            }



@app.route("/invoices")
def invoices():
    """ return a json list of invoices """
    response = {'data':getInvoices(),'meta':{'title':'get Invoices'}}
    return jsonify(response)

@app.route('/config')
def config():
    return jsonify({
        'USERNAME':os.getenv('USERNAME'),
        'PASSWORD':os.getenv('PASSWORD'),

        'KASHFLOW_CONSUMER_KEY':os.getenv('KASHFLOW_CONSUMER_KEY'),

        'ROSSUM_CONSUMER_KEY':app.config['ROSSUM_CONSUMER_KEY'],
        'ROSSUM_ENDPOINT':app.config['ROSSUM_ENDPOINT'],
        'APP_KEY':app.config['APP_KEY'],

        'UPLOAD_FOLDER':app.config['UPLOAD_FOLDER'],
        'ALLOWED_EXTENSIONS':', '.join(app.config['ALLOWED_EXTENSIONS']),
    })

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
def getPreviewUrl(id):
    """ return the url that displays the data overlayed over the scan"""
    return 'https://rossum.ai/document/'+id+'?apikey='+app.config['ROSSUM_CONSUMER_KEY']

def getCurrencySymbol(currency,value):
    """ return the value with a symbol if the 3 char currency name is in this list - else return the value and the name """
    if not value: return ''
    currency = currency.upper()
    symbols = {
        'GBP': '£',
        'USD': '$',
        'EUR': '€'
    }
    symbol =  symbols.get(currency, False)
    if not symbol :
        return '{} ({})'.format(value, currency)
    else:
        return '{}{}'.format(symbol, value)
        
def getKashflowTemporaryToken():
    """Gets the JSON response with the temporary token"""
    url = app.config['KASHFLOW_API_URL']+'/sessiontoken'
    headers = {'Content-Type': 'application/json'}
    data = '{{ "Password":"{}", "UserName":"{}" }}'.format(app.config['KASHFLOW_API_PASSWORD'],app.config['KASHFLOW_API_USERNAME'])
    r = requests.post(url, headers=headers, data=data)
    jsonBody = r.json()
    return jsonBody

def getKashflowSessionToken(temp):
    """Gets the session token. Requires that you first run getKashflowTemporaryToken()"""
    url = app.config['KASHFLOW_API_URL']+'/sessiontoken'
    memorableWord = app.config['KASHFLOW_API_MEMORABLE_WORD']

    p1 = temp['MemorableWordList'][0]['Position']
    p2 = temp['MemorableWordList'][1]['Position']
    p3 = temp['MemorableWordList'][2]['Position']

    v1 = memorableWord[p1-1]
    v2 = memorableWord[p2-1]
    v3 = memorableWord[p3-1]

    headers = {'Content-Type': 'application/json'}
    data = '{{"TemporaryToken":"{}","MemorableWordList":[ {{ "Position":{}, "Value":"{}" }}, {{ "Position":{}, "Value":"{}" }}, {{ "Position":{}, "Value":"{}" }}] }}'.format(temp['TemporaryToken'],p1,v1,p2,v2,p3,v3)
    r = requests.put(url, headers=headers, data=data)
    jsonBody = r.json()
    return jsonBody['SessionToken']


def kashflowApiCall(endpoint='',verb='GET', data=''):
    """ perform a http request to app.kashflow.com and return the response as a dict"""
    # put incoming verb into uppercase chars
    verb = verb.upper()

    # get session key if not available
    if not session.get('kashflowToken'):
        tmpToken = getKashflowTemporaryToken()
        session['kashflowToken'] = getKashflowSessionToken(tmpToken)
    
    # add auth header if in session
    headers = {'Content-Type': 'application/json'}
    if session.get('kashflowToken'):
        headers['Authorization'] = 'KfToken {}'.format(session['kashflowToken'])
    
    url = app.config['KASHFLOW_API_URL']+'/{}'.format(endpoint)
    
    if verb == 'POST':
        r = requests.post(url, headers=headers, data=data)
    elif verb == 'PUT':
        r = requests.put(url, headers=headers, data=data)
    elif verb == 'UPDATE':
        r = requests.update(url, headers=headers, data=data)
    elif verb == 'DELETE':
        r = requests.delete(url, headers=headers, data=data)
    else:
        r = requests.get(url, headers=headers)

    jsonBody = r.json()
    return jsonBody

def getKashflow(endpoint):
    """ perform a http GET request to app.kashflow.com and return the response as a dict"""
    return kashflowApiCall(endpoint,'get')

def getPurchases():
    """ return list of purchase objects for the TEMP01 supplier """
    return getKashflow('Purchases?SupplierCode={}'.format(app.config['KASHFLOW_API_DUMMY_SUPPLIER_CODE']))

@app.route('/suppliers')
def getSuppliers():
    """ return json array of kashflow supplier names and ids """ 
    suppliers = []
    for supplier in getKashflow('suppliers')['Data']:
        suppliers.append({
            'Name': supplier['Name'],
            'Code': supplier['Code']
        })
    return jsonify(suppliers)

def getPurchaseDocumentIds():
    """ check all notes for all purchases for the rossum document id"""
    responses = []
    purchases = getPurchases()
    for p in purchases['Data']:
        for note in getKashflow('Purchases/{}/notes'.format(p['Number'])):
            document_ids = []
            # pattern match the rossum elis document id pattern (24 hex chars)
            m = re.search('([0-9a-fA-F]{24})',note['Text'])
            # single note might have multiple ids (shouldn't, but could)
            if m:
                document_ids.append(m.group(0))

            responses.append({
                'id': p['Number'],
                'date': p['IssuedDate'], 
                'note_id': note['Number'], 
                # 'message': note['Text'],
                'document_id': ','.join(document_ids) # join multiples if they exist
            })
    return responses

def getRossum(document_id):
    """ send a http GET request to the rossum.ai server. """
    return callRossumApi('/'+document_id, 'get')

def postRossum(files):
    """ send a http POST reqest to the rossum.ai server (Upload files ***)"""
    return callRossumApi('','post',files)

def callRossumApi(endpoint='',verb='get',files=''):
    """ perform a http request to rossum.ai and return the response as a dict"""
    # put incoming verb into uppercase chars
    verb = verb.upper()
    url = app.config['ROSSUM_ENDPOINT']+endpoint
    headers = {'Authorization': 'secret_key '+app.config['ROSSUM_CONSUMER_KEY']}
    if verb == 'POST':
        r = requests.post(url, files=files, headers=headers)
    else:
        r = requests.get(url, headers=headers)
    
    return r.json()
        
@app.route('/document/<document_id>')
def getDocumentJSON(document_id):
    """ get all details regarding a rossum.ai scanned document. JSON output"""
    document = getRossum(document_id)
    return jsonify(document)

def getDocument(document_id):
    """ get all details regarding a rossum.ai scanned document"""
    document = getRossum(document_id)
    return document

def getInvoices():
    """loop through all the kashflow purchases and find a matching rossum elis document id"""
    purchases = getPurchaseDocumentIds()
    invoices = []
    for purchase in purchases:
        document = getDocument(purchase['document_id'])
        if purchase['document_id']:
            invoice = dict(
                id = purchase['id'],
                doc_id = purchase['document_id'],
                upload_date = purchase['date'],
                url = getPreviewUrl(purchase['document_id']),
                date = purchase['date'],
                status = 'not yet',
                supplier = document['fields'][21]['value'],
                supplier_id = '??',
                invoice_date = document['fields'][12]['value'],
                invoice_amount = document['fields'][4]['value'],
                invoice_currency = document['currency'],
                invoice_ref = document['fields'][19]['value'],
                invoice_amount_formatted = getCurrencySymbol(document['currency'],document['fields'][4]['value'])
            )
            invoices.append(invoice)
    return invoices
    




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
    
    return humanize.naturaltime(datetime.datetime.now() - date)


# host the app
if __name__ == "__main__":

    sess.init_app(app)

    app.debug = True
    app.host = '0.0.0.0'
    app.port = 80

    app.run()
