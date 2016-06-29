# coding=utf-8
import hashlib, langdetect, json, requests

"""

Processing data for the insertion into DB

"""

def pagination(data):
    alldata = []
    while(True):
        try:
            for item in data['data']:
                alldata.append(item)
            data=requests.get(data['paging']['next']).json()
        except KeyError:
            break
    return alldata

def process_comment_data (post, comment, comment_keys, comments_data, message_tags_users, message_tags_pages, reactions_data):    
    if len(comment_keys) > 1: # just do if there more than the comment id
        try: #if 'likes' in comment_keys:
            comment_likes_total_count = comment['likes']['summary']['total_count']
            if comment_likes_total_count > 0:
                for like in comment['likes']['data']:
                    idhash = hashlib.sha1(like['name'].encode("utf-8") + like['id']).hexdigest()
                    reactions_data.append( { 'post_id':post['id'], 'comment_id':comment['id'], 'type': 'LIKE', 'id':like['id'], 'name':like['name'], 'idhash':idhash} )
        except KeyError:
            comment_likes_total_count = None
        has_picture = False
        has_link = False
        try: #if 'attachment' in comment_keys:
            if comment['attachment']['type'] == 'photo':  
                has_picture = True
            if comment['attachment']['type'] == 'share':
                has_link = True
        except KeyError:
            pass
        if 'message' in comment_keys:
            message_length = len(comment['message'])
            if message_length > 0:
                try:
                    message_language = langdetect.detect(comment['message'])
                except:
                    message_language = None
                    pass
            else:
                message_language = None
        else:
            message_length = None
            message_language = None
        try: #if 'message_tags' in comment_keys:
            for message_tag in comment['message_tags']:
                if message_tag['type'] == 'user':
                    idhash = hashlib.sha1(message_tag['name'].encode("utf-8") + message_tag['id']).hexdigest()
                    message_tags_users.append({'post_id':post['id'], 'comment_id':comment['id'],'idhash':idhash, 'id':message_tag['id'], 'name':message_tag['name'], 'type':message_tag['type'], 'page_id':None})
                elif message_tag['type'] == 'page':
                    message_tags_pages.append({'post_id':post['id'], 'comment_id':comment['id'],'idhash':None, 'id':None, 'name':message_tag['name'], 'type':message_tag['type'], 'page_id':message_tag['id']})               
        except KeyError:
            pass
        try:
            comment_summary_total_count = comment['comments']['summary']['total_count'] # for the most inner comment I don't retriever the inner comments related (leaf)
        except:
            comment_summary_total_count = None
        try: #if 'from' in comment_keys:
            comment_from_id = comment['from']['id']
            comment_from_name = comment['from']['name'] 
            idhash = hashlib.sha1( comment['from']['name'].encode("utf-8") + comment['from']['id']).hexdigest()
        except KeyError: #else:
            comment_from_id = 'from does not exist' 
            comment_from_name = 'from does not exist'
            idhash = 'from does not exist'
        if 'created_time' in comment_keys:
            created_time = comment['created_time']
        else:
            created_time = None
        comments_data.append( { 'post_id':post['id'] , 'comment_id':comment['id'] ,'created_time':created_time, 'id':comment_from_id, 'name':comment_from_name, 'idhash':idhash, 'language':message_language, 'text_length':message_length, 'has_picture':has_picture, 'has_link':has_link, 'nreactions':comment_likes_total_count, 'ncomments':comment_summary_total_count } )

