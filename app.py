from flask import Flask, render_template, request, redirect

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/assets')
def assets():
    return render_template('assets.html') 

@app.route('/equity')
def equity():
    return render_template('equity.html')

@app.route('/taxes')
def taxes():
    return render_template('taxes.html')

@app.route('/crypto')
def crypto():
    return render_template('crypto.html')

@app.route('/budget')
def budget():
    return render_template('budget.html')

app.run(debug=True, port=3000)