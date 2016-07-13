# coding=utf-8
import config
import procedures
import MySQLdb
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

uidhash = None
current_close_user = None
closer_users = []
ranking = []
token = None

@app.route('/ranking', methods=['GET','POST'])
def ranking():
    global ranking    
    ranking = procedures.get_ranking(uidhash, mysql, token)    
    return render_template('ranking.html', users=ranking)

@app.route('/data')
def data():
    global uidhash
    global token
    token = request.args.get('token', 0, type=str)
    uid = request.args.get('uid', 0, type=str)
    uidhash = procedures.download_data(uid, token, mysql)    
    return jsonify(result="ok")

@app.route('/')
def index():
    return render_template('index.html', app_id=FB_APP_ID, version=API_VERSION)


@app.route('/hello', methods=['POST'])
def hello():
    global uidhash
    global closer_users
    closer_users = procedures.closeness_filter( request, ranking, uidhash, mysql )
    return redirect(url_for('survey'))

@app.route('/survey', methods=['GET','POST'] )
def survey():
    global current_close_user
        
    #channels = channels = [{"id":"ftf", "name":"Face to face"}, {"id":"pc","name":"Phone Calls"}, {"id":"vc","name":"Video chats"}, {"id":"sn", "name":"Social Networks"}, {"id":"sms","name":"Messaging"}]
    channels = channels = [{"id":"ftf", "name":"Face to face"}, {"id":"fb","name":"Facebook"}, {"id":"other","name":"Other remote channels"}]
    if request.method == 'POST':
        procedures.insert_survey_data( request, uidhash, current_close_user, mysql )
    #closer_users = [{"id":"0" ,"name":"Emanuel Sanchiz", 'pic':"https://scontent.xx.fbcdn.net/v/t1.0-1/p50x50/13124828_1405791279447233_1812688549634903355_n.jpg?oh=85e93710c4000544ccadbe2535cdf09e&oe=57EC99C8"}]
    if closer_users <> []:
        current_close_user = closer_users.pop(0)
        return render_template('survey.html', channels = channels, user=current_close_user)
    else:
        return render_template('thankyou.html')

if __name__ == "__main__":
    app.run(debug=False)
