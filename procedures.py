# coding=utf-8
import facebook, collections, hashlib, data_processing
import sys
import time

reload(sys)  
sys.setdefaultencoding('utf8')

NO = 0
YES = 1

# database insertions and queries
def verify_existence_in_database ( data, cur, band ):
    #band = ( 'user' OR 'page' )
    column_id = 'idhash'
    if band == 'page':
        column_id = 'id'
    data_to_add_in_db = []
    if data <> []:
        select_statement =  'SELECT ' + column_id + ' FROM ' + band
        cur.execute(select_statement)
        result = cur.fetchall()
        data_in_db = []
        for row in result:
            data_in_db.append(row[0])    
        data_added = []
        data_to_add_in_db = []
        if band == 'user':
            for person in data:
                if person['idhash'] not in (data_in_db + data_added): # if the id of user not in the db
                    data_added.append ( person['idhash'] )
                    data_to_add_in_db.append ( ( person['idhash'], person['id'], person['name'] ) )            
        elif band == 'page':
            for page in data:
                if page['page_id'] not in (data_in_db + data_added): # if the id of user not in the db
                    data_added.append ( page['page_id'] )
                    page_keys = page.keys()
                    category = None
                    total_fans = None
                    if 'category' in page_keys:
                        category = page['category']
                    if 'total_fans' in page_keys:
                        total_fans = page['fan_count']
                    data_to_add_in_db.append ( ( page['page_id'], page['name'], category, total_fans ) )            
    return data_to_add_in_db

def get_granted_users(cur):
    cur.execute("SELECT user_idhash from profile")
    result = cur.fetchall()
    granted_users = []
    for row in result:
        granted_users.append(row[0])
    return granted_users

def proof(uid, token, mysql):
    open('statistics.friends', 'w').close()
    statistics = open ('statistics.friends', 'a')
    # database connection
    conn = mysql.connect()
    cur = conn.cursor()
    
    # facebook api initialization
    start_time = time.time()
    graph = facebook.GraphAPI(access_token=token, timeout=float(60.0), version='2.6')
    end_time = time.time()
    statistics.write( 'Time processing graph api initialization: ' + str(end_time - start_time) + '\n' )

    """
    FROM dev.mysql.com

    syntaxcursor.execute(operation, params=None, multi=False)

    insert_stmt = (
      "INSERT INTO employees (emp_no, first_name, last_name, hire_date) "
      "VALUES (%s, %s, %s, %s)"
    )
    data = (2, 'Jane', 'Doe', datetime.date(2012, 3, 23))
    cursor.execute(insert_stmt, data)

    select_stmt = "SELECT * FROM employees WHERE emp_no = %(emp_no)s"
    cursor.execute(select_stmt, { 'emp_no': 2 })


    syntax: cursor.executemany(operation, seq_of_params)

    data = [
      ('Jane', date(2005, 2, 12)),
      ('Joe', date(2006, 5, 23)),
      ('John', date(2010, 10, 3)),
    ]
    stmt = "INSERT INTO employees (first_name, hire_date) VALUES (%s, %s)"
    cursor.executemany(stmt, data)

    """

    """ 

    Getting data from Facebook for tables: user, profile, relationship, place, user_has_place, user_with_in_place

    """

    """

    Data for user table

    """
    # get data from facebook
    start_time = time.time()
    profile = graph.get_connections(id=uid, connection_name='?fields=name,birthday,education,gender,hometown,interested_in,languages,location,meeting_for,political,family.limit(5000),relationship_status,religion,significant_other,work,friends.limit(5000),likes.limit(5000){category,name,created_time,fan_count}')
    end_time = time.time()

    statistics.write( 'Time processing get profile (from graph API): ' + str(end_time - start_time) + '\n' )
    
    # id and names of current user
    user_id = uid
    user_name = profile['name']
    del profile['name']
    # generate a hash code based on name and pass
    # for non-ascii symbols (e.g accents) -> use unicode _string = u"años luz detrás" -> _string.encode("utf-8")
    uidhash = hashlib.sha1(user_name.encode("utf-8") + uid).hexdigest()

    # prepare user data for insertion into db
    user_data = [(uidhash, user_id, user_name)]
    person_to_add = [{'idhash':uidhash, 'id':user_id, 'name':user_name}]

    
    # carry at bottom
    # verify if user exists in db
    start_time = time.time()
    person_to_add = verify_existence_in_database (person_to_add, cur, 'user')
    
    if person_to_add <> []:
        insertion_statement = ("INSERT INTO user ( idhash, id, name ) " "VALUES (%s, %s, %s)")    
        cur.executemany( insertion_statement, user_data)
    
    end_time = time.time()
    statistics.write( 'Time verifying the existence and insertion of current user in DB: ' + str(end_time - start_time) + '\n' )
    """
    Data for relationship table

    """
    granted_users = get_granted_users (cur)
    if uidhash not in granted_users:
        family = None
        significant_other = None

        profile_keys = profile.keys()
        if 'family' in profile_keys:
            family = profile['family']
            del profile['family']
        if 'significant_other' in profile_keys:
            significant_other = profile['significant_other']
            del profile['significant_other']

        # get data from facebook
