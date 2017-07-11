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


# UI language, initialize language, english as a default language
fname = "static/js/lang/en.lang.js" 
f = open( fname, "r" )
gtextlang = json.load(f) 
f.close()

# dict sdata to store some data (like friends or answers of participants) per each user
# besides this dict we use the session dict (from flasksession) to store the id and token of user
sdata = {}


# initial page
@app.route('/')
def index():
    # set to the default language
    textlang = gtextlang
    if 'chlang' in session:
        fname = "static/js/lang/" + session['chlang'] + ".lang.js"
        f = open( fname, "r" )
        textlang = json.load(f)
        f.close()
    return render_template('index.html', app_id=FB_APP_ID, version=API_VERSION, textlang=textlang)

# changing UI language
@app.route('/language', methods=['GET','POST'])
def language():
    # set to the user chosen language
    chlang = request.args.get('chLang', 0, type=str)
    if 'chlang' in session:
        session.pop('chlang', None)
    session['chlang'] = chlang 
    return jsonify(result="ok")

# downloading user data
@app.route('/userdata')
def userdata():
    # set or update user's basic data
    if 'token' in session:
        session.pop('token', None) 
    session['token'] = request.args.get('token', 0, type=str)
    uid = request.args.get('uid', 0, type=str)
    browserlang = request.args.get('browserlang', 0, type=str)
    ipcountry = request.args.get('ipcountry', 0, type=str)

    chlang = request.args.get('chLang', 0, type=str)
    if chlang <> 0: # if chlang is null 
        session['chlang'] = chlang

    device = request.args.get('udevice', 0, type=str)
    if 'uidhash' in session:
        session.pop('uidhash', None)
    session['uidhash'] = uid # hashlib.sha1(uid).hexdigest()
    sdata[session['uidhash']] = {}
    ftimepath = "backup/" + session['uidhash'] + "_time"
    if not os.path.isfile(ftimepath):
        ftime = open (ftimepath, "w")
        ftime.close()

    conn = mysql.connect()
    cur = conn.cursor()
    # verify the status of the participants (the experiment stage in which he/she is )
    status = procedures.get_user_status ( session['uidhash'], cur )
    cur.close()
    conn.close()
    # if we don't have yet the participant data (None represents the first state), then we proceed to download the data
    if status == None:
        procedures.download_data(uid, browserlang, ipcountry, device, session['token'], mysql)    

    return jsonify(result="ok")

# rendering connectedness and interaction frequecncy questions
@app.route('/connectedness', methods=['GET','POST'])
def connectedness():
    conn = mysql.connect()
    cur = conn.cursor()
    status = procedures.get_user_status (session['uidhash'], cur)
    cur.close()
    conn.close()

    # path of file to backup the answers of users
    fname = "backup/" + session['uidhash'] + "_connectedness"

    # Do the routing according user state and connectedness_file existence
    if status == 'connectedness_questions' and 'friends_for_connectedness' in sdata[session['uidhash']]: # if the user reload the page 
        pass 
    elif status == 'user_data_downloaded': # if the application had crashed for some circunstance and then it recovered again, recalculate friends for connectedness
        sdata[session['uidhash']]['friends_for_connectedness'] = procedures.get_friends_for_connectedness(session['uidhash'], mysql, session['token'])
    elif status == 'connectedness_questions' and not os.path.isfile(fname): # if the app crashed during when the participant was anwering the questions about connectedness and interaction
        sdata[session['uidhash']]['friends_for_connectedness'] = procedures.get_friends_for_connectedness(session['uidhash'], mysql, session['token'])
    elif status == 'connectedness_questions' and os.path.isfile(fname): # if the user already anwsered the questions about connectedness before the app got crashed
        return redirect(url_for('connectednessdata'))
    elif status == 'user_connectedness_data_stored': # if we already stored the data about connectedness and interaction frequency questions
        return redirect(url_for('connectednessdata'))
    elif status == 'finished': # if the user finished the experiment, just show the final list of 10 friends
        return redirect(url_for('friends'))

    # register the time when the user started the question
    sdata[session['uidhash']]['start_time'] = time.time()
    # check and set the language
    textlang = gtextlang
    if 'chlang' in session:
        fname = "static/js/lang/" + session['chlang'] + ".lang.js"
        f = open( fname, "r" )
        textlang = json.load(f)
        f.close()

    return render_template('connectedness.html', users = sdata[session['uidhash']]['friends_for_connectedness'], textlang = textlang)

