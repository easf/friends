import config
import procedures
from flask import Flask, url_for, render_template, jsonify, request, redirect
from flaskext.mysql import MySQL
from PrefixMiddleware import PrefixMiddleware



# Facebook app details
FB_APP_ID = '1733963700184652'
FB_APP_NAME = 'Matching Finder'
FB_APP_SECRET = 'a6b94f66589e9f9a7d558cda0e83a3dd'
API_VERSION = 'v2.6'

# instance_path: Please keep in mind that this path must be absolute when provided. , instance_path='/var/www/friends/instance'
app = Flask(__name__, instance_path = config.INSTANCE_PATH)
#application = app  # make uwsgi happy

mysql = MySQL()

# DATABASE SETTINGS

app.config['MYSQL_DATABASE_USER'] = config.MYSQL_DATABASE_USER
app.config['MYSQL_DATABASE_PASSWORD'] = config.MYSQL_DATABASE_PASSWORD
app.config['MYSQL_DATABASE_DB'] = config.MYSQL_DATABASE_DB
app.config['MYSQL_DATABASE_HOST'] = config.MYSQL_DATABASE_HOST

# PREFIX SETTING
app.wsgi_app = PrefixMiddleware(app.wsgi_app, prefix = config.PREFIX)

mysql.init_app(app)


@app.route('/login', methods=['GET','POST'])
def login():
    #names = ['Emanuel', 'Antonio', 'Sanchiz', 'Flores']
    return render_template('login.html', app_id=FB_APP_ID, version=API_VERSION)

@app.route('/data')
def data():
    token = request.args.get('token', 0, type=str)
    uid = request.args.get('uid', 0, type=str)
    procedures.proof(uid, token, mysql)
    return jsonify(result = token)

@app.route('/')
def index():
    return render_template('index.html', app_id=FB_APP_ID, version=API_VERSION)


@app.route('/logout')
def logout():
    return 'logouuuut'

if __name__ == "__main__":
    app.run(debug=False)
