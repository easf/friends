# coding=utf-8
from multiprocessing import Process, Queue, Pool, Manager
import multiprocessing.pool
import facebook, collections, hashlib, data_processing
import sys
import time, hashlib, langdetect, json, requests, config
from functools import partial
import numpy as np
import random, json

reload(sys)  
sys.setdefaultencoding('utf8')

NO = 0
YES = 1

def pagination_s(data, limit):
    alldata = [] 
    while(limit):
        try:
            for item in data['data']:
                alldata.append(item)
            data=requests.get(data['paging']['next']).json()
            limit -= 1
        except KeyError:
            break
    return alldata

def paginate_posts(posts):
    try:
        for post in posts['data']:
            try:
                reactions = pagination_s ( post['reactions'], 2 )
                post['reactions']['data'] = reactions
            except KeyError:
                pass
    except KeyError:
        pass

def pagination(data):
    queue = data[0]
    statistics = data[1]
    graph = data[2]
    uid = data[3]
    start_time = time.time()                                                                                                                                                                                                                                                                                                                        
    try:
        posts = graph.get_connections (id=uid, connection_name = '?fields=posts.limit('+ str(config.POST_FIRST_CALL_LIMIT_1) +'){created_time,type,story,story_tags,privacy,link,message,application,reactions.summary(true).limit('+str(config.REACTIONS_LIMIT)+'),comments.summary(true).limit('+str(config.COMMENTS_LIMIT)+'){created_time,from,attachment,message,message_tags,likes.summary(true).limit(10),comments.summary(true).limit(10){created_time,from}}}')
    except:
        posts = graph.get_connections (id=uid, connection_name = '?fields=posts.limit('+ str(config.POST_FIRST_CALL_LIMIT_2) +'){created_time,type,story,story_tags,privacy,link,message,application,reactions.summary(true).limit('+str(config.REACTIONS_LIMIT)+'),comments.summary(true).limit('+str(config.COMMENTS_LIMIT)+'){created_time,from,attachment,message,message_tags,likes.summary(true).limit(10)}}')
    c=1
    end_time = time.time()
    statistics.write( 'Time getting post data (from GraphAPI) ' + str(c) + ': ' + str(end_time - start_time) + '\n' )
    data = posts['posts']   
    alldata = []
    p_limit = config.PAGINATION_LIMIT  
    while(p_limit):
        try:
            for item in data['data']:
                alldata.append(item)
            queue.put(alldata[:])
            #print "pagination", len (alldata)
            del alldata[:]
            start_time = time.time()
            data=requests.get(data['paging']['next']).json()
            p_limit -= 1
            c+=1
            end_time = time.time()
            statistics.write( 'Time getting post data (from GraphAPI) ' + str(c) + ': ' + str(end_time - start_time) + '\n' )
        except KeyError:
            break
    #print 'Nro de llamadas: ', c 
    queue.put('DONE')

