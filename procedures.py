import facebook, requests, collections, csv, json

uidt="1420945151265179"
tokent="EAACEdEose0cBACL6y095WhdEu18w0DHfjlrU9KZBAD1na1d1ZCuZAxYZBoSZBuIdZBJvLG9MWh0NmAy129bTkMMXCFLa1SJS2VPj8bAxRtYUbeXLm5QXcXsiYRrs70Wd3pfXkCuZAP2NfYk7T9vodRI1HQTiAkZARooFkgZAEEglZCOQZDZD"
app_secrett='a6b94f66589e9f9a7d558cda0e83a3dd'
app_idt='1733963700184652'
NO = 0
YES = 1


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

def proof(uid, token):
    tlist=[]
    graph = facebook.GraphAPI(access_token=token, version='2.6')
    
    fusers = open("database/users.txt")
    users = json.load(fusers)
    fusers.close
    
    
    fprofiles = open("database/profiles.txt")
    profiles = json.load(fprofiles)
    fprofiles.close


    profile = graph.get_object(id=uid, fields= 'name,birthday,education,gender,hometown,interested_in,languages,location,meeting_for,political,relationship_status,religion,significant_other,work')
    
    #todo: leer el archivo (el dictionario almacenado) y agregar el nuevo usuario
    users[uid] = profile['name']
    del profile['name']
    profiles[uid] = profile

    
    fusers = open("database/users.txt", 'w')
    fprofiles = open("database/profiles.txt", 'w')
    json.dump(users, fusers)
    json.dump(profiles, fprofiles)

    fusers.close
    fprofiles.close


    
    #todo read the friend file, verify if the uid user have already a friend
    ffriends = open("database/friends.txt")
    friends = json.load(ffriends)
    ffriends.close


    ufriends = graph.get_connections (id=uid, connection_name= '?fields=friends{id}')

    for key in friends:
        if key in ufriends['friends']['data']:
            friends[key].append(uid)



    friends[uid] = ufriends['friends']['data']

    ffriends = open("database/friends.txt", 'w')
    json.dump(friends, ffriends)

    ffriends.close


    flikes = open("database/likes.txt")
    likes = json.load(flikes)
    flikes.close

    ulikes = graph.get_connections (id= uid, connection_name= '?fields=likes{category,name,created_time}')

    likes[uid] = ulikes['likes']['data']

    flikes = open("database/likes.txt", 'w')
    json.dump(likes, flikes)

    flikes.close



    posts = graph.get_connections (id=uid, connection_name = '?fields=posts{created_time,from,reactions,comments{created_time,from,message,message_tags,likes,comments{created_time,from,message,message_tags,likes}}}')
    
    #correct posts['data'] , at this moment I'm adding a new element to the dict (date: 18-06)
    posts['data'] = pagination (posts['posts'])
    try: 
        for post in posts['data']:
            try:
                reactions = pagination(post['reactions'])
                post['reactions']['data'] = reactions
            except KeyError:
                pass

            try:
                comments = pagination(post['comments'])
                post['comments']['data'] = comments
                for comment in post['comments']['data']:
                    try:
                        likesincomm = pagination(comment['likes'])
                        comment['likes']['data'] = likesincomm
                    except KeyError:
                        pass
                        try:
                            commentsincomm = pagination(comment['comments'])
                            comment['comments']['data'] = commentsincomm
                            for comment2 in comment['comments']['data']:
                                try:
                                    likesincomm2 = pagination(comment2['likes'])
                                    comment2['likes']['data'] =  likesincomm2
                                except KeyError:
                                    pass
                        except KeyError:
                            pass
            except KeyError:
                pass   
    except KeyError:
        pass


    uposts = {}
    uposts[uid] = posts['data']

    newfile = "database/connections/" + uid + ".txt"
    fposts = open(newfile, 'w')    
    json.dump(uposts, fposts)

    fposts.close


def counter(uid, token):
    graph = facebook.GraphAPI(access_token=token, version='2.6')
    response = graph.get_connections(id=uid, connection_name='invitable_friends') 
    invitable_friends = pagination2(response['data'])
    len(invitable_friends)
    




    





























# def proof(uid, token):
#     graph = facebook.GraphAPI(access_token=token, version='2.6')
#     likesA = graph.get_connections(id=uid, connection_name='likes')
#     friends = graph.get_connections(id=uid, connection_name='?fields=friends{likes,name}')

#     alllikesA = pagination(likesA)
#     #allfriends = pagination(friends,YES)
#     likesxfriend={}
#     alllikesB = {}
#     friends = friends['friends']['data']
    
#     for friend in friends:
#         try:
#             alllikesB = pagination(friend['likes'])
#         except KeyError:
#             pass

#         #graph.get_connections(id=friend , connection_name='likes') 
#         #alllikesB = pagination(likesB)
#         likesxfriend.update({friend['name'] : set(alllikesB.values()).intersection(alllikesA.values())})
#         alllikesB = {}
    
#     print likesxfriend

#proof(uidt, tokent)

