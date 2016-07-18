# coding=utf-8
import config
import procedures
from flask import Flask, url_for, render_template, jsonify, request, redirect
from flaskext.mysql import MySQL
from PrefixMiddleware import PrefixMiddleware
import socket, errno, time

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
list_of_friends = []
token = None

@app.route('/connectedness', methods=['GET','POST'])
def connectedness():
    global list_of_friends    
    list_of_friends = procedures.get_list_of_friends(uidhash, mysql, token)    
    return render_template('closeness.html', users=list_of_friends)

@app.route('/userdata')
def userdata():
    global uidhash
    global token
    token = request.args.get('token', 0, type=str)
    uid = request.args.get('uid', 0, type=str)
    uidhash = procedures.download_data(uid, token, mysql)    
    return jsonify(result="ok")

@app.route('/')
def index():
    return render_template('index.html', app_id=FB_APP_ID, version=API_VERSION)


@app.route('/connectedata', methods=['GET','POST'] )
def connectedata():
    global uidhash
    global closer_users
    #print request.form
    closer_users = procedures.store_connectedness_data( request, list_of_friends, uidhash, mysql )
    return redirect(url_for('survey'))

@app.route('/survey', methods=['GET','POST'] )
def survey():
    global current_close_user
        
    #channels = channels = [{"id":"ftf", "name":"Face to face"}, {"id":"pc","name":"Phone Calls"}, {"id":"vc","name":"Video chats"}, {"id":"sn", "name":"Social Networks"}, {"id":"sms","name":"Messaging"}]
    channels = channels = [{"id":"f2f", "name":"Face to face"}, {"id":"online","name":"Online"}]
    if request.method == 'POST':
        procedures.insert_survey_data( request, uidhash, current_close_user, mysql )
    #closer_users = [{"id":"0" ,"name":"Emanuel Sanchiz", 'pic':"https://scontent.xx.fbcdn.net/v/t1.0-1/p50x50/13124828_1405791279447233_1812688549634903355_n.jpg?oh=85e93710c4000544ccadbe2535cdf09e&oe=57EC99C8"}]
    if closer_users <> []:
        current_close_user = closer_users.pop(0)
        return render_template('survey.html', channels = channels, user=current_close_user)
    else:
        return render_template('thankyou.html')

@app.errorhandler(500)
def internal_error(error):

    return "Wrong things happened :'( , can you reload the page please"

@app.errorhandler(404)
def not_found(error):
    return "404 error",404

if __name__ == "__main__":
    try:
        app.run(debug=False, threaded=True)    
    except socket.error, e:
        if isinstance(e.args, tuple):
            print "errno is %d" % e[0]
            if e[0] == errno.EPIPE:
               # remote peer disconnected
               print "Detected remote disconnect"
            else:
               # determine and handle different error
               pass
        else:
            print "socket error ", error
    except IOError, e:
        # Hmmm, Can IOError actually be raised by the socket module?
        print "Got IOError: ", e



    