#        start_time = time.time()
        #friends = profile #graph.get_connections (id=uid, connection_name= '?fields=friends.limit(5000)')
#        end_time = time.time()
#        statistics.write( 'Time processing get friends: ' + str(end_time - start_time) + '\n' )
        
        start_time = time.time()
        relationships = data_processing.process_relationship_data ( uidhash, { 'family':family, 'significant_other':significant_other, 'friends':profile['friends'] } )
        del profile['friends']
#        end_time = time.time()
#        statistics.write( 'Time processing relationship data: ' + str(end_time - start_time) + '\n' )        
        # { 'users_to_db':users_to_db, 'users_to_relationship':users_to_relationship }
        user_data = verify_existence_in_database( relationships['users_to_db'], cur, 'user' )
        if user_data <> []:
            insertion_statement = ("INSERT INTO user ( idhash, id, name ) " "VALUES (%s, %s, %s) ON DUPLICATE KEY UPDATE idhash = idhash")
            cur.executemany( insertion_statement, user_data)

        #start_time = time.time()
        relationships_data = []
        for relationship in relationships['users_to_relationship']:
            relationships_data.append ( ( relationship['uidhash'], relationship['idhash'], relationship['relationship_type'], relationship['description'] ) )
        if relationships_data <> []:
            insertion_statement = ("INSERT INTO relationship ( user_idhash, user_idhash1, relationship_type, description ) " "VALUES (%s, %s, %s, %s) ON DUPLICATE KEY UPDATE relationship_type = VALUES(relationship_type), description = VALUES(description)")
            cur.executemany( insertion_statement, relationships_data)

        for user in relationships['users_to_relationship']:
            if user['relationship_type'] == 'friendship':
                cur.execute("Select user_idhash1 from relationship WHERE user_idhash = '%s' " % ( user['idhash'] ) )
                result = cur.fetchall()
                if result <> []:
                    friends_of_friend = []
                    for row in result:
                        friends_of_friend.append(row[0])
                    if uidhash not in friends_of_friend:
                        cur.execute('INSERT INTO relationship (user_idhash, user_idhash1, relationship_type, description) VALUES (%s, %s, %s, %s) ON DUPLICATE KEY UPDATE user_idhash = user_idhash', (user['idhash'], uidhash, 'friendship', 'friend') )
        end_time = time.time()
        statistics.write( 'Time processing and inserting relationship data: ' + str(end_time - start_time) + '\n' )        
    """
    Data for place, user_with_in_place table

    """
    start_time = time.time()
    places = data_processing.process_place_data (uidhash, profile) # it returns the list of places for current user 
    user_data = places['place_data']
    if user_data <> []: 
        insertion_statement = ("INSERT INTO place ( id, type, name, school_type ) " "VALUES (%s, %s, %s, %s) ON DUPLICATE KEY UPDATE id = id")
        cur.executemany (insertion_statement, user_data)

    user_data = places['user_has_place']
    if user_data <> []:
        insertion_statement = ("INSERT INTO user_has_place ( user_idhash, place_id ) " "VALUES ( %s, %s ) ON DUPLICATE KEY UPDATE user_idhash = user_idhash")
        cur.executemany (insertion_statement, user_data)

