# coding=utf-8
import config
import procedures
from flask import Flask, url_for, render_template, jsonify, request, redirect
from flaskext.mysql import MySQL
from PrefixMiddleware import PrefixMiddleware
import socket, errno, time
import sys,hashlib, os, json
import time
import datetime

reload(sys)  
sys.setdefaultencoding('utf8')

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

# URL PREFIX SETTING
app.wsgi_app = PrefixMiddleware(app.wsgi_app, prefix = config.PREFIX)

mysql.init_app(app)

# it makes accesible from all pages the hash id and token of current experiment participant
uidhash = None
token = None

# it contains the list of friends to complete the questions about connectedness and so on
friends_for_connectedness = []

# it contains the list of friends to complete the questions about common points and so on
friends_for_common_points = []


# it contains the top list of friends who most interacted in the current experiment participants
top_ten = []

# variables to track the time that is taken by the participant doing the experiment
start_time = None
end_time = None
ftimepath = None
ftime = None

# UI language, initialize language, english as a default language
chlang = None
fname = "static/js/lang/en.lang.js"
f = open( fname, "r" )
textlang = json.load(f)
f.close()


# initial page
@app.route('/')
def index():
	return render_template('index.html', app_id=FB_APP_ID, version=API_VERSION, textlang=textlang)

# changing UI language
@app.route('/language', methods=['GET','POST'])
def language():
	global chlang
	global textlang

	chlang = request.args.get('chLang', 0, type=str)

	fname = "static/js/lang/"+ chlang + ".lang.js"
	f = open( fname, "r" )
	textlang = json.load(f)
	f.close()

	return jsonify(result="ok")

# downloading user data
@app.route('/userdata')
def userdata():
    global uidhash
    global token
    global chlang
    global ftimepath
    global ftime
    
    token = request.args.get('token', 0, type=str)
    uid = request.args.get('uid', 0, type=str)
    browserlang = request.args.get('browserlang', 0, type=str)
    ipcountry = request.args.get('ipcountry', 0, type=str)
    chlang = request.args.get('chLang', 0, type=str)
    device = request.args.get('udevice', 0, type=str)
    
    uidhash = hashlib.sha1(uid).hexdigest()
    
    ftimepath = "backup/" + uidhash + "_time"
    ftime = open (ftimepath, "w")
    ftime.close()

    conn = mysql.connect()
    cur = conn.cursor()
    # verify the status of the participants (the experiment stage in which he/she is )
    status = procedures.get_user_status (uidhash, cur)
    cur.close()
    conn.close()

    # if we don't have yet the participant data (None represents the first state), then we proceed to download the data
    if status == None:
    	procedures.download_data(uid, browserlang, ipcountry, device, token, mysql)    

    return jsonify(result="ok")


@app.route('/connectedness', methods=['GET','POST'])
def connectedness():
    global friends_for_connectedness
    global start_time

    conn = mysql.connect()
    cur = conn.cursor()
    status = procedures.get_user_status (uidhash, cur)
    cur.close()
    conn.close()

    # file to backup the answers of users
    fname = "backup/" + uidhash + "_connectedness"

    # Do the routing according user state and connectedness_file existence
    if status == 'connectedness_questions' and friends_for_connectedness <> []:
    	pass 
    elif status == 'user_data_downloaded':
    	friends_for_connectedness = procedures.get_friends_for_connectedness(uidhash, mysql, token)
    elif status == 'connectedness_questions' and not os.path.isfile(fname):
    	friends_for_connectedness = procedures.get_friends_for_connectedness(uidhash, mysql, token)
    elif status == 'connectedness_questions' and os.path.isfile(fname):
    	return redirect(url_for('connectednessdata'))
    elif status == 'user_connectedness_data_stored':
    	return redirect(url_for('connectednessdata'))
    elif status == 'finished':
    	return render_template('thanks.html')

    start_time = time.time()
    return render_template('connectedness.html', users = friends_for_connectedness, userLang = chlang, textlang = textlang)