def process_comment_data (post, comment, comment_keys, uidhash,  comment_d_insertion, reaction_d_insertion, tag_d_insertion, user_d_insertion, page_d_insertion ):    
    if len(comment_keys) > 1: # just do if there more than the comment id
        try:
            comment_summary_total_count = comment['comments']['summary']['total_count'] # for the most inner comment I don't retriever the inner comments related (leaf)
        except KeyError:
            comment_summary_total_count = None
        try:
            comment_likes_total_count = comment['likes']['summary']['total_count'] # for the most inner comment I don't retriever the inner comments related (leaf)
        except KeyError:
            comment_likes_total_count = None
        try: #if 'from' in comment_keys:
            comment_from_id = comment['from']['id']
            comment_from_name = comment['from']['name'] 
            idhash = comment['from']['id'] #hashlib.sha1( comment['from']['id'] ).hexdigest()
            del comment['from']
        except KeyError: #else:
            comment_from_id = 'from does not exist' 
            comment_from_name = 'from does not exist'
            idhash = 'from does not exist'
        if 'created_time' in comment_keys:
            created_time = comment['created_time']
            del comment['created_time']
        else:
            created_time = None

        has_picture = False
        has_link = False
        try: #if 'attachment' in comment_keys:
            if comment['attachment']['type'] == 'photo':  
                has_picture = True
            if comment['attachment']['type'] == 'share':
                has_link = True
            del comment['attachment']
        except KeyError:
            pass

        if 'message' in comment_keys:
            message_length = len(comment['message'])
        else:
            message_length = None
        
        message_language = None

        #cur.execute( "INSERT INTO user ( idhash, id, name ) " "VALUES (%s, %s, %s) ON DUPLICATE KEY UPDATE idhash = idhash", ( idhash, comment_from_id, comment_from_name ) )
        user_d_insertion.append ( ( idhash, comment_from_id, comment_from_name, False ) )
        #cur.execute("INSERT INTO comment ( id, post_id, user_idhash, created_time, language, has_picture, has_link, nreactions, ncomments, text_lenght ) " "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s) ON DUPLICATE KEY UPDATE has_picture = VALUES(has_picture), has_link = VALUES(has_link), nreactions = VALUES(nreactions), ncomments = VALUES(ncomments), text_lenght = VALUES(text_lenght)", ( comment['id'], post['id'], idhash, created_time, message_language, has_picture, has_link, comment_likes_total_count, comment_summary_total_count, message_length ) )
        comment_d_insertion.append( ( comment['id'], post['id'], idhash, created_time, has_picture, has_link, comment_likes_total_count, comment_summary_total_count, message_length ) )

        try: #if 'likes' in comment_keys:
            if comment_likes_total_count > 0:
                while comment['likes']['data']:
                    like = comment['likes']['data'].pop(0)
                    idhash = like['id'] #hashlib.sha1( like['id']).hexdigest()
                    #cur.execute( "INSERT INTO user ( idhash, id, name ) " "VALUES (%s, %s, %s) ON DUPLICATE KEY UPDATE idhash = idhash", ( idhash, like['id'], like['name'] ))
                    user_d_insertion.append ( ( idhash, like['id'], like['name'], False ) )
                    #if uidhash not in granted_users:
                        #cur.execute("INSERT INTO reaction ( user_idhash, post_id, comment_id, type ) " "VALUES (%s, %s, %s, %s)", ( idhash, post['id'], comment['id'], 'LIKE' ))
                    reaction_d_insertion.append (( idhash, post['id'], comment['id'], 'LIKE' ))
        except KeyError:
            pass

        try: #if 'message_tags' in comment_keys:
            while comment['message_tags']:
                message_tag = comment['message_tags'].pop(0)
                if message_tag['type'] == 'user':
                    idhash = message_tag['id'] #hashlib.sha1( message_tag['id']).hexdigest()
                    #cur.execute( "INSERT INTO user ( idhash, id, name ) " "VALUES (%s, %s, %s) ON DUPLICATE KEY UPDATE idhash = idhash", ( idhash, message_tag['id'], message_tag['name'] ))
                    user_d_insertion.append ( ( idhash, message_tag['id'], message_tag['name'], False ) )
                    #if uidhash not in granted_users:
                        #cur.execute("INSERT INTO tag ( post_id, comment_id, type, user_idhash, page_id ) " "VALUES (%s, %s, %s, %s, %s)", ( post['id'], comment['id'], message_tag['type'], idhash, None  ))
                    tag_d_insertion.append ( ( post['id'], comment['id'], message_tag['type'], idhash, None  ) )
                elif message_tag['type'] == 'page':
                    #cur.execute("INSERT INTO page ( id, name, category, total_fans ) " "VALUES (%s, %s, %s, %s) ON DUPLICATE KEY UPDATE id = id", ( message_tag['id'], message_tag['name'], None, None ) )                    
                    page_d_insertion.append ( ( message_tag['id'], message_tag['name'], None, None ) )
                    #if uidhash not in granted_users:
                         #cur.execute("INSERT INTO tag ( post_id, comment_id, type, user_idhash, page_id ) " "VALUES (%s, %s, %s, %s, %s)", ( post['id'], None, story_tag['type'], None, message_tag['id'] ))
                    tag_d_insertion.append ( ( post['id'], None, message_tag['type'], None, message_tag['id'] ) )                      
        except KeyError:
            pass


