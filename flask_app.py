from flask import Flask, url_for, render_template, jsonify, request, redirect
from flaskext.mysql import MySQL
import procedures


# Facebook app details
FB_APP_ID = '1733963700184652'
FB_APP_NAME = 'Matching Finder'
FB_APP_SECRET = 'a6b94f66589e9f9a7d558cda0e83a3dd'
API_VERSION = 'v2.6'

HOME=''

# instance_path: Please keep in mind that this path must be absolute when provided. , instance_path='/home/easf/friends/instance'
app = Flask(__name__)
mysql = MySQL()

app.config['MYSQL_DATABASE_USER'] = 'emanuel'
app.config['MYSQL_DATABASE_PASSWORD'] = 'root'
app.config['MYSQL_DATABASE_DB'] = 'friendsdb'
app.config['MYSQL_DATABASE_HOST'] = 'localhost'

mysql.init_app(app)

#app.config['APPLICATION_ROOT'] = '/home/emanuel/'

@app.route(HOME + '/login', methods=['GET','POST'])
def login():
    #names = ['Emanuel', 'Antonio', 'Sanchiz', 'Flores']
    return render_template('login.html', app_id=FB_APP_ID, version=API_VERSION)

@app.route(HOME + '/data')
def data():
    token = request.args.get('token', 0, type=str)
    uid = request.args.get('uid', 0, type=str)
    procedures.proof(uid, token, mysql)
    return jsonify(result = token)

@app.route(HOME + '/')
def index():
    return render_template('index.html', app_id=FB_APP_ID, version=API_VERSION)


@app.route(HOME + '/logout')
def logout():
    return 'logouuuut'

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080)