@app.route('/connectednessdata', methods=['GET','POST'] )
def connectednessdata():
    global uidhash
    global friends_for_common_points
    global end_time

    conn = mysql.connect()
    cur = conn.cursor()
    status = procedures.get_user_status (uidhash, cur)
    cur.close()
    conn.close()
    # convert user anwsers in dict
    end_time = time.time()
    ts = time.time()


    fname = "backup/" + uidhash + "_connectedness"

    try:
        data = dict((key, request.form.getlist(key)[0]) for key in request.form.keys())
        if len(data) > 4:
            if not os.path.isfile(fname):
                f = open( fname, "w" )
                json.dump(data, f)
                f.close()
    except:
        pass

    connectedness_data = request.form

    if os.path.isfile(fname):
        f = open( fname, "r" )  
        user_answers = json.load(f)
        f.close()
        connectedness_data = user_answers

    if status == 'connectedness_questions' and friends_for_connectedness <> []:
        ftime = open (ftimepath, "a")
    	ftime.write( "Current time: " + datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S') + ": Connectedness and interaction questions, user time -> " + str( (end_time - start_time)/60 ) + " minutes" + "\n" )
    	ftime.close()
        friends_for_common_points = procedures.store_connectedness_data( connectedness_data,  uidhash, mysql )

    elif status == 'user_connectedness_data_stored':
        friends_for_common_points = procedures.store_connectedness_data( connectedness_data, uidhash, mysql )
    elif status == 'finished':
        return render_template('thanks.html')

    return redirect(url_for('commonpoints'))

@app.route('/commonpoints', methods=['GET','POST'] )
def commonpoints():
    global current_close_user
    global friends_for_common_points
    global start_time
    conn = mysql.connect()
    cur = conn.cursor()
    status = procedures.get_user_status (uidhash, cur)
    cur.close()
    conn.close()
    fname = "backup/" + uidhash + "_commonpoints"
    if status == 'finished':
        return render_template('thanks.html')
    else: #if status == 'user_connectedness_data_stored':
        if os.path.isfile(fname):
            return redirect( url_for('commonpointsdata') )
        elif friends_for_common_points <> []:
            start_time = time.time()
            return render_template('common.html', users=friends_for_common_points, textlang=textlang)
        elif status == 'user_connectedness_data_stored':
            connectedness_data = request.form
            if os.path.isfile(fname):
                f = open( fname, "r" )  
                user_answers = json.load(f)
                f.close()
                connectedness_data = user_answers
            friends_for_common_points = procedures.store_connectedness_data( connectedness_data, friends_for_connectedness, uidhash, mysql )
            start_time = time.time()
            return render_template('common.html', users=friends_for_common_points, textlang=textlang)
        else:	
            return redirect(url_for('thanks'))

@app.route('/commonpointsdata', methods=['GET','POST'] )
def commonpointsdata():
    global end_time
    fname = "backup/" + uidhash + "_commonpoints"
    
    end_time = time.time()
    ftime = open (ftimepath, "a")
    ts = time.time()
    ftime.write( "Current time: " + datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S') + ": Common points questions, user time -> " + str( (end_time - start_time)/60 ) + " minutes" + "\n" )
    ftime.close()

    try:
        data = dict((key, request.form.getlist(key)[0]) for key in request.form.keys())
        if len(data) > 4:
            if not os.path.isfile(fname):
                print 'jajajajaajjajaja'
                f = open( fname, "w" )
                json.dump(data, f)
                f.close()
    except:
        pass
    commonpoints_data = request.form

    if os.path.isfile(fname):
         f = open( fname, "r" )  
         user_answers = json.load(f)
         f.close()
         commonpoints_data = user_answers

    procedures.insert_common_points_data( commonpoints_data, uidhash, mysql )
    return redirect(url_for('friends'))

@app.route('/friends', methods=['GET','POST'] )
def friends():
    global top_ten
    top_ten = procedures.get_best_friends(uidhash, mysql)
    return render_template('bestfriends.html', users=top_ten, textlang=textlang)
    
@app.route('/thanks', methods=['GET','POST'] )
def thanks():
	return render_template('thankyou.html', userLang=chlang)

@app.errorhandler(500)
def internal_error(error):
    return render_template('recoverpage.html', app_id=FB_APP_ID, version=API_VERSION, textlang=textlang)

@app.errorhandler(404)
def not_found(error):
    return "404 error",404

if __name__ == "__main__":
    try:
        app.run(debug=True, threaded=False)    
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



    