def process_place_data ( uidhash, profile ) :
    place_data = []
    user_in_place_details = []
    user_has_place = []
    with_data = []
    try:
        place_type = 'education'
        for edu_place in profile['education']:
            edu_keys = edu_place.keys()
            place_id = edu_place['school']['id']
            place_name = edu_place['school']['name']
            school_type = edu_place['type']

            try: #if 'concentration' in edu_keys:
                for concentration in edu_place['concentration']:
                    school_concentration = concentration['name']
                    break
            except KeyError: #else:
                school_concentration = 'not specified'
            try: #if 'year' in edu_keys:
                end_date = edu_place['year']['name'] + '-01-01'
            except KeyError: #else:
                end_date = None

            #place tuple (id,type,name,school_type)
            place_data.append ( (place_id, place_type, place_name, school_type))
            #( uidhash, place_id, school_concentration,location_id,location_name,position_id,position_name,start_date,end_date)
            user_in_place_details.append (( uidhash, place_id, school_concentration, 'not apply', 'not apply', 'not apply', 'not apply', '1000-01-01', end_date ))
            user_has_place.append ( ( uidhash, place_id ) )
            if 'with' in edu_keys:
                for person in edu_place['with']:
                    person['place_id'] = place_id
                    idhash = hashlib.sha1(person['name'].encode("utf-8") + person['id']).hexdigest()
                    person['idhash'] = idhash
                with_data += edu_place['with']
        del profile['education'] # delete the processed data
    except KeyError:
        pass

    try:
        place_type = 'work'
        for work_place in profile['work']:
            work_keys = work_place.keys()
            place_id = work_place['employer']['id']
            place_name = work_place['employer']['name']

            try: #if 'location' in work_keys:
                place_location_id = work_place['location']['id']
                place_location_name = work_place['location']['name']
            except KeyError: # else:
                place_location_id = None
                place_location_name = None

            try: #if 'position' in work_keys:
                place_position_id = work_place['position']['id']
                place_position_name = work_place['position']['name']
            except KeyError: #else:
                place_position_id = 'not specified'
                place_position_name = 'not specified'

            if 'start_date' in work_keys:
                place_start_date = work_place['start_date']
            else:
                place_start_date = None

            if 'end_date' in work_keys:
                place_end_date = work_place['end_date']
            else:
                place_end_date = None
            #(place tuple (id,type,name,school_type,)
            place_data.append ((place_id, place_type, place_name, 'not apply'))
            #(uidhash, place_id,school_concentration,location_id,location_name,position_id,position_name,start_date,end_date)
            user_in_place_details.append ( ( uidhash, place_id, 'not apply',  place_location_id, place_location_name, place_position_id, place_position_name, place_start_date, place_end_date ) )
            user_has_place.append ( ( uidhash, place_id ) )
            if 'projects' in work_keys:
                all_with = []
                try:
                    for project in work_place['projects']:
                        all_with = all_with + project['with']
                except KeyError:
                    pass
                # next line: removing duplicates
                work_with = [dict(user_tuple) for user_tuple in set([tuple(user.items()) for user in all_with])]
                for person in work_with:
                    person['place_id'] = place_id
                    idhash = hashlib.sha1(person['name'].encode("utf-8") + person['id']).hexdigest()
                    person['idhash'] = idhash
                with_data += work_with
        del profile['work'] # delete the processed data
    except KeyError:
        pass
    return {'place_data':place_data, 'with_data':with_data, 'user_in_place_details':user_in_place_details, 'user_has_place':user_has_place}


