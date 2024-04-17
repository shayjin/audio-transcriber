import io
import json
import ssl
import whisper
import os
from SessionInfo import SessionInfo
from flask import Flask, render_template, request, session, redirect, url_for
from werkzeug.utils import secure_filename
from Google import Create_Service
from googleapiclient.http import MediaIoBaseDownload, MediaFileUpload
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials

CLIENT_SECRET_FILE = 'secret.json'
API_NAME = 'drive'
API_VERSION = 'v3'
SCOPES = ['https://www.googleapis.com/auth/drive']
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'mp3'}

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.secret_key = os.urandom(24)
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
ssl._create_default_https_context = ssl._create_unverified_context
service = Create_Service(CLIENT_SECRET_FILE, API_NAME, API_VERSION, SCOPES)
sessionInfo = SessionInfo(None, None, None)

def get_mp3(access_token):
    credentials = Credentials(access_token)
    service = build('drive', 'v3', credentials=credentials)
    files = service.files().list(q="mimeType='audio/mpeg'", fields="files(id, name, size)").execute()
    return files

def delete_leftover_files():    
    for filename in os.listdir("uploads"):
        file_path = os.path.join("uploads", filename)

        if os.path.isfile(file_path):
            os.remove(file_path)

def transcribe(file):
    model = whisper.load_model("small")
    result = model.transcribe(file)
    return result["text"]

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def download(id,name, access_token):
    credentials = Credentials(access_token)
    service = build(API_NAME, API_VERSION, credentials=credentials)
    request = service.files().get_media(fileId=id)
    fh = io.BytesIO()
    downloader = MediaIoBaseDownload(fd=fh, request=request)
    done = False
    
    while not done:
        status, done = downloader.next_chunk()
    
    fh.seek(0)

    with open(os.path.join('./uploads', name), 'wb') as f:
        f.write(fh.read())
        f.close()

@app.route('/')
def index():
    global sessionInfo
    delete_leftover_files()
    return render_template('index.html', variable=sessionInfo.v, files=sessionInfo.f)

@app.route('/about')
def about():
    delete_leftover_files()
    return render_template('about.html', files=sessionInfo.f)

@app.route("/login", methods=["GET"])
def login():
    flow = Flow.from_client_secrets_file(
        "secret.json",
        scopes=SCOPES,
        redirect_uri=url_for("callback", _external=True)
    )
    
    authorization_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true'
    )
    session["state"] = state
    return redirect(authorization_url)

@app.route("/callback", methods=["GET", "POST"])
def callback():
    global sessionInfo

    state = session.pop("state", None)
    flow = Flow.from_client_secrets_file(
        "secret.json",
        scopes=SCOPES,
        state=state,
        redirect_uri=url_for("callback", _external=True)
    )

    flow.fetch_token(authorization_response=request.url)
    session["google_token"] = flow.credentials.to_json()
    access_token = session.get('google_token')
    t = json.loads(access_token)['token']
    files = get_mp3(t)["files"]

    for file in files:
        file["name"] = file["name"].replace("'", "")

    sessionInfo.session = session
    sessionInfo.v = "hi"
    sessionInfo.f = files
    return redirect(url_for('index'))

@app.route("/logout", methods=["GET"])
def logout():
    session.clear()
    sessionInfo.f = None
    sessionInfo.v = None
    return redirect(url_for('index'))

@app.route('/upload', methods=['POST'])
def upload_file():
    file = request.files['mp3_file']

    if request.form["hi"] == "":
        if file and allowed_file(file.filename):
            filename = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(file.filename))
            file.save(filename)
            result = transcribe(filename)
            os.remove(filename)
            return render_template('result.html', result=result.replace("'", "ㄱ"), files=sessionInfo.f)
        else:
            return redirect(url_for('index'))
    else:
        print("hi")
        i1 = request.form["hi"]
        n1 = request.files["mp3_file"].filename
        access_token = session.get('google_token')
        t = json.loads(access_token)['token']
        download(i1, n1, t)
        filename = os.path.join(app.config['UPLOAD_FOLDER'], n1)
        result = transcribe(filename)
        os.remove(filename)
        return render_template('result.html', result=result.replace("'", "ㄱ"), user=sessionInfo.v, files=sessionInfo.f)

@app.route('/download_to_drive')
def upload_to_drive():
    global sessionInfo
    
    contents = request.args.get('param')
    access_token = sessionInfo.session.get('google_token')
    t = json.loads(access_token)['token']
    credentials = Credentials(t)
    service = build('drive', 'v3', credentials=credentials)
    file_metadata = {
        'name': 'result.txt'
    }

    with open('./result.txt', 'w') as f:
        f.write(contents)

    media = MediaFileUpload('./result.txt', mimetype='text/plain')
    service.files().create(body=file_metadata, media_body=media, fields='id').execute()
    return ""

if __name__ == '__main__':
    app.run(debug=True)