def process_posts_data( data ):
# uid, uidhash, granted_users, post_d_insertion, comment_d_insertion, reaction_d_insertion, user_d_insertion, comm_h_comm_insertion, tag_d_insertion, page_d_insertion, data
    # insertion_statement = ("INSERT INTO post ( id, user_idhash, created_time, type, story, privacy, text_length, link, nreactions, ncomments, application, shares_count, language ) " "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) ON DUPLICATE KEY UPDATE type = VALUES(type), story = VALUES(story), privacy= VALUES(privacy), text_length= VALUES(text_length), link= VALUES(link), nreactions= VALUES(nreactions), ncomments = VALUES(ncomments), application = VALUES(application), shares_count = VALUES(shares_count), language = VALUES(language)")    
    c=0
    #manager = Manager()
    post_d_insertion = []
    comment_d_insertion = []
    reaction_d_insertion = []
    user_d_insertion = []
    comm_h_comm_insertion = []
    tag_d_insertion = []
    page_d_insertion = []

    while True:
        #queue, id, uidhash, granted_users, cur
        queue = data[0]
        uid = data[1]
        uidhash = data[2]
        #granted_users = data[3]
        cur = data[3]
        statistics = data[4]

        data_from_queue = queue.get()
 
        if data_from_queue == 'DONE':
            #print 'Llamadas process', c
            break
        else:
            #print "Process", len ( data_from_queue )
            c += 1
            while data_from_queue:
                post = data_from_queue.pop(0)
                e = 0
                start_time = time.time()
                #post = data
                post_keys = post.keys()
                try:
                    post_reactions_summary_total_count = post['reactions']['summary']['total_count']
                    del post['reactions']['summary']
                except KeyError:
                    post_reactions_summary_total_count = None
                    e += 1
                try:
                    post_comments_summary_total_count = post['comments']['summary']['total_count']
                    del post['comments']['summary']
                except KeyError:
                    post_comments_summary_total_count = None
                    e += 1

                if 'created_time' in post_keys:
                    created_time = post['created_time']
                    del post['created_time']
                else:
                    created_time = None
                    e += 1
                try:
                    post_privacy = post['privacy']['description']
                    del post['privacy']
                except KeyError:
                    post_privacy = None
                    e += 1
                if 'story' in post_keys:
                    post_story = post['story']
                    del post['story']
                else:
                    post_story = None
                if 'message' in post_keys:
                    post_message_lenght = len(post['message'])
                else:
                    post_message_lenght = None
                post_message_language = None
                try:
                    post_shares_count = post['shares']['count']
                    del post['shares']
                except KeyError:
                    post_shares_count = None
                    e += 1
                try:
                    post_app = post['application']['name']
                    del post['application']
                except:
                    post_app = None
                    e += 1
                try:
                    post_link = post['link'][:64]
                    del post['link']
                except:
                    post_link = None
                    e += 1
                try:
                    post_type = post['type']
                except KeyError:
                    post_type = None
                    e += 1
                #posts_data.append ( { 'post_id':post['id'], 'idhash':uidhash, 'created_time':created_time, 'post_type':post['type'], 'story':post_story, 'privacy':post['privacy']['description'], 'text_length':post_message_lenght, 'link':post_link, 'nreactions':post_reactions_summary_total_count, 'ncomments':post_comments_summary_total_count, 'application':post_app, 'shares_count':post_shares_count, 'language':post_message_language } )
                # ( post['post_id'], post['idhash'],post['created_time'], post['post_type'], post['story'], post['privacy'], post['text_length'], post['link'], post['nreactions'], post['ncomments'], post['application'], post['shares_count'], post['language'] )
                end_time = time.time()
                #print  'Time processing only post_____: ' + post['id'] + ' num of exceptions: '+ str(e) + ' time -> '+ str(end_time - start_time) + '\n'
                post_data = ( post['id'], uidhash, created_time, post_type, post_story, post_privacy, post_message_lenght, post_link, post_reactions_summary_total_count, post_comments_summary_total_count, post_app )
                post_d_insertion.append ( post_data )

                #cur.execute( "INSERT INTO post ( id, user_idhash, created_time, type, story, privacy, text_length, link, nreactions, ncomments, application, shares_count, language ) " "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) ON DUPLICATE KEY UPDATE type = VALUES(type), story = VALUES(story), privacy= VALUES(privacy), text_length= VALUES(text_length), link= VALUES(link), nreactions= VALUES(nreactions), ncomments = VALUES(ncomments), application = VALUES(application), shares_count = VALUES(shares_count), language = VALUES(language)", post_data )
                if 'reactions' in post_keys:
                    try:
                        del post['reactions']['paging']
                    except KeyError:
                        pass
                    try:
                        if post_reactions_summary_total_count <> None:
                            if post_reactions_summary_total_count > 0:
                                while post['reactions']['data']:
                                    reaction =  post['reactions']['data'].pop(0) #post['reactions']['data'][index_r]
                                    try:
                                        idhash = reaction['id'] #hashlib.sha1( reaction['id']).hexdigest()
                                        user_d_insertion.append ( ( idhash, reaction['id'], reaction['name'], False ) )
                                        #cur.execute( "INSERT INTO user ( idhash, id, name ) " "VALUES (%s, %s, %s) ON DUPLICATE KEY UPDATE idhash = idhash", ( idhash, reaction['id'], reaction['name'] ) )
                                        #if uidhash not in granted_users:
                                        reaction_d_insertion.append ( ( idhash, post['id'], None, reaction['type'] ) )
                                            #cur.execute("INSERT INTO reaction ( user_idhash, post_id, comment_id, type ) " "VALUES (%s, %s, %s, %s)", ( idhash, post['id'], None, reaction['type'] ))
                                    except KeyError:
                                        pass
                    except KeyError:    
                        pass
                
                if 'comments' in post_keys:
                    try:
                        del post['comments']['paging']
                    except KeyError:
                        pass
                    try: 
                        if post_comments_summary_total_count <> None:
                            if post_comments_summary_total_count > 0:
                                comment_len = len(post['comments']['data'])                        # 
                                try: 
                                    while post['comments']['data']:
                                        comment =post['comments']['data'].pop(0)
                                        comment_keys = comment.keys()
                                        process_comment_data ( post, comment, comment_keys, uidhash,  comment_d_insertion, reaction_d_insertion, tag_d_insertion, user_d_insertion, page_d_insertion)
                                        if 'comments' in comment_keys:
                                            try:
                                                del comment['comments']['paging']
                                            except KeyError:
                                                pass
                                            while comment['comments']['data']:
                                                inner_comment = comment['comments']['data'].pop()
                                                inner_comment_keys = inner_comment.keys()
                                                process_comment_data ( post, inner_comment, inner_comment_keys, uidhash,  comment_d_insertion, reaction_d_insertion, tag_d_insertion, user_d_insertion, page_d_insertion)
                                                comm_h_comm_insertion.append ( ( comment['id'], inner_comment['id'] ) )

                                except KeyError:
                                    pass
                    except KeyError:
                        pass

                if 'story_tags' in post_keys:
                    while post['story_tags']:
                        story_tag = post['story_tags'].pop(0)
                        try: # if there is not type of story_tag don't add
                            if story_tag['type'] == 'user':
                                if story_tag['id'] <> uid:
                                    idhash = story_tag['id'] #hashlib.sha1( story_tag['id']).hexdigest()
                                    user_d_insertion.append ( ( idhash, story_tag['id'], story_tag['name'], False )  )
                                    #cur.execute( "INSERT INTO user ( idhash, id, name ) " "VALUES (%s, %s, %s) ON DUPLICATE KEY UPDATE idhash = idhash",( idhash, story_tag['id'], story_tag['name'] ))
                                    #if uidhash not in granted_users:
                                        #cur.execute("INSERT INTO tag ( post_id, comment_id, type, user_idhash, page_id ) " "VALUES (%s, %s, %s, %s, %s)", ( post['id'], None, story_tag['type'], idhash, None ))
                                    tag_d_insertion.append ( ( post['id'], None, story_tag['type'], idhash, None ) )
                            elif story_tag['type'] == 'page':
                                #cur.execute("INSERT INTO page ( id, name, category, total_fans ) " "VALUES (%s, %s, %s, %s) ON DUPLICATE KEY UPDATE id = id", ( story_tag['id'], story_tag['name'], None, None ) )
                                page_d_insertion.append (( story_tag['id'], story_tag['name'], None, None )  )
                                #if uidhash not in granted_users:
                                    #cur.execute("INSERT INTO tag ( post_id, comment_id, type, user_idhash, page_id ) " "VALUES (%s, %s, %s, %s, %s)", ( post['id'], None, story_tag['type'], None, story_tag['id'] ))
                                tag_d_insertion.append (  ( post['id'], None, story_tag['type'], None, story_tag['id'] ))
                                #story_tags_pages.append({'post_id':post['id'], 'comment_id':None , 'idhash':None, 'id':None, 'name':story_tag['name'], 'type':story_tag['type'], 'page_id':story_tag['id']})
                        except KeyError:
                            pass

                # here, we do all the insertion data of user's posts
                cur.execute ("SET FOREIGN_KEY_CHECKS=0")
                cur.executemany( "INSERT INTO user ( idhash, id, name, granted_permissions ) " "VALUES (%s, %s, %s, %s) ON DUPLICATE KEY UPDATE idhash = idhash", user_d_insertion )
                cur.executemany( "INSERT INTO post ( id, user_idhash, created_time, type, story, privacy, text_length, link, nreactions, ncomments, application) " "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) ON DUPLICATE KEY UPDATE type = VALUES(type), story = VALUES(story), privacy= VALUES(privacy), text_length= VALUES(text_length), link= VALUES(link), nreactions= VALUES(nreactions), ncomments = VALUES(ncomments), application = VALUES(application)", post_d_insertion )
                #cur.executemany( "INSERT INTO postb ( id, user_idhash, created_time, type, story, privacy, text_length, link, nreactions, ncomments, application) " "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) ON DUPLICATE KEY UPDATE type = VALUES(type), story = VALUES(story), privacy= VALUES(privacy), text_length= VALUES(text_length), link= VALUES(link), nreactions= VALUES(nreactions), ncomments = VALUES(ncomments), application = VALUES(application)", post_d_insertion )
                cur.executemany("INSERT INTO comment ( id, post_id, user_idhash, created_time, has_picture, has_link, nreactions, ncomments, text_lenght ) " "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s) ON DUPLICATE KEY UPDATE has_picture = VALUES(has_picture), has_link = VALUES(has_link), nreactions = VALUES(nreactions), ncomments = VALUES(ncomments), text_lenght = VALUES(text_lenght)", comment_d_insertion ) 
                #cur.executemany("INSERT INTO commentb ( id, post_id, user_idhash, created_time, has_picture, has_link, nreactions, ncomments, text_lenght ) " "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s) ON DUPLICATE KEY UPDATE has_picture = VALUES(has_picture), has_link = VALUES(has_link), nreactions = VALUES(nreactions), ncomments = VALUES(ncomments), text_lenght = VALUES(text_lenght)", comment_d_insertion ) 
                cur.executemany ("INSERT INTO comment_has_comment ( comment_id, comment_id1 ) " "VALUES (%s, %s) ON DUPLICATE KEY UPDATE comment_id = VALUES(comment_id), comment_id1 = VALUES(comment_id1)", comm_h_comm_insertion)                                        
                cur.executemany("INSERT INTO reaction ( user_idhash, post_id, comment_id, type ) " "VALUES (%s, %s, %s, %s)", reaction_d_insertion)                                                
                #cur.executemany("INSERT INTO reactionb ( user_idhash, post_id, comment_id, type ) " "VALUES (%s, %s, %s, %s)", reaction_d_insertion)                                                
                cur.executemany("INSERT INTO tag ( post_id, comment_id, type, user_idhash, page_id ) " "VALUES (%s, %s, %s, %s, %s)", tag_d_insertion)                            
                #cur.executemany("INSERT INTO tagb ( post_id, comment_id, type, user_idhash, page_id ) " "VALUES (%s, %s, %s, %s, %s)", tag_d_insertion)                            
                cur.executemany("INSERT INTO page ( id, name, category, total_fans ) " "VALUES (%s, %s, %s, %s) ON DUPLICATE KEY UPDATE id = id", page_d_insertion )
                cur.execute ("SET FOREIGN_KEY_CHECKS=1")
                # "free" memory
                del post_d_insertion[:]
                del comment_d_insertion[:]
                del reaction_d_insertion[:]
                del user_d_insertion[:]
                del comm_h_comm_insertion[:]
                del tag_d_insertion[:]
                del page_d_insertion[:]  

