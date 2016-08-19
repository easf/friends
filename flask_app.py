# coding=utf-8
import config
import procedures
from flask import Flask, url_for, render_template, jsonify, request, redirect, session
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
FB_APP_NAME = 'FriendRover'
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
app.config['SECRET_KEY'] = config.SECRET_KEY
app.config['DEBUG'] = False
# URL PREFIX SETTING
app.wsgi_app = PrefixMiddleware(app.wsgi_app, prefix = config.PREFIX)


mysql.init_app(app)

# it makes accesible from all pages the hash id and token of current experiment participant
#session['uidhash'] = None #uidhash = None
#session['token'] = None #token = None

# it contains the list of friends to complete the questions about connectedness and so on
#session['friends_for_connectedness'] = [] #friends_for_connectedness = []

# it contains the list of friends to complete the questions about common points and so on
#session['friends_for_common_points'] = [] #friends_for_common_points = []


# it contains the top list of friends who most interacted in the current experiment participants
#session['top_ten'] = [] #top_ten = []

# variables to track the time that is taken by the participant doing the experiment
#session['start_time'] = None #start_time = None
#session['end_time'] = None #end_time = None
#session['ftimepath'] = None #ftimepath = None
#session['ftime'] = None #ftime = None

# UI language, initialize language, english as a default language
#session['chlang'] = None #chlang = None
fname = "static/js/lang/en.lang.js" #fname = "static/js/lang/en.lang.js"
f = open( fname, "r" )
textlang = json.load(f) #textlang = json.load(f)
f.close()

#recover request form
#session['request_form_connectednessdata'] = None
#session['request_form_commonpointsdata'] = None

#application = app  # make uwsgi happy
sdata = {}
# initial page
@app.route('/')
def index():
    global textlang
    if 'textlang' in session:
        textlang = session['textlang']
    return render_template('index.html', app_id=FB_APP_ID, version=API_VERSION, textlang=textlang)

# changing UI language
@app.route('/language', methods=['GET','POST'])
def language():
    #global chlang
    #global textlang
    chlang = request.args.get('chLang', 0, type=str)
    fname = "static/js/lang/" + str(chlang) + ".lang.js"
    f = open( fname, "r" )
    if 'textlang' in session:
        session.pop('textlang', None)
    session['textlang'] = json.load(f)
    f.close()
    return jsonify(result="ok")

# downloading user data
@app.route('/userdata')
def userdata():
    #global uidhash
    #global token
    #global chlang
    #global ftimepath
    #global ftime
    session['token'] = request.args.get('token', 0, type=str)
    uid = request.args.get('uid', 0, type=str)
    browserlang = request.args.get('browserlang', 0, type=str)
    ipcountry = request.args.get('ipcountry', 0, type=str)
    if 'textlang' in session:
        session.pop('textlang', None)
    chlang = request.args.get('chLang', 0, type=str)
    fname = "static/js/lang/" + str(chlang) + ".lang.js"
    f = open( fname, "r" )
    session['textlang'] = json.load(f)
    f.close()
    device = request.args.get('udevice', 0, type=str)
    if 'uidhash' in session:
        session.pop('uidhash', None)
    session['uidhash'] = hashlib.sha1(uid).hexdigest()
    sdata[session['uidhash']] = {}
    ftimepath = "backup/" + session['uidhash'] + "_time"
    if not os.path.isfile(ftimepath):
        ftime = open (ftimepath, "w")
        ftime.close()

    conn = mysql.connect()
    cur = conn.cursor()

    # verify the status of the participants (the experiment stage in which he/she is )
    status = procedures.get_user_status (session['uidhash'], cur)
    cur.close()
    conn.close()

    # if we don't have yet the participant data (None represents the first state), then we proceed to download the data
    if status == None:
    	procedures.download_data(uid, browserlang, ipcountry, device, session['token'], mysql)    

    return jsonify(result="ok")

# rendering connectedness and interaction frequecncy questions
@app.route('/connectedness', methods=['GET','POST'])
def connectedness():
    #global friends_for_connectedness
    #global start_time

    conn = mysql.connect()
    cur = conn.cursor()
    status = procedures.get_user_status (session['uidhash'], cur)
    cur.close()
    conn.close()

    # file to backup the answers of users
    fname = "backup/" + session['uidhash'] + "_connectedness"

    # Do the routing according user state and connectedness_file existence
    if status == 'connectedness_questions' and 'friends_for_connectedness' in sdata[session['uidhash']]: # if the user reload the page 
    	pass 
    elif status == 'user_data_downloaded': # if the application was crashed and then recover, recalculate friends for connectedness
    	sdata[session['uidhash']]['friends_for_connectedness'] = procedures.get_friends_for_connectedness(session['uidhash'], mysql, session['token'])
    elif status == 'connectedness_questions' and not os.path.isfile(fname): # if the app crashed during or something worng happend when the participant was anwering the questions
    	sdata[session['uidhash']]['friends_for_connectedness'] = procedures.get_friends_for_connectedness(session['uidhash'], mysql, session['token'])
    elif status == 'connectedness_questions' and os.path.isfile(fname): # if the user already anwsered the questions about connectedness before the app got crashed
    	return redirect(url_for('connectednessdata'))
    elif status == 'user_connectedness_data_stored': # if we aalready stored the data about connectedness and interaction frequency questions
    	return redirect(url_for('connectednessdata'))
    elif status == 'finished': # if the user finished the experiment, say thanks
    	return redirect(url_for('friends'))

    sdata[session['uidhash']]['start_time'] = time.time()
    
    if 'textlang' not in session:
        session['textlang'] = textlang

    return render_template('connectedness.html', users = sdata[session['uidhash']]['friends_for_connectedness'], textlang = session['textlang'])