def process_posts_data(uid, uidhash, posts):
    posts_data = []
    comments_data = []
    comments_inner_comm_data = []
    reactions_data = []
    story_tags_users = []
    story_tags_pages = []
    message_tags_users = []
    message_tags_pages = []
    try:
        posts['data'] = pagination ( posts['posts'] )
        for post in posts['data']:
            try:
                reactions = pagination ( post['reactions'] )
                post['reactions']['data'] = reactions
            except KeyError:
                pass
            try:
                comments = pagination ( post['comments'] )
                post['comments']['data'] = comments
                for comment in post['comments']['data']:
                    try:
                        likesincomm = pagination( comment['likes'] )
                        comment['likes']['data'] = likesincomm
                    except KeyError:
                        pass
                    try:
                        commentsincomm = pagination ( comment['comments'] )
                        comment['comments']['data'] = commentsincomm
                        for comment2 in comment['comments']['data']:
                            try:
                                likesincomm2 = pagination( comment2['likes'] )
                                comment2['likes']['data'] =  likesincomm2
                            except KeyError:
                                pass
                    except KeyError:
                        pass
            except KeyError:
                pass
    except KeyError:
        pass

    for post in posts['data']:
        post_keys = post.keys()
        if 'story' in post_keys:
            post_story = post['story']
        else:
            post_story = None
        if 'story_tags' in post_keys:
            for story_tag in post['story_tags']:
                try: # if there is not type of story_tag don't add
                    if story_tag['type'] == 'user':
                        if story_tag['id'] <> uid:
                            idhash = hashlib.sha1(story_tag['name'].encode("utf-8") + story_tag['id']).hexdigest()
                            story_tags_users.append({'post_id':post['id'], 'comment_id':None , 'idhash':idhash, 'id':story_tag['id'], 'name':story_tag['name'], 'type':story_tag['type'], 'page_id':None})
                    elif story_tag['type'] == 'page':
                        story_tags_pages.append({'post_id':post['id'], 'comment_id':None , 'idhash':None, 'id':None, 'name':story_tag['name'], 'type':story_tag['type'], 'page_id':story_tag['id']})
                except KeyError:
                    pass
        #else story_tag still empty
        if 'message' in post_keys:
            post_message_lenght = len(post['message'])
            if post_message_lenght > 0:
                try:
                    post_message_language = langdetect.detect(post['message'])
                except:
                    post_message_language = None
                    pass
            else:
                post_message_language= None
        else:
            post_message_lenght = None
            post_message_language = None
        try:
            post_shares_count = post['shares']['count']
        except KeyError:
            post_shares_count = None
        try:
            post_app = post['application']['name']
        except:
            post_app = None
        try:
            post_link = post['link']
        except:
            post_link = None
        if 'reactions' in post_keys:
            try:
                post_reactions_summary_total_count = post['reactions']['summary']['total_count']
                if post_reactions_summary_total_count > 0:
                    for reaction in post['reactions']['data']:
                        try:
                            idhash = hashlib.sha1(reaction['name'].encode("utf-8") + reaction['id']).hexdigest()
                            reactions_data.append( { 'post_id':post['id'], 'comment_id':None, 'type': reaction['type'], 'id':reaction['id'], 'name':reaction['name'], 'idhash':idhash} )
                        except KeyError:
                            pass
            except KeyError:
                post_reactions_summary_total_count = None
                pass
        if 'comments' in post_keys:
            try:
                post_comments_summary_total_count = post['reactions']['summary']['total_count']
                if post_comments_summary_total_count > 0:
                    for comment in post['comments']['data']:
                        try:
                            comment_keys = comment.keys()
                            process_comment_data ( post, comment, comment_keys, comments_data, message_tags_users, message_tags_pages, reactions_data)
                            if 'comments' in comment_keys:
                                for inner_comment in comment['comments']['data']:
                                    inner_comment_keys = inner_comment.keys()
                                    process_comment_data ( post, inner_comment, inner_comment_keys, comments_data, message_tags_users, message_tags_pages, reactions_data )
                                    comments_inner_comm_data.append ({ 'comment_id':comment['id'], 'comment_id1':inner_comment['id'] })
                        except KeyError:
                            pass
            except KeyError:
                post_comments_summary_total_count = None
                pass
        if 'created_time' in post_keys:
            created_time = post['created_time']
        else:
            created_time = None
        posts_data.append ( { 'post_id':post['id'], 'idhash':uidhash, 'created_time':created_time, 'post_type':post['type'], 'story':post_story, 'privacy':post['privacy']['description'], 'text_length':post_message_lenght, 'link':post_link, 'nreactions':post_reactions_summary_total_count, 'ncomments':post_comments_summary_total_count, 'application':post_app, 'shares_count':post_shares_count, 'language':post_message_language } )
        #unique = [] # remove the post with the same id. Facebook have posts that have the same ID!!!!
        # for i in range(len(posts_data)):
        #     if posts_data[i]['post_id'] in unique:
        #         posts_data.pop(i)
        #     else:
        #         unique.append (posts_data[i]['post_id'])
    return {'posts_data':posts_data, 'comments_data':comments_data, 'comment_has_comment':comments_inner_comm_data, 'reactions_data':reactions_data, 'story_tags_users':story_tags_users, 'story_tags_pages':story_tags_pages, 'message_tags_users': message_tags_users, 'message_tags_pages': message_tags_pages}

