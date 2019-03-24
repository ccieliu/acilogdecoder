from flask import Flask, url_for, request, g, render_template, make_response, abort, session, redirect, escape, flash
from werkzeug.utils import secure_filename
from decoder import logDecoder
import os
import datetime

app = Flask(__name__, static_folder="data", static_url_path="/data")
app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'

ALLOWED_EXTENSIONS = set(["tar.gz", "tgz", "tar"])


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/', methods=['GET'])
def index():
    if request.method == 'GET':
        return render_template("index.html")


@app.route('/upload', methods=['POST'])
def upload():
    if request.method == "POST":
        if request.form['srno']:
            srNo = str(request.form['srno'])
        else:
            srNo = 'temp'
        if 'file' not in request.files:
            flash('You must upload the file tye of: *.tgz *.tar.gz *.tar')
            return redirect(url_for('index'))
        gotFile = request.files['file']
        if gotFile.filename == '':
            flash('No selected file')
            return redirect(url_for('index'))
        if gotFile and allowed_file(gotFile.filename):
            g.decoderClient = logDecoder(srNo=srNo)
            filename = datetime.datetime.now().strftime("/%Y%m%d_%H_%M_%S_%f-SR_") + \
                secure_filename(gotFile.filename)
            savePath = './data/uploads/' + srNo + filename
            gotFile.save(savePath)
            originFileName = filename
            # g.fileItemList = g.decoderClient.actionsTarFile(
            #     originFileName=g.originFileName, actionName='getnames')
            return redirect('/decode/' + srNo + originFileName + '/')


@app.route('/decode/<srNo>/<originFileName>/', methods=['GET', 'POST'])
def decode(srNo, originFileName):
    if request.method == "GET":
        if os.path.exists('./data/uploads/' + srNo + '/' + originFileName) == True:
            decoderClient = logDecoder(srNo=srNo)
            g.fileItemList = decoderClient.actionsTarFile(
                originFileName=originFileName, actionName='getnames')
            return render_template('index.html')
        else:
            return redirect(url_for('index'))
    if request.method == "POST":
        decoderClient = logDecoder(srNo=srNo)
        decoderClient.actionsTarFile(
            originFileName=originFileName, actionName='unzip')
        attribList = ['severity', 'code', 'affected', 'changeSet', 'descr']
        xmlList = request.form.getlist('chooseList')
        g.resultList = []
        for xmlFileNameItem in xmlList:
            g.resultList.append(decoderClient.returnLineResult(
                xmlFileName=xmlFileNameItem, attribList=attribList))
        g.fileItemList = decoderClient.actionsTarFile(
                originFileName=originFileName, actionName='getnames')
        g.resultZipFilePath = decoderClient.compressResultDir()
        print (g.resultZipFilePath)
        return render_template('index.html')


@app.route('/decode/<srNo>/<originFileName>/', methods=['GET'])
def download():
    pass


if __name__ == '__main__':
    app.run()