#    granted_users = get_granted_users (cur)
#granted_users was calculated above
    if uidhash not in granted_users:
        user_data = places['user_in_place_details']
        if user_data <> []:
            insertion_statement = ("INSERT INTO user_in_place_details ( user_has_place_user_idhash, user_has_place_place_id, school_concentration, location_id, location_name, position_id, position_name, start_date, end_date ) " "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s) ")
            cur.executemany (insertion_statement, user_data)

    user_data = []
    user_data = verify_existence_in_database (places['with_data'], cur, 'user')
    if user_data <> []:
        insertion_statement = ("INSERT INTO user ( idhash, id, name ) " "VALUES (%s, %s, %s)")
        cur.executemany (insertion_statement, user_data)

    user_data = []
    for person in places['with_data']:    
        user_data.append( ( person['idhash'], uidhash, person['place_id'] ) )
    
    if user_data <> []:
        insertion_statement = ("INSERT INTO user_with_in_place ( user_idhash, user_has_place_user_idhash, user_has_place_place_id ) " "VALUES (%s, %s, %s) ON DUPLICATE KEY UPDATE user_idhash = VALUES (user_idhash), user_has_place_user_idhash = VALUES(user_has_place_user_idhash), user_has_place_place_id = VALUES(user_has_place_place_id)")
        cur.executemany (insertion_statement, user_data)
    end_time = time.time()
    statistics.write( 'Time processing and inserting place data: ' + str(end_time - start_time) + '\n' )
    """
    Data for page, user_likes_page table
    
    """
    start_time = time.time()
    ##liked_pages = profile #graph.get_connections (id= uid, connection_name= '?fields=likes.limit(5000){category,name,created_time,fan_count}')
    
    liked_pages_data = data_processing.process_liked_pages_data (uidhash, profile['likes'], statistics)
    del profile['likes']

    #{'liked_pages':liked_pages['data'], 'user_likes_pages':user_likes_pages}
    pages_to_add = verify_existence_in_database (liked_pages_data['liked_pages'], cur, 'page')
    if pages_to_add <> []:
        insertion_statement = ("INSERT INTO page ( id, name, category, total_fans ) VALUES (%s, %s, %s, %s) ON DUPLICATE KEY UPDATE total_fans = VALUES(total_fans)")
        cur.executemany (insertion_statement, pages_to_add)    

    user_page_data = []
    for page in liked_pages_data['user_likes_pages']:
        user_page_data.append ( ( uidhash, page ) )
    del liked_pages_data['user_likes_pages']
    insertion_statement = ("INSERT INTO user_likes_page ( user_idhash, page_id ) " "VALUES (%s, %s) ON DUPLICATE KEY UPDATE user_idhash = user_idhash")
    cur.executemany (insertion_statement, user_page_data)        
    end_time = time.time()
    statistics.write( 'Time processing and inserting likes data: ' + str(end_time - start_time) + '\n' )
    
    """
    Data for post, reaction, comment, tag, comment_has_comment
    
    """
    start_time = time.time()
    try:
        posts = graph.get_connections (id=uid, connection_name = '?fields=posts.limit(5000){created_time,type,story,story_tags,privacy,message,link,application,shares,from,reactions.summary(true).limit(5000),comments.summary(true).limit(5000){created_time,from,message,attachment,message_tags,likes.summary(true).limit(5000),comments.summary(true).limit(5000){created_time,from,message,attachment,message_tags,likes.summary(true).limit(5000)}}}')
    except:
        posts = graph.get_connections (id=uid, connection_name = '?fields=posts.limit(5000){created_time,type,story,story_tags,privacy,message,link,application,shares,from,reactions.summary(true).limit(5000),comments.summary(true).limit(5000){created_time,from,message,attachment,message_tags,likes.summary(true).limit(5000)}}')
        pass
    end_time = time.time()
    statistics.write( 'Time processing get post data (from GraphAPI): ' + str(end_time - start_time) + '\n' )

    start_time = time.time()
    posts_all_data = data_processing.process_posts_data (uid, uidhash, posts, statistics)
    end_time = time.time()
    statistics.write( 'Time processing post data: ' + str(end_time - start_time) + '\n' )
    """
    Add users in db

    """
    start_time = time.time()
    # {'posts_data', 'comments_data', 'comment_has_comment', 'reactions_data', 'story_tags', 'message_tags'}
    user_data = []
    users_in_posts = list(posts_all_data['comments_data']) + list(posts_all_data['reactions_data']) + list(posts_all_data['story_tags_users']) + list(posts_all_data['message_tags_users'])
    #user_data += verify_existence_in_database (users_in_posts, cur, 'user')
    for user in users_in_posts:
        user_data.append ( ( user['idhash'], user['id'], user['name'] ) )
    
    # user_data += verify_existence_in_database (posts_all_data['reactions_data'], cur, 'user')
    # user_data += verify_existence_in_database (posts_all_data['story_tags_users'], cur, 'user')
    # user_data += verify_existence_in_database (posts_all_data['message_tags_users'], cur, 'user')
    user_data = list(set(user_data)) #remove duplicates
    #if user_data <> []:
    insertion_statement = ("INSERT INTO user ( idhash, id, name ) " "VALUES (%s, %s, %s) ON DUPLICATE KEY UPDATE idhash = idhash")
    cur.executemany (insertion_statement, user_data)
    end_time = time.time()
    statistics.write( 'Time verifying and inserting of users in comments, reactions, tags: ' + str(end_time - start_time) + '\n' )
    """
    Add pages in db
    """
    start_time = time.time()
    page_data = []
    pages_in_posts = list(posts_all_data['story_tags_pages']) + list(posts_all_data['message_tags_pages'])
    page_data += verify_existence_in_database (pages_in_posts, cur, 'page')