def process_profile_data (profile):
    profile_data = {}
    profile_keys = profile.keys()
    if 'birthday' in profile_keys:
        profile_data['birthday'] = profile['birthday']
    else:
        profile_data['birthday'] = None
    if 'gender' in profile_keys:
        profile_data['gender'] = profile['gender'][0]
    else:
        profile_data['gender'] = None
    try: #if 'hometown' in profile_keys:
        profile_data['hometown_id'] = profile['hometown']['id']
        profile_data['hometown_name'] = profile['hometown']['name']
    except KeyError: #else:
        profile_data['hometown_id'] = None
        profile_data['hometown_name'] = None
    try: #if 'location' in profile_keys:
        profile_data['location_id'] = profile['location']['id']
        profile_data['location_name'] = profile['location']['name']
    except KeyError: #else:
        profile_data['location_id'] = None
        profile_data['location_name'] = None
    profile_data['interested_women'] = False 
    profile_data['interested_men'] = False
    if 'interested_in' in profile_keys:
        for interest in profile['interested_in']:
            if interest == 'female':
                profile_data['interested_women'] = True
            elif interest == 'men':
                profile_data['interested_men'] = True
    if 'relationship_status' in profile_keys:
        profile_data['relationship_status'] = profile['relationship_status']
    else:
        profile_data['relationship_status'] = None
    if 'religion' in profile_keys:
        profile_data['religion'] = profile['religion']
    else:
        profile_data['religion'] = None
    if 'political' in profile_keys:
        profile_data['political'] = profile['political']
    else:
        profile_data['political'] = None
    profile_data['languages'] = [None, None, None, None, None]
    try: #if 'languages' in profile_keys:
        for i in range(len(profile['languages'])):
            profile_data['languages'][i] = profile['languages'][i]['name']
    except KeyError:
        pass
    return profile_data

#( { 'family':family, 'significant_other':significant_other, 'friends':friends } )
def process_relationship_data ( uidhash, data ) :
    family = {'data':[]}
    friends = {'data':[]}
    if data['family'] <> None:
        family['data'] = pagination (data['family'])
    try:
        if len(data['friends']['data']) > 0:
            friends['data'] = pagination (data['friends'])
    except:
        pass

    significant_other =  data['significant_other']
    all_users = family['data'] + friends['data'] 
    if significant_other <> None:
        significant_other['type']='significant_other'
        all_users.append(significant_other)

    users_to_db = []
    users_to_relationship = []
    if all_users <> []:
        for user in all_users:
            idhash = hashlib.sha1(user['name'].encode("utf-8") + user['id']).hexdigest()
            users_to_db.append ({ 'idhash':idhash, 'id':user['id'], 'name':user['name']} )
            user_keys = user.keys()
            if 'relationship' in user_keys:
                users_to_relationship.append ( { 'uidhash':uidhash, 'idhash':idhash, 'relationship_type':'family', 'description':user['relationship'] } )
            elif 'type' in user_keys:
                users_to_relationship.append ( { 'uidhash':uidhash, 'idhash':idhash, 'relationship_type':'romantic', 'description':'significant_other' } )
            else:
                users_to_relationship.append ( { 'uidhash':uidhash, 'idhash':idhash, 'relationship_type':'friendship', 'description':'friend' } )
    return { 'users_to_db':users_to_db, 'users_to_relationship':users_to_relationship }

def process_liked_pages_data (uidhash, data):
    liked_pages = pagination(data)
    user_likes_pages = []
    for page in liked_pages:
        page['page_id'] = page['id']
        del page['id']
        user_likes_pages.append ( page['page_id'])

    return {'liked_pages':liked_pages, 'user_likes_pages':user_likes_pages}
