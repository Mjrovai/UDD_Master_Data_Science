from flask import Flask, request, g, redirect, url_for, render_template, flash, make_response
# from dotenv import load_dotenv
import requests
import os
import io

# FLASK_APP="main.py"
API_URL="https://westus.api.cognitive.microsoft.com/vision/v2.0/analyze?visualFeatures=Faces&details=Celebrities&language=en"
API_KEY="d37ec0ea33bb4d23b511a32dc2b11089"

PEOPLE_FOLDER = os.path.join('static', 'people_photo')
ALLOWED_EXTENSIONS = set(['pdf', 'png', 'jpg', 'jpeg', 'PDF', 'PNG', 'JPG', 'JPEG'])

app = Flask(__name__)
# APP_ROOT = os.path.join(os.path.dirname(__file__), '..') 
# dotenv_path = os.path.join(APP_ROOT, '.env')
# load_dotenv(dotenv_path)
app.config['UPLOAD_FOLDER'] = PEOPLE_FOLDER

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS                                
@app.route('/')
def hello_world():
	return render_template('index.html')
	

@app.route("/query", methods=["POST"])
def query():
    if request.method == 'POST':
        # RECIBIR DATA DEL POST
        if 'file' not in request.files:
            return render_template('index.html', name='Juan Perez', confidence=0, image = full_filename) 
        file = request.files['file']
        image_data = file.read()
        # if user does not select file, browser also
        # submit an empty part without filename
        if file.filename == '':
            return render_template('index.html', name='Juan Perez', confidence=0, image = full_filename)
        if file and allowed_file(file.filename):
            filename = file.filename
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            image_name = filename
            # POST A AZURE
            url = API_URL
            api_key = API_KEY
            headers={"Content-Type":"application/octet-stream", "Ocp-Apim-Subscription-Key":api_key}
            azure_post = requests.post(url,headers=headers,data=image_data)
            # azure_post es un objeto response, necesitamos parsear su data

            # import pdb; pdb.set_trace()
            azure_obj = azure_post.json()
            full_filename = os.path.join(app.config['UPLOAD_FOLDER'], image_name)
            try:
                if azure_obj['categories'][0]['detail']['celebrities'][0]:
                    name = azure_obj['categories'][0]['detail']['celebrities'][0]['name']
                    confidence = azure_obj['categories'][0]['detail']['celebrities'][0]['confidence']
                    confidence = round(confidence*100)
                    return render_template('index.html', azure = azure_obj, name=name, confidence=confidence, image = full_filename)
            except:
                return render_template('index.html', name='Juan Perez', confidence=0, image = full_filename)
        else:
            return render_template('index.html', name='FILE NOT ALOWED', confidence=0)
    
    # POST con un binario que viene en el adjunto
    # Setear headers antse de enviar el request (Content Type, API KEY)


if __name__ == '__main__':
    app.run()