# database insertions and queries
def insert_update_in_database ( data, cur, band ):
    #band = ( 'user' OR 'page' )
    column_id = 'idhash'
    if band == 'page':
        column_id = 'id'

    if data <> []:
            #select_statement =  'SELECT ' + column_id + ' FROM ' + band
            #cur.execute(select_statement)
            #result = cur.fetchall()
            #data_in_db = []
            #for row in result:
            #    data_in_db.append(row[0])    
            #data_added = []
            #data_to_add_in_db = []
        if band == 'user':
            for person in data:
            #        if person['idhash'] not in (data_in_db + data_added): # if the id of user not in the db
            #            data_added.append ( person['idhash'] )
                #data_to_add_in_db.append ( ( person['idhash'], person['id'], person['name'] ) )

                cur.execute ( "INSERT INTO user ( idhash, id, name, granted_permissions) "
                "VALUES (%s, %s, %s, %s) ON DUPLICATE KEY UPDATE idhash = idhash", ( person['idhash'], person['id'], person['name'], False ) )
        elif band == 'page':
            for page in data:
                #if page['page_id'] not in (data_in_db + data_added): # if the id of user not in the db
                #data_added.append ( page['page_id'] )
                page_keys = page.keys()
                category = None
                total_fans = None
                if 'category' in page_keys:
                    category = page['category']
                if 'total_fans' in page_keys:
                    total_fans = page['fan_count']
                cur.execute ( "INSERT INTO page ( id, name, category, total_fans) "
            "VALUES (%s, %s, %s, %s) ON DUPLICATE KEY UPDATE category = VALUES ( category ), total_fans = VALUES ( total_fans )", (page['page_id'], page['name'], category, total_fans)  )
                #data_to_add_in_db.append ( ( page['page_id'], page['name'], category, total_fans ) )            
    #return data_to_add_in_db

