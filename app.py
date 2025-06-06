from flask import Flask, render_template, request
#from pathlib import Path

app = Flask(__name__)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/view360')
def view360():
    panorama_url = request.args.get('url')
    return render_template('view360.html', panorama_url=panorama_url)


@app.route('/projeto')
def projeto():
  #  pasta = Path('/caminho/para/pasta')
    return render_template('projeto.html')

@app.route('/animado')
def animacao():
    baseurl='static/images/DJI_20241030151411_0046_D.JPG'
    image='DJI_20241030151411_0046_D.JPG'
    panorama_url = request.args.get('url')
    return render_template('animacao.html', image=image, baseurl=baseurl)

