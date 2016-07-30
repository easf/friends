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

#recover request form
request_form_connectednessdata = None
request_form_commonpointsdata = None

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
    if not os.path.isfile(ftimepath):
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

# rendering connectedness and interaction frequecncy questions
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
    if status == 'connectedness_questions' and friends_for_connectedness <> []: # if the user reload the page 
    	pass 
    elif status == 'user_data_downloaded': # if the application was crashed and then recover, recalculate friends for connectedness
    	friends_for_connectedness = procedures.get_friends_for_connectedness(uidhash, mysql, token)
    elif status == 'connectedness_questions' and not os.path.isfile(fname): # if the app crashed during or something worng happend when the participant was anwering the questions
    	friends_for_connectedness = procedures.get_friends_for_connectedness(uidhash, mysql, token)
    elif status == 'connectedness_questions' and os.path.isfile(fname): # if the user already anwsered the questions about connectedness before the app got crashed
    	return redirect(url_for('connectednessdata'))
    elif status == 'user_connectedness_data_stored': # if we aalready stored the data about connectedness and interaction frequency questions
    	return redirect(url_for('connectednessdata'))
    elif status == 'finished': # if the user finished the experiment, say thanks
    	return redirect(url_for('friends'))

    start_time = time.time()

    return render_template('connectedness.html', users = friends_for_connectedness, userLang = chlang, textlang = textlang)

# store connectedness data and get friend list for common points
@app.route('/connectednessdata', methods=['GET','POST'] )
def connectednessdata():
    global uidhash
    global friends_for_common_points
    global end_time
    global request_form_connectednessdata

    request_form_connectednessdata = request.form
    fname = "backup/" + str(uidhash) + "_connectedness"

    try:
        data = dict((key, request_form_connectednessdata.getlist(key)[0]) for key in request_form_connectednessdata.keys())
        if len(data) > 4:
            if not os.path.isfile(fname):
                f = open( fname, "w" )
                json.dump(data, f)
                f.close()
    except:
        pass

    connectedness_data = request_form_connectednessdata

    if os.path.isfile(fname):
        f = open( fname, "r" )  
        user_answers = json.load(f)
        f.close()
        connectedness_data = user_answers

    conn = mysql.connect()
    cur = conn.cursor()
    status = procedures.get_user_status (uidhash, cur)
    cur.close()
    conn.close()
    # convert user anwsers in dict
    end_time = time.time()
    ts = time.time()

    if status == 'connectedness_questions' and friends_for_connectedness <> []:
        ftime = open (ftimepath, "a")
    	ftime.write( "Current time: " + datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S') + ": Connectedness and interaction questions, user time -> " + str( (end_time - start_time)/60 ) + " minutes" + "\n" )
    	ftime.close()
        friends_for_common_points = procedures.store_connectedness_data( connectedness_data,  uidhash, mysql )

    elif status == 'user_connectedness_data_stored': # in any case get again the list of friends for common points questions (crashed or no crashed)
        friends_for_common_points = procedures.store_connectedness_data( connectedness_data, uidhash, mysql )
    elif status == 'finished':
        return redirect(url_for('friends'))

    return redirect(url_for('commonpoints'))

# rendering common points
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
        return redirect(url_for('friends'))
    else: #if status == 'user_connectedness_data_stored':
        if os.path.isfile(fname): # if the user already answer the questions about common points
            return redirect( url_for('commonpointsdata') )
        elif friends_for_common_points <> []: # if the user reload the page
            start_time = time.time()
            return render_template('common.html', users=friends_for_common_points, textlang=textlang)
        elif status == 'user_connectedness_data_stored': # if there were a chrash, get again friends for common points
            connectedness_data = request.form
            if os.path.isfile(fname):
                f = open( fname, "r" )  
                user_answers = json.load(f)
                f.close()
                connectedness_data = user_answers
            friends_for_common_points = procedures.store_connectedness_data( connectedness_data, uidhash, mysql )
            start_time = time.time()
            return render_template('common.html', users=friends_for_common_points, textlang=textlang)
        else:	
            return redirect(url_for('thanks'))

@app.route('/commonpointsdata', methods=['GET','POST'] )
def commonpointsdata():
    global end_time
    global request_form_commonpointsdata
    
    request_form_commonpointsdata = request.form
    fname = "backup/" + uidhash + "_commonpoints"
    

    try:
        data = dict((key, request_form_commonpointsdata.getlist(key)[0]) for key in request_form_commonpointsdata.keys())
        if len(data) > 4:
            if not os.path.isfile(fname):
                f = open( fname, "w" )
                json.dump(data, f)
                f.close()
    except:
        pass
    commonpoints_data = request_form_commonpointsdata

    if os.path.isfile(fname):
         f = open( fname, "r" )  
         user_answers = json.load(f)
         f.close()
         commonpoints_data = user_answers

    conn = mysql.connect()
    cur = conn.cursor()
    status = procedures.get_user_status (uidhash, cur)
    cur.close()
    conn.close()
    
    end_time = time.time()
    ts = time.time()
    
    if status <> 'finished':
        ftime = open (ftimepath, "a")
        ftime.write( "Current time: " + datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S') + ": Common points questions, user time -> " + str( (end_time - start_time)/60 ) + " minutes" + "\n" )
        ftime.close()
    	procedures.insert_common_points_data( commonpoints_data, uidhash, mysql )

    return redirect(url_for('friends'))


@app.route('/friends', methods=['GET','POST'] )
def friends():
    global top_ten
    top_ten = procedures.get_best_friends(uidhash, mysql)
    return render_template('bestfriends.html', users=top_ten, textlang=textlang)
    
@app.route('/thanks', methods=['GET','POST'] )
def thanks():
	return render_template('thanks.html', textlang=textlang)

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



    