def get_user_status (uidhash, cur):
    cur.execute ("SELECT status FROM user WHERE idhash = %s ", (uidhash,) )
    result = cur.fetchall()
    if result == ():
        status = None
        return status
    else:
        status = result[0][0]
    return status


def download_data(uid, browser_language, browser_country, device, token, mysql):
    start_time_total = time.time()
    open('statistics.friends', 'w').close()
    statistics = open ('statistics.friends', 'a')
    conn = mysql.connect()
    cur = conn.cursor()

    # facebook api initialization
    start_time = time.time()
    graph = facebook.GraphAPI(access_token=token, timeout=float(60.0), version='2.6')
    end_time = time.time()
    statistics.write( 'Time processing graph api initialization: ' + str(end_time - start_time) + '\n' )

    """ 

    Getting data from Facebook for tables: user, profile, relationship, place, user_has_place, user_with_in_place

    """

    """

    Data for user table

    """
    # get data from facebook
    start_time = time.time()
    profile = graph.get_connections(id=uid, connection_name='?fields=name,birthday,education,gender,hometown,interested_in,languages,location,meeting_for,political,family.limit(500),relationship_status,religion,significant_other,work,friends.limit(500),likes.limit(500){category,name,created_time,fan_count}')
    end_time = time.time()

    statistics.write( 'Time getting profile (from graph API): ' + str(end_time - start_time) + '\n' )
    
    # id and names of current user
    user_id = uid
    user_name = profile['name']
    del profile['name']
    # generate a hash code based on name and pass
    # for non-ascii symbols (e.g accents) -> use unicode _string = u"años luz detrás" -> _string.encode("utf-8")
    uidhash = uid #hashlib.sha1( uid).hexdigest()
    #granted_users = get_granted_users(cur)
    
    current_user_data = (uidhash, user_id, user_name, True)

    cur.execute ("INSERT INTO user ( idhash, id, name, granted_permissions ) "
     "VALUES (%s, %s, %s, %s) ON DUPLICATE KEY UPDATE granted_permissions = VALUES( granted_permissions ) ", current_user_data) 

    user_status = get_user_status( uidhash, cur )
    if user_status == None:
        end_time = time.time()
        statistics.write( 'Time verifying the existence and insertion of current user in DB: ' + str(end_time - start_time) + '\n' )
        """
        Data for relationship table

        """

        family = None
        significant_other = None

        profile_keys = profile.keys()
        if 'family' in profile_keys:
            family = profile['family']
            del profile['family']
        if 'significant_other' in profile_keys:
            significant_other = profile['significant_other']
            del profile['significant_other']

        relationships = data_processing.process_relationship_data ( uidhash, { 'family':family, 'significant_other':significant_other, 'friends':profile['friends'] } )
        del profile['friends']

        insert_update_in_database( relationships['users_to_db'], cur, 'user' )

        relationships_data = []
        for relationship in relationships['users_to_relationship']:
            relationships_data.append ( ( relationship['uidhash'], relationship['idhash'], relationship['relationship_type'], relationship['description'] ) )

        if relationships_data <> []:
            insertion_statement = ("INSERT INTO relationship ( user_idhash, user_idhash1, relationship_type, description ) " "VALUES (%s, %s, %s, %s) ON DUPLICATE KEY UPDATE relationship_type = VALUES(relationship_type), description = VALUES(description)")
            cur.executemany( insertion_statement, relationships_data)
        del relationships_data[:]

        completing_friendships = []
        for user in relationships['users_to_relationship']:
            if user['relationship_type'] == 'friendship':
                cur.execute("Select user_idhash1 from relationship WHERE user_idhash = '%s' " % ( user['idhash'] ) )
                result = cur.fetchall()
                if result <> []:
                    friends_of_friend = []
                    for row in result:
                        friends_of_friend.append(row[0])
                    if uidhash not in friends_of_friend:
                        cur.execute ( 'INSERT INTO relationship (user_idhash, user_idhash1, relationship_type, description) VALUES (%s, %s, %s, %s) ON DUPLICATE KEY UPDATE user_idhash = user_idhash', ( user['idhash'], uidhash, 'friendship', 'friend' )  )
  
        """
        Data for place, user_with_in_place table

        """
        places = data_processing.process_place_data (uidhash, profile) # it returns the list of places for current user 
        places_user_data = places['place_data']
        del places['place_data']
        if places_user_data <> []: 
            insertion_statement = ("INSERT INTO place ( id, type, name, school_type ) " "VALUES (%s, %s, %s, %s) ON DUPLICATE KEY UPDATE id = id")
            cur.executemany (insertion_statement, places_user_data)
        del places_user_data[:]

        user_has_place_data = places['user_has_place']
        del places['user_has_place']
        if user_has_place_data <> []:
            insertion_statement = ("INSERT INTO user_has_place ( user_idhash, place_id ) " "VALUES ( %s, %s ) ON DUPLICATE KEY UPDATE user_idhash = user_idhash")
            cur.executemany (insertion_statement, user_has_place_data)
        del user_has_place_data[:]


        place_details_data = places['user_in_place_details']
        del places['user_in_place_details']
        if place_details_data <> []:
            insertion_statement = ("INSERT INTO user_in_place_details ( user_has_place_user_idhash, user_has_place_place_id, school_concentration, location_id, location_name, position_id, position_name, start_date, end_date ) " "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s) ")
            cur.executemany (insertion_statement, place_details_data)
        del place_details_data[:]

        insert_update_in_database (places['with_data'], cur, 'user')

        user_data = []
        for person in places['with_data']:    
            user_data.append( ( person['idhash'], uidhash, person['place_id'] ) )
        del places['with_data']
        
        if user_data <> []:
            insertion_statement = ("INSERT INTO user_with_in_place ( user_idhash, user_has_place_user_idhash, user_has_place_place_id ) " "VALUES (%s, %s, %s) ON DUPLICATE KEY UPDATE user_idhash = VALUES (user_idhash), user_has_place_user_idhash = VALUES(user_has_place_user_idhash), user_has_place_place_id = VALUES(user_has_place_place_id)")
            cur.executemany (insertion_statement, user_data)
        del user_data[:]

        """
        Data for page, user_likes_page table
        
        """
        
        liked_pages_data = data_processing.process_liked_pages_data (uidhash, profile['likes'], statistics)
        del profile['likes']

        insert_update_in_database (liked_pages_data['liked_pages'], cur, 'page')
        

        user_page_data = []
        for page in liked_pages_data['user_likes_pages']:
            user_page_data.append ( ( uidhash, page ) )
        del liked_pages_data['user_likes_pages']
        insertion_statement = ("INSERT INTO user_likes_page ( user_idhash, page_id ) " "VALUES (%s, %s) ON DUPLICATE KEY UPDATE user_idhash = user_idhash")
        cur.executemany (insertion_statement, user_page_data)        

        del user_page_data[:]
        
        """
        Data for post, reaction, comment, tag, comment_has_comment
        
        """
        start_time = time.time()
        queue   = Queue()

        reader_p = Process( target = process_posts_data, args= ( ( queue, uid, uidhash,  cur, statistics ), )  )
        reader_p.daemon = True
        reader_p.start()

        data = ( queue, statistics, graph, uid )
        pagination( data ) # writer
        
        reader_p.join()
        queue.close()


        end_time = time.time()
        statistics.write( 'Time processing post data: ' + str(end_time - start_time) + '\n' )


        """
        Data for profile table

        """

        user_profile = data_processing.process_profile_data (profile)
        profile_data = []
        profile_data.append ( ( uidhash, user_profile['birthday'], user_profile['gender'], user_profile['hometown_id'], user_profile['hometown_name'], user_profile['location_id'], user_profile['location_name'], user_profile['political'], user_profile['religion'], user_profile['interested_women'], user_profile['interested_men'], user_profile['relationship_status'], user_profile['languages'][0], user_profile['languages'][1], user_profile['languages'][2], user_profile['languages'][3], user_profile['languages'][4], browser_language, browser_country, device ))  
        insertion_statement = ("INSERT INTO profile ( user_idhash, birthday, gender, hometown_id, hometown_name, location_id, location_name, political_view, religion, interested_women, interested_men, relationship_status, language_1, language_2, language_3, language_4, language_5, browser_language, browser_country, device ) " 
        "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) ON DUPLICATE KEY UPDATE hometown_id = VALUES(hometown_id), hometown_name = VALUES(hometown_name), location_id = VALUES(location_id), location_name = VALUES(location_name), political_view = VALUES(political_view), religion = VALUES(religion), interested_women = VALUES(interested_women), interested_men = VALUES(interested_men), relationship_status = VALUES(relationship_status), language_1 = VALUES(language_1), language_2 = VALUES(language_2), language_3 = VALUES(language_3), language_4 = VALUES(language_4), language_5 = VALUES(language_5), browser_language = VALUES(browser_language), browser_country = VALUES(browser_country), device = VALUES(device)")
        cur.executemany( insertion_statement, profile_data)
        del profile_data[:]
        
        cur.execute ("UPDATE user SET status = %s WHERE idhash = %s", ('user_data_downloaded', uidhash))
        """
        Finally, let's commit all the statements
        """
        conn.commit()
        
        end_time_total = time.time()
        statistics.write( 'Total time : ' + str(end_time_total - start_time_total) + '\n' )



