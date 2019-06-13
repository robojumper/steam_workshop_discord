#!/usr/bin/env python

import json
from pprint import pprint
import requests
import datetime
import re
from operator import attrgetter
import calendar
import sys
import hashlib

keyobj = json.load(open('config.txt'))
key = keyobj["webkey"]
query_url = "https://api.steampowered.com/IPublishedFileService/QueryFiles/v1/?key=%s" % (key)
getplayersumm_url = "https://api.steampowered.com/ISteamUser/GetPlayerSummaries/v2/?key=%s" % (key)
post_url  = "https://api.steampowered.com/ISteamRemoteStorage/GetPublishedFileDetails/v1/"
built_query_url = "%s&format=%s&query_type=%i&page=%i&numperpage=%i&creator_appid=%i&appid=%s&filetype=%i" % (query_url, "json", 1, 1, 10, 0, "%i", 0)

handled_mods = dict()


def keyhash(s):
    return hashlib.sha1(s).hexdigest()

try:
    with open('known_mods', 'a+') as f:
        try:
            handled_mods = dict(json.load(f))
        except Exception as e:
            handled_mods = dict()

        for key in keyobj["webhooks"]:
            if not keyhash(key) in handled_mods:
                handled_mods[keyhash(key)] = list()
except EnvironmentError as e:
    print(e)
    sys.exit(1)

"""Returns the latest 10 mods for the given consumer app id."""
def get_latest_mods(app_id):
    mod_arr = []
    try:
        r = requests.get(built_query_url % (app_id))
        if r.status_code == 200:
            response = json.loads(r.text)
            mod_arr = response["response"]["publishedfiledetails"]
            return map(lambda x: int(x["publishedfileid"]), mod_arr)
    except requests.exceptions.RequestException as e:
        print(e)
        return []

"""Returns the lastest 10 mods for every consumer app id."""
def get_all_latest_mods():
    mod_arr = []
    ids = set()
    for k, v in keyobj["webhooks"].iteritems():
        for id in v:
            ids.add(id)

    for id in ids:
        mod_arr.extend(get_latest_mods(id))

    return mod_arr

"""Filters the latest 10 mods by removing ones present in already_handled_mods. If it is empty, return an empty list"""
def determine_mods_to_post():
    global handled_mods
    new_mods = get_all_latest_mods()
    everywhere_posted_mods = set(new_mods)
    # We need to build the intersection of all our known mods in order to find the ones we need to post
    # Excepting empty sets, they become initialized with the mods
    for key in keyobj["webhooks"]:
        h = keyhash(key)
        if not handled_mods[h]:
            handled_mods[h] = list(new_mods)
        else:
            everywhere_posted_mods = everywhere_posted_mods & set(handled_mods[h])

    new_mods = list(set(new_mods) - everywhere_posted_mods)
    return new_mods

def post_mod(m, u):
    global handled_mods
    e = {}
    wk_obj = {'embeds': [ {} ] }
    e["title"] = "%s" % (m["title"])
    e["type"] = "rich"
    e["url"] = "http://steamcommunity.com/sharedfiles/filedetails/?id=%i" % (int(m["publishedfileid"]))
    e["description"] = re.sub("[\(\[].*?[\)\]]", '' , m["description"][:200].replace("\r\n", " ")) + '\\u2026'.decode('unicode-escape')
    e["color"] = 3447003
    e["timestamp"] = datetime.datetime.fromtimestamp(m["time_created"]).isoformat()

    e["author"] = {}
    e["author"]["name"] = u["personaname"]
    e["author"]["url"] = u["profileurl"]
    e["author"]["proxy_icon_url"] = u["profileurl"]
    e["author"]["icon_url"] = u["avatar"]

    e["thumbnail"] = {}
    e["thumbnail"]["url"] = m["preview_url"]
    e["thumbnail"]["proxy_url"] = u["profileurl"]
    e["thumbnail"]["height"] = 84
    e["thumbnail"]["width"] = 84

    wk_obj["embeds"][0] = e
    headers = {'Content-type': 'application/json'}
    for key, ids in keyobj["webhooks"].iteritems():
        h = keyhash(key)
        if not int(m["publishedfileid"]) in handled_mods[h]:
            if int(m["consumer_app_id"]) in ids:
                try:
                    r = requests.post(key, data=json.dumps(wk_obj), headers=headers)
                    if r.status_code == 204:
                        handled_mods[h].append(int(m["publishedfileid"]))
                except requests.exceptions.RequestException as e:
                    print(e)
            else:
                handled_mods[h].append(int(m["publishedfileid"]))

def get_users(l):
    user_list = ",".join(l)
    built_get = "%s&steamids=%s" % (getplayersumm_url, user_list)
    try:
        r = requests.get(built_get)
        if r.status_code == 200:
            response = json.loads(r.text)
            p = response["response"]["players"]
            players = {}
            for pl in p:
                players[pl["steamid"]] = pl
            return players
    except requests.exceptions.RequestException as e:
        print(e)

    return []


def post_new_mods():
    mod_ids = determine_mods_to_post()
    if len(mod_ids) > 0:
        data = {'key': key, 'itemcount': len(mod_ids)}
        for idx, i in enumerate(mod_ids):
            data["publishedfileids[%i]" % (idx)] = i
        try:
            i = requests.post(post_url, data=data)
            if i.status_code == 200:
                response = json.loads(i.text)["response"]
                if response["result"] == 1:
                    sorted_mods = sorted(response["publishedfiledetails"], key=lambda f: f["time_created"])
                    users = get_users(map(lambda x: x["creator"], sorted_mods))
                    for m in sorted_mods:
                        post_mod(m, users[m["creator"]])
        except requests.exceptions.RequestException as e:
            print(e)

post_new_mods()

try:
    with open('known_mods', 'w+') as f:
        json.dump(handled_mods, f)
except EnvironmentError as e:
    print(e)
    sys.exit(1)

print("[%s] Success!" % (datetime.datetime.now().isoformat()))
sys.exit(0)

