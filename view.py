from flask import Flask, url_for, render_template, jsonify, request, redirect
import procedures


# Facebook app details
FB_APP_ID = '1733963700184652'
FB_APP_NAME = 'Matching Finder'
FB_APP_SECRET = 'a6b94f66589e9f9a7d558cda0e83a3dd'
API_VERSION = 'v2.6'

app = Flask(__name__)

#app.config['APPLICATION_ROOT']= ''

@app.route('/login', methods=['GET','POST'])
def login():
    #names = ['Emanuel', 'Antonio', 'Sanchiz', 'Flores']
    return render_template('login.html', app_id=FB_APP_ID, version=API_VERSION)

@app.route('/data')
def data():
    token = request.args.get('token', 0, type=str)
    uid = request.args.get('uid', 0, type=str)
    procedures.proof(uid, token)
    return jsonify(result = token)

@app.route('/index')
def index():
    return render_template('index.html', app_id=FB_APP_ID, version=API_VERSION)


@app.route('/logout')
def logout():
    return 'logouuuut'