def get_friends_for_connectedness(uidhash, mysql, token):
    # database connection
    conn = mysql.connect()
    cur = conn.cursor()
    graph = facebook.GraphAPI(access_token=token, timeout=float(60.0), version='2.6')
    #rows -> po_fbid, po_id, post_owner, friend_fbid, friend_id, friend, total_interaction
    cur.execute("SELECT * FROM interactions_in_posts_summary where po_id = %s", (uidhash,))
    result = cur.fetchall()
    conn.commit()
    total_interaction_values = []
    data = []
    for row in result:
        total_interaction_values.append ( int(row[6]) )
        data.append ( { "fbid":row[3] ,"id":row[4], "name":row[5], "total_interaction":int(row[6])  }  )
    total_interaction_values.sort()
    list_len = len ( total_interaction_values )

    np_total_interaction_values = np.array(total_interaction_values) # input array
    
    median = np.median ( np_total_interaction_values )
    q_2 = median

    total_interaction_values = list (np_total_interaction_values) 
    
    if list_len % 2 <> 0:
        total_interaction_values.remove ( median )
        list_len -=1
    
    half_list_len = list_len/2
    first_half = total_interaction_values[ :half_list_len ]
    second_half = total_interaction_values[ half_list_len: ]

    np_first_half = np.array(first_half)
    q_1 = np.median(np_first_half)
    np_second_half = np.array(second_half)
    q_3 = np.median(np_second_half)
    
    IQR = q_3 - q_1

    q1=[]
    q2=[]
    q3=[]
    q4=[]

    for user in data:
        total_interaction = user["total_interaction"]
        if total_interaction >= q_1 and total_interaction <= q_2:
            q1.append ( user )
        elif total_interaction >= q_2 and total_interaction <= q_3:
            q2.append ( user )
        elif total_interaction >= q_3 and total_interaction <= (q_3 + 1.5*IQR):
            q3.append ( user )
        elif total_interaction >= (q_3 + 1.5*IQR):
            q4.append ( user )
 
    q1_len= len(q1)
    q2_len= len(q2)
    q3_len= len(q3)
    q4_len= len(q4)

    all_users = q1 + q2 + q3 + q4

    random.seed()
    NUMBER_OF_USER_PER_QUARTILE = config.FRIENDS_PER_QUARTILE
    NUMBER_OF_CHOSENS_REQUIRED = config.FRIENDS_TOTAL_NUMBER

    NUMBER_OF_USER_PER_QUARTILE_Q1 = NUMBER_OF_USER_PER_QUARTILE
    NUMBER_OF_USER_PER_QUARTILE_Q2 = NUMBER_OF_USER_PER_QUARTILE
    NUMBER_OF_USER_PER_QUARTILE_Q3 = NUMBER_OF_USER_PER_QUARTILE
    NUMBER_OF_USER_PER_QUARTILE_Q4 = NUMBER_OF_USER_PER_QUARTILE

    if q1_len < NUMBER_OF_USER_PER_QUARTILE:
        NUMBER_OF_USER_PER_QUARTILE_Q1 = q1_len
    if q2_len < NUMBER_OF_USER_PER_QUARTILE:
        NUMBER_OF_USER_PER_QUARTILE_Q2 = q2_len
    if q3_len < NUMBER_OF_USER_PER_QUARTILE:
        NUMBER_OF_USER_PER_QUARTILE_Q3 = q3_len
    if q4_len < NUMBER_OF_USER_PER_QUARTILE:
        NUMBER_OF_USER_PER_QUARTILE_Q4 = q4_len

    rand_user_from_q1 = random.sample ( xrange ( 0, q1_len ), NUMBER_OF_USER_PER_QUARTILE_Q1)
    rand_user_from_q2 = random.sample ( xrange ( q1_len, q1_len + q2_len), NUMBER_OF_USER_PER_QUARTILE_Q2)
    rand_user_from_q3 = random.sample ( xrange ( q1_len + q2_len, q1_len + q2_len + q3_len ), NUMBER_OF_USER_PER_QUARTILE_Q3)
    rand_user_from_q4 = random.sample ( xrange ( q1_len + q2_len + q3_len, q1_len + q2_len + q3_len + q4_len ), NUMBER_OF_USER_PER_QUARTILE_Q4)
    
    total_chosens = NUMBER_OF_USER_PER_QUARTILE_Q1 + NUMBER_OF_USER_PER_QUARTILE_Q2 + NUMBER_OF_USER_PER_QUARTILE_Q3 + NUMBER_OF_USER_PER_QUARTILE_Q4
    rand_user_rest = []
    if total_chosens < NUMBER_OF_CHOSENS_REQUIRED:
        others = [ item for item in range(len(all_users)) if item not in ( rand_user_from_q1 + rand_user_from_q2 + rand_user_from_q3 + rand_user_from_q4 ) ]
        diff = NUMBER_OF_CHOSENS_REQUIRED - total_chosens
        if diff < len(others):
            for ch in reversed(others):
                rand_user_rest.append ( ch )
                diff -= 1
                if diff == 0:
                    break
        else:
            rand_user_rest = others

    chosen_ones = [ ]

    for i in rand_user_from_q1:
        chosen_ones.append ( all_users[ i ] )
    for i in rand_user_from_q2:
        chosen_ones.append ( all_users[ i ] )
    for i in rand_user_from_q3:
        chosen_ones.append ( all_users[ i ] )
    for i in rand_user_from_q4:
        chosen_ones.append ( all_users[ i ] )
    for i in rand_user_rest:
        chosen_ones.append ( all_users[ i ] )

    random.shuffle ( chosen_ones )
    cur.execute ("UPDATE user SET status = %s WHERE idhash = %s", ('connectedness_questions', uidhash))
    conn.commit()
    return chosen_ones