# store connectedness data and get friend list for common points
@app.route('/connectednessdata', methods=['GET','POST'] )
def connectednessdata():
    #global session['uidhash']
    #global friends_for_common_points
    #global end_time
    #global request_form_connectednessdata

    request_form_connectednessdata = request.form
    fname = "backup/" + str(session['uidhash']) + "_connectedness"

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
    status = procedures.get_user_status (session['uidhash'], cur)
    cur.close()
    conn.close()
    # convert user anwsers in dict
    sdata[session['uidhash']]['end_time'] = time.time()
    ts = time.time()
    
    ftimepath = "backup/" + session['uidhash'] + "_time"

    if status == 'connectedness_questions' and 'friends_for_connectedness' in sdata[session['uidhash']]:
        ftime = open (ftimepath, "a")
    	ftime.write( "Current time: " + datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S') + ": Connectedness and interaction questions, user time -> " + str( (sdata[session['uidhash']]['end_time'] - sdata[session['uidhash']]['start_time'])/60 ) + " minutes" + "\n" )
    	ftime.close()
        sdata[session['uidhash']]['friends_for_common_points'] = procedures.store_connectedness_data( connectedness_data,  session['uidhash'], mysql )

    elif status == 'user_connectedness_data_stored': # in any case get again the list of friends for common points questions (crashed or no crashed)
        sdata[session['uidhash']]['friends_for_common_points'] = procedures.store_connectedness_data( connectedness_data, session['uidhash'], mysql )
    elif status == 'finished':
        return redirect(url_for('friends'))

    return redirect(url_for('commonpoints'))

# rendering common points
@app.route('/commonpoints', methods=['GET','POST'] )
def commonpoints():
    global current_close_user
    #global friends_for_common_points
    #global start_time
    conn = mysql.connect()
    cur = conn.cursor()
    status = procedures.get_user_status (session['uidhash'], cur)
    cur.close()
    conn.close()
    fname = "backup/" + session['uidhash'] + "_commonpoints"
    if status == 'finished':
        return redirect(url_for('friends'))
    else: #if status == 'user_connectedness_data_stored':
        if os.path.isfile(fname): # if the user already answer the questions about common points
            return redirect( url_for('commonpointsdata') )
        elif 'friends_for_common_points' in sdata[session['uidhash']]: # if the user reload the page
            sdata[session['uidhash']]['start_time'] = time.time()
            return render_template('common.html', users=sdata[session['uidhash']]['friends_for_common_points'], textlang=session['textlang'])
        elif status == 'user_connectedness_data_stored': # if there were a chrash, get again friends for common points
            connectedness_data = request.form
            if os.path.isfile(fname):
                f = open( fname, "r" )  
                user_answers = json.load(f)
                f.close()
                connectedness_data = user_answers
            sdata[session['uidhash']]['friends_for_common_points'] = procedures.store_connectedness_data( connectedness_data, session['uidhash'], mysql )
            sdata[session['uidhash']]['start_time'] = time.time()
            return render_template('common.html', users=sdata[session['uidhash']]['friends_for_common_points'], textlang=session['textlang'])
        else:	
            return redirect(url_for('thanks'))

@app.route('/commonpointsdata', methods=['GET','POST'] )
def commonpointsdata():
    #global end_time
    #global request_form_commonpointsdata
    
    request_form_commonpointsdata = request.form
    fname = "backup/" + session['uidhash'] + "_commonpoints"
    

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
    status = procedures.get_user_status (session['uidhash'], cur)
    cur.close()
    conn.close()
    
    sdata[session['uidhash']]['end_time'] = time.time()
    ts = time.time()
    
    ftimepath = "backup/" + session['uidhash'] + "_time"

    if status <> 'finished':
        ftime = open (ftimepath, "a")
        ftime.write( "Current time: " + datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S') + ": Common points questions, user time -> " + str( (sdata[session['uidhash']]['end_time'] - sdata[session['uidhash']]['start_time'])/60 ) + " minutes" + "\n" )
        ftime.close()
    	procedures.insert_common_points_data( commonpoints_data, session['uidhash'], mysql )

    return redirect(url_for('friends'))


@app.route('/friends', methods=['GET','POST'] )
def friends():
    #global top_ten
    del sdata[session['uidhash']]
#    session.pop('friends_for_connectedness', None)
    
    top_ten = procedures.get_best_friends(session['uidhash'], mysql)

    return render_template('bestfriends.html', users=top_ten, textlang=session['textlang'])
    
@app.route('/thanks', methods=['GET','POST'] )
def thanks():
	return render_template('thanks.html', textlang=session['textlang'])

@app.route('/about', methods=['GET','POST'] )
def about():
    return render_template('about.html', textlang=session['textlang'])

@app.errorhandler(500)
def internal_error(error):
    if 'textlang' not in session:
        fname = "static/js/lang/en.lang.js" #fname = "static/js/lang/en.lang.js"
        f = open( fname, "r" )
        session['textlang'] = json.load(f) #textlang = json.load(f)
        f.close()
    return render_template('recoverpage.html', app_id=FB_APP_ID, version=API_VERSION, textlang=session['textlang'])

@app.errorhandler(404)
def not_found(error):
    return "404 error",404

if __name__ == "__main__":
    try:
        app.run(debug=False,port=5500, threaded=False)
        print 'comienzooooooooo'    
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
