# coding=utf-8
import config
import hashlib, langdetect, json, requests, time
from multiprocessing import Pool, Manager
from functools import partial

"""

Processing data for the insertion into DB

"""
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
                    idhash = person['id'] #hashlib.sha1( person['id']).hexdigest()
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
                    idhash = person['id'] #hashlib.sha1(person['id']).hexdigest()
                    person['idhash'] = idhash
                with_data += work_with
        del profile['work'] # delete the processed data
    except KeyError:
        pass
    return {'place_data':place_data, 'with_data':with_data, 'user_in_place_details':user_in_place_details, 'user_has_place':user_has_place}



    
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
            if interest == 'men':
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
        family['data'] = data['family']['data']
    try:
        if len(data['friends']['data']) > 0:
            friends['data'] = data['friends']['data']
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
            idhash = user['id'] #hashlib.sha1( user['id']).hexdigest()
            users_to_db.append ({ 'idhash':idhash, 'id':user['id'], 'name':user['name']} )
            user_keys = user.keys()
            if 'relationship' in user_keys:
                users_to_relationship.append ( { 'uidhash':uidhash, 'idhash':idhash, 'relationship_type':'family', 'description':user['relationship'] } )
            elif 'type' in user_keys:
                users_to_relationship.append ( { 'uidhash':uidhash, 'idhash':idhash, 'relationship_type':'romantic', 'description':'significant_other' } )
            else:
                users_to_relationship.append ( { 'uidhash':uidhash, 'idhash':idhash, 'relationship_type':'friendship', 'description':'friend' } )
    return { 'users_to_db':users_to_db, 'users_to_relationship':users_to_relationship }


def process_liked_pages_data (uidhash, data, statistics):
    liked_pages = data['data']
    user_likes_pages = []
    for page in liked_pages:
        page['page_id'] = page['id']
        del page['id']
        user_likes_pages.append ( page['page_id'])

    return {'liked_pages':liked_pages, 'user_likes_pages':user_likes_pages}