def store_connectedness_data( connectedness_data, uidhash, mysql):
    conn = mysql.connect()
    cur = conn.cursor()
    closer_users = []
    top_ten = []
    users_in_connectedness = connectedness_data

    dict_users = {}
    added_users=[]
    status = get_user_status(uidhash, cur)
    
    for key in users_in_connectedness.keys():
        user_idhash1 = key.split('_')[-1]
        if (user_idhash1 not in added_users) and (user_idhash1 != 'check'):
            added_users.append ( user_idhash1 )
            gender = users_in_connectedness[ 'rg_' + user_idhash1 ]
            
            connectedness = users_in_connectedness[ 'connectedness_' + user_idhash1 ]
            
            online_interaction = users_in_connectedness[ 'interaction_online_' + user_idhash1 ]
            
            f2f_interaction = users_in_connectedness[ 'interaction_face_' + user_idhash1 ]

            if status == 'connectedness_questions':
                cur.execute ("INSERT INTO connectedness (user_idhash, user_idhash1, connectedness_level, f2f_interaction, online_interaction) VALUES (%s, %s, %s, %s, %s)", (uidhash, user_idhash1, connectedness, f2f_interaction, online_interaction ) )
                cur.execute ("INSERT INTO gender_from_survey (user_idhash, gender) VALUES (%s, %s) ON DUPLICATE KEY UPDATE gender = VALUES (gender) ", (user_idhash1, gender) )
            
            dict_users[ connectedness +'_'+ user_idhash1] = user_idhash1

    connectedness_check = users_in_connectedness[ 'connectedness_check' ]
    cur.execute ("INSERT INTO response_validity (user_idhash, connectedness_check) VALUES (%s, %s)", (uidhash, connectedness_check) )

    cur.execute ("UPDATE user SET status = %s WHERE idhash = %s", ('user_connectedness_data_stored', uidhash))
    conn.commit()
    dict_users_keys = dict_users.keys()
    dict_users_keys.sort() 
    limit = 10
    for user_conn_key in reversed(dict_users_keys):
        top_ten.append ( dict_users[user_conn_key] )
        limit -= 1
        if limit == 0:
            break
    top_ten_temp =[]
    for user in top_ten:
        cur.execute ("SELECT id, name FROM user WHERE idhash = %s", (user,))
        result = cur.fetchall()
        user_fbid = result[0][0]
        user_name = result[0][1]
        top_ten_temp.append( {"fbid":user_fbid, "id":user, "name":user_name } )
        
    top_ten = top_ten_temp
    
    return top_ten