# store connectedness data and get friend list for common points
@app.route('/connectednessdata', methods=['GET','POST'] )
def connectednessdata():
    # store participant's answers
    request_form_connectednessdata = request.form
    # backup the answers
    fname = "backup/" + str(session['uidhash']) + "_connectedness"
    #verify if backup file exists, if not exists then create it
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
    # "stop" the user answering time measurement
    sdata[session['uidhash']]['end_time'] = time.time()
    ts = time.time()
    
    ftimepath = "backup/" + session['uidhash'] + "_time"

    if status == 'connectedness_questions' and 'friends_for_connectedness' in sdata[session['uidhash']]: # if didn't store yet the answers, the store them
        ftime = open (ftimepath, "a")
        if 'start_time' in sdata[session['uidhash']]:
            ftime.write( "Current time: " + datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S') + ": Connectedness and interaction questions, user time -> " + str( (sdata[session['uidhash']]['end_time'] - sdata[session['uidhash']]['start_time'])/60 ) + " minutes" + "\n" )
        ftime.close()
        sdata[session['uidhash']]['friends_for_common_points'] = procedures.store_connectedness_data( connectedness_data,  session['uidhash'], mysql )
    elif status == 'user_connectedness_data_stored': # in any case get again the list of friends for common points questions (after the app crashed or no)
        sdata[session['uidhash']]['friends_for_common_points'] = procedures.store_connectedness_data( connectedness_data, session['uidhash'], mysql )
    elif status == 'finished':
        return redirect(url_for('friends'))

    return redirect(url_for('commonpoints'))

# rendering common points
@app.route('/commonpoints', methods=['GET','POST'] )
def commonpoints():
    global current_close_user
    conn = mysql.connect()
    cur = conn.cursor()
    status = procedures.get_user_status (session['uidhash'], cur)
    cur.close()
    conn.close()
    textlang = gtextlang
    if 'chlang' in session:
        fname = "static/js/lang/" + session['chlang'] + ".lang.js"
        f = open( fname, "r" )
        textlang = json.load(f)
        f.close()

    fname = "backup/" + session['uidhash'] + "_commonpoints"
    if status == 'finished':
        return redirect(url_for('friends'))
    else: #if status == 'user_connectedness_data_stored':
        if os.path.isfile(fname): # if the user already answer the questions about common points
            return redirect( url_for('commonpointsdata') )
        elif 'friends_for_common_points' in sdata[session['uidhash']]: # if the user reload the page
            sdata[session['uidhash']]['start_time'] = time.time()
            return render_template('common.html', users=sdata[session['uidhash']]['friends_for_common_points'], textlang=textlang)
        elif status == 'user_connectedness_data_stored': # if there were a chrashed, get again friends for common points
            connectedness_data = request.form
            if os.path.isfile(fname):
                f = open( fname, "r" )  
                user_answers = json.load(f)
                f.close()
                connectedness_data = user_answers
            sdata[session['uidhash']]['friends_for_common_points'] = procedures.store_connectedness_data( connectedness_data, session['uidhash'], mysql )
            sdata[session['uidhash']]['start_time'] = time.time()
            return render_template('common.html', users=sdata[session['uidhash']]['friends_for_common_points'], textlang=textlang)
        else:	
            return redirect(url_for('thanks'))

#store the data from common points answers
@app.route('/commonpointsdata', methods=['GET','POST'] )
def commonpointsdata():
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
        if 'start_time' in sdata[session['uidhash']]:
            ftime.write( "Current time: " + datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S') + ": Common points questions, user time -> " + str( (sdata[session['uidhash']]['end_time'] - sdata[session['uidhash']]['start_time'])/60 ) + " minutes" + "\n" )
        ftime.close()
        procedures.insert_common_points_data( commonpoints_data, session['uidhash'], mysql )

    return redirect(url_for('friends'))

# top ten one side interaction
@app.route('/friends', methods=['GET','POST'] )
def friends():
    if session['uidhash'] in sdata:
        del sdata[session['uidhash']]
    textlang = gtextlang
    if 'chlang' in session:
        fname = "static/js/lang/" + session['chlang'] + ".lang.js"
        f = open( fname, "r" )
        textlang = json.load(f)
        f.close()    
    top_ten = procedures.get_best_friends(session['uidhash'], mysql)
    return render_template('bestfriends.html', users=top_ten, textlang=textlang)

#store student data for credits
@app.route('/creditdata', methods=['GET','POST'] )
def creditdata():
    request_form_creditdata = request.form
    fname = "backup/" + session['uidhash'] + "_credit"
    try:
        data = dict((key, request_form_creditdata.getlist(key)[0]) for key in request_form_creditdata.keys())
        if not os.path.isfile(fname):
            f = open( fname, "w" )
            json.dump(data, f)
            f.close()
    except:
        pass

    credit_data = request_form_creditdata
    #check if all form fields are filled
    credit_form_is_filled = credit_data['sona_id'] and credit_data['first_name'] and credit_data['last_name']

    if os.path.isfile(fname):
         f = open( fname, "r" )
         user_answers = json.load(f)
         f.close()
         credit_data = user_answers

    conn = mysql.connect()
    cur = conn.cursor()
    status = procedures.get_user_status (session['uidhash'], cur)
    cur.close()
    conn.close()

    #sdata[session['uidhash']]['end_time'] = time.time()
    #ts = time.time()

    #ftimepath = "backup/" + session['uidhash'] + "_time"

    if status == 'finished':
        if credit_form_is_filled:
            #ftime = open (ftimepath, "a")
            #if 'start_time' in sdata[session['uidhash']]:
            #    ftime.write( "Current time: " + datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S') + ": Common points questions, user time -> " + str( (sdata[session['uidhash']]['end_time'] - sdata[session['uidhash']]['start_time'])/60 ) + " minutes" + "\n" )
            #ftime.close()

            procedures.insert_credit_data( credit_data, session['uidhash'], mysql )

    #return to home
    return redirect("http://happy.mateine.org/friends-us")
    
@app.route('/thanks', methods=['GET','POST'] )
def thanks():
    #conn = mysql.connect()
    #cur = conn.cursor()
    #cur.execute ("DELETE FROM reactionb USING postb INNER JOIN reactionb WHERE postb.user_idhash = %s AND postb.id = reactionb.post_id", (session['uidhash'],))
    #cur.execute ("DELETE FROM commentb USING postb INNER JOIN commentb WHERE postb.user_idhash = %s AND postb.id = commentb.post_id", (session['uidhash'],))
    #cur.execute ("DELETE FROM tagb USING postb INNER JOIN tagb WHERE postb.user_idhash = %s AND postb.id = tagb.post_id", (session['uidhash'],))
    #cur.execute ("DELETE FROM postb WHERE postb.user_idhash = %s ", (session['uidhash'],))
    #conn.commit()
    #conn.close()
    textlang = gtextlang
    if 'chlang' in session:
        fname = "static/js/lang/" + session['chlang'] + ".lang.js"
        f = open( fname, "r" )
        textlang = json.load(f)
        f.close()
    return render_template('thanks.html', textlang= textlang)

@app.route('/consent', methods=['GET','POST'] )
def consent():
    textlang = gtextlang
    if 'chlang' in session:
        fname = "static/js/lang/" + session['chlang'] + ".lang.js"
        f = open( fname, "r" )
        textlang = json.load(f)
        f.close()
    return render_template('consent.html', textlang=textlang)

@app.route('/about', methods=['GET','POST'] )
def about():
    textlang = gtextlang
    if 'chlang' in session:
        fname = "static/js/lang/" + session['chlang'] + ".lang.js"
        f = open( fname, "r" )
        textlang = json.load(f)
        f.close()
    return render_template('about.html', textlang=textlang)

@app.errorhandler(500)
def internal_error(error):
    textlang = gtextlang
    if 'chlang' in session:
        if session['chlang'] <> 0:
            fname = "static/js/lang/" + session['chlang'] + ".lang.js"
            f = open( fname, "r" )
            textlang = json.load(f)
            f.close()
        else:
            session.pop('chlang', None)
    return render_template('recoverpage.html', app_id=FB_APP_ID, version=API_VERSION, textlang = textlang)

@app.errorhandler(404)
def not_found(error):
    return "404 error",404

if __name__ == "__main__":
    try:
        app.run(debug=False,port=5100, threaded=False)
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
