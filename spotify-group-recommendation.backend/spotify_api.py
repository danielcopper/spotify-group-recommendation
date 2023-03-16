__author__ = 'Numan Tok, Krystof Belak'


import spotipy
from spotipy.oauth2 import SpotifyOAuth
import spotipy.util as util
import main

def authorize(tokens):
    sp = []
    username = []
    print(tokens)
    for token in tokens:
        sp_obj = spotipy.Spotify(auth=token)
        sp.append(sp_obj)
        username.append(sp_obj.current_user()["id"])
        print(username)
    return sp, username