def insert_common_points_data(commonpoints_data, uidhash, mysql):
    channels = {}
    relationships = []
    relationships_update = []
    common_aspects = []
    common_aspect_update = []
    conn = mysql.connect()
    cur = conn.cursor()
    survey_data_keys = commonpoints_data.keys()
    
    status = get_user_status (uidhash, cur)
    if status == 'user_connectedness_data_stored':
        for key in survey_data_keys:
            ids = key.split('_')
            user_idhash1 = ids[-1]
            data_id = ids[0] 
            if data_id == "trait":
                cur.execute ( "INSERT INTO trait (user_idhash, user_idhash1, trait) VALUES (%s, %s, %s)", (uidhash, user_idhash1, commonpoints_data[key] ) )
            if data_id == 'cbr':
                try:
                    cur.execute("INSERT INTO relationship_from_survey (user_idhash, user_idhash1, relationship_type, description) VALUES (%s, %s, %s, %s)", ( uidhash, user_idhash1, ids[1], commonpoints_data[key] ) )
                except:
                    pass

            if data_id == 'cba':
                try:
                    cur.execute ( "INSERT INTO common_aspect (user_idhash, user_idhash1, type, description) VALUES (%s, %s, %s, %s)", ( uidhash, user_idhash1, ids[1], commonpoints_data[key] ) )
                except:                   
                    pass

        common_check = commonpoints_data[ 'common_check' ]
        cur.execute ("UPDATE response_validity SET common_check = %s WHERE uidhash = %s", (common_check, uidhash))

        cur.execute ("UPDATE user SET status = %s WHERE idhash = %s", ('finished', uidhash))
        conn.commit()

def insert_credit_data(credit_data, uidhash, mysql):
    #channels = {}
    #relationships = []
    #relationships_update = []
    #common_aspects = []
    #common_aspect_update = []
    conn = mysql.connect()
    cur = conn.cursor()
    #survey_data_keys = commonpoints_data.keys()

    #process credit_data from form
    sona_id = credit_data['sona_id']
    first_name = credit_data['first_name']
    last_name = credit_data['last_name']

    # do we need to check status?
    status = get_user_status (uidhash, cur)
    #if status == 'user_connectedness_data_stored':
    # insert, add indent if status check is needed
    try:
        cur.execute ( "INSERT INTO credit_data (sona_id, first_name, last_name) VALUES (%s, %s, %s)", (sona_id, first_name, last_name) )
        print 'insert to db'
    except:
        pass

    #commit
    conn.commit()

def get_best_friends (uidhash, mysql):
    conn = mysql.connect()
    cur = conn.cursor()
    cur.execute("SELECT friend_fbid, friend_id, friend, total_interaction, po_fbid, post_owner FROM interactions_in_posts_summary where po_id = %s ORDER BY total_interaction DESC limit 10", (uidhash,))
    result = cur.fetchall()
    top_ten = []
    
    for row in result:
        top_ten.append ( { "fbid": row[0], "id":row[1], "name":row[2], "interaction": row[3], "pfbid": row[4], "pname": row[5] } )
    
    return top_ten