#   page_data += verify_existence_in_database (pages_in_posts, cur, 'page')
    page_data = list(set(page_data)) #remove duplicates
    if page_data <> []:
        insertion_statement = ("INSERT INTO page ( id, name, category, total_fans ) " "VALUES (%s, %s, %s, %s) ON DUPLICATE KEY UPDATE id = id")
        cur.executemany (insertion_statement, page_data)
    end_time = time.time()
    statistics.write( 'Time inserting pages: ' + str(end_time - start_time) + '\n' )
    """
    post
    """
    start_time = time.time()
    data_posts =[]
    # ('post_id':post['id'], 'idhash':uidhash, 'created_time':post['created_time'], 'post_type':post['type'], 'story':post_story, 'privacy':post['privacy']['description'], 'text_length':post_message_lenght, 'link':post['link'], 'nreactions':post['reactions']['summary']['total_count'], 'ncomments':post['comments']['summary']['total_count'], 'application':post_app, 'shares_count':post_shares_count, 'language':post_message_language)
    for post in posts_all_data['posts_data']:
        data_posts.append ( ( post['post_id'], post['idhash'],post['created_time'], post['post_type'], post['story'], post['privacy'], post['text_length'], post['link'], post['nreactions'], post['ncomments'], post['application'], post['shares_count'], post['language'] ) )
    del posts_all_data['posts_data']
    if data_posts <> []:
        insertion_statement = ("INSERT INTO post ( id, user_idhash, created_time, type, story, privacy, text_length, link, nreactions, ncomments, application, shares_count, language ) " "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) ON DUPLICATE KEY UPDATE type = VALUES(type), story = VALUES(story), privacy= VALUES(privacy), text_length= VALUES(text_length), link= VALUES(link), nreactions= VALUES(nreactions), ncomments = VALUES(ncomments), application = VALUES(application), shares_count = VALUES(shares_count), language = VALUES(language)")
        cur.executemany (insertion_statement, data_posts)
    end_time = time.time()
    statistics.write( 'Time inserting posts: ' + str(end_time - start_time) + '\n' )
    """
    comment
    """
    start_time = time.time()
    data_comments = []
    # { 'post_id':post['id'] , 'comment_id':comment['id'] ,'created_time':comment['created_time'], 'id':comment['from']['id'], 'name':comment['from']['name'], 'idhash':idhash, 'language':message_language, 'text_length':message_length, 'has_picture':has_picture, 'has_link':has_link, 'nreactions':comment['likes']['summary']['total_count'], 'ncomments':comment['comments']['summary']['total_count'] }
    for comment in posts_all_data['comments_data']:
        if comment['idhash'] == 'from does not exist': # if there not exists owner of message add "default" value: the id of current user
            comment['idhash'] = uidhash
        data_comments.append ( ( comment['comment_id'], comment['post_id'], comment['idhash'], comment['created_time'], comment['language'], comment['has_picture'], comment['has_link'], comment['nreactions'], comment['ncomments'], comment['text_length'] ) )
    del posts_all_data['comments_data']
    if data_comments <> []:
        insertion_statement = ("INSERT INTO comment ( id, post_id, user_idhash, created_time, language, has_picture, has_link, nreactions, ncomments, text_lenght ) " "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s) ON DUPLICATE KEY UPDATE has_picture = VALUES(has_picture), has_link = VALUES(has_link), nreactions = VALUES(nreactions), ncomments = VALUES(ncomments), text_lenght = VALUES(text_lenght)")
        cur.executemany (insertion_statement, data_comments)
    end_time = time.time()
    statistics.write( 'Time inserting comments: ' + str(end_time - start_time) + '\n' )
    """
    comment_has_comment
    """
    start_time = time.time()
    data_comm_has_comm = []
    # { 'comment_id':comment['id'], 'comment_id1':inner_comment['id'] }
    for comm_comm in posts_all_data['comment_has_comment']:
        data_comm_has_comm.append ( ( comm_comm['comment_id'], comm_comm['comment_id1'] ) )
    del posts_all_data['comment_has_comment']
    if data_comm_has_comm <> []:
        insertion_statement = ("INSERT INTO comment_has_comment ( comment_id, comment_id1 ) " "VALUES (%s, %s) ON DUPLICATE KEY UPDATE comment_id = VALUES(comment_id), comment_id1 = VALUES(comment_id1)")
        cur.executemany (insertion_statement, data_comm_has_comm) 
    end_time = time.time()
    statistics.write( 'Time inserting comment_has_comment: ' + str(end_time - start_time) + '\n' )
    """
    reaction
    """
    start_time = time.time()
    granted_users #= get_granted_users (cur)
    if uidhash not in granted_users:
        data_reactions = []
        # { 'post_id':post['id'], 'comment_id':None, 'type': reaction['type'], 'id':reaction['id'], 'name':reaction['name'], 'idhash':idhash}
        for reaction in posts_all_data['reactions_data']:
            data_reactions.append ( ( reaction['idhash'], reaction['post_id'], reaction['comment_id'], reaction['type'] ) )
        del posts_all_data['reactions_data']
        if data_reactions <> []:
            insertion_statement = ("INSERT INTO reaction ( user_idhash, post_id, comment_id, type ) " "VALUES (%s, %s, %s, %s)")
            cur.executemany (insertion_statement, data_reactions) 
    end_time = time.time()
    statistics.write( 'Time inserting reactions: ' + str(end_time - start_time) + '\n' )
    """
    tag
    """
    start_time = time.time()
    granted_users #= get_granted_users (cur)
    if uidhash not in granted_users:
        data_tags = []
        # {'post_id':post['id'], 'comment_id':None , 'idhash':idhash, 'id':story_tag['id'], 'name':story_tag['name'], 'type':story_tag['type']}
        for tag in (posts_all_data['story_tags_users'] + posts_all_data['story_tags_pages'] + posts_all_data['message_tags_users'] + posts_all_data['message_tags_pages']):
            data_tags.append ( ( tag['post_id'], tag['comment_id'], tag['type'], tag['idhash'], tag['page_id']  ) )
        
        del posts_all_data['story_tags_users']
        del posts_all_data['story_tags_pages']
        del posts_all_data['message_tags_users']
        del posts_all_data['message_tags_pages']

        if data_tags <> []:
            insertion_statement = ("INSERT INTO tag ( post_id, comment_id, type, user_idhash, page_id ) " "VALUES (%s, %s, %s, %s, %s)")
            cur.executemany (insertion_statement, data_tags) 
    end_time = time.time()
    statistics.write( 'Time inserting tags: ' + str(end_time - start_time) + '\n' )

    """
    Data for profile table

    """
    start_time = time.time()
    user_profile = data_processing.process_profile_data (profile)
    profile_data = []
    profile_data.append ( ( uidhash, user_profile['birthday'], user_profile['gender'], user_profile['hometown_id'], user_profile['hometown_name'], user_profile['location_id'], user_profile['location_name'], user_profile['political'], user_profile['religion'], user_profile['interested_women'], user_profile['interested_men'], user_profile['relationship_status'], user_profile['languages'][0], user_profile['languages'][1], user_profile['languages'][2], user_profile['languages'][3], user_profile['languages'][4] ))
    insertion_statement = ("INSERT INTO profile ( user_idhash, birthday, gender, hometown_id, hometown_name, location_id, location_name, political_view, religion, interested_women, interested_men, relationship_status, language_1, language_2, language_3, language_4, language_5 ) " 
    "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) ON DUPLICATE KEY UPDATE hometown_id = VALUES(hometown_id), hometown_name = VALUES(hometown_name), location_id = VALUES(location_id), location_name = VALUES(location_name), political_view = VALUES(political_view), religion = VALUES(religion), interested_women = VALUES(interested_women), interested_men = VALUES(interested_men), relationship_status = VALUES(relationship_status), language_1 = VALUES(language_1), language_2 = VALUES(language_2), language_3 = VALUES(language_3), language_4 = VALUES(language_4), language_5 = VALUES(language_5)")
    cur.executemany( insertion_statement, profile_data)
    end_time = time.time()
    statistics.write( 'Time inserting profile data: ' + str(end_time - start_time) + '\n' )
    """
    Finally, let's commit all the statements
    """

    start_time = time.time()
    conn.commit()
    end_time = time.time()
    statistics.write( 'Time processing commit: ' + str(end_time - start_time) + '\n' )
    

    

def counter(uid, token):
    graph = facebook.GraphAPI(access_token=token, version='2.6')
    response = graph.get_connections(id=uid, connection_name='invitable_friends')
    invitable_friends = pagination2(response['data'])
    len(invitable_friends)


