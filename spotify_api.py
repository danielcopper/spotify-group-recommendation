__author__ = 'Numan Tok'


import spotipy
from spotipy.oauth2 import SpotifyOAuth


# Set the Spotify API scope and redirect URI
scope = 'user-library-read, user-read-email, playlist-read-private, user-top-read, playlist-modify-private'
redirect_uri = 'http://localhost:8888/callback'


# Set the client ID and client secret
with open('client_id.txt', 'r') as file:
    client_id = file.read().rstrip()
with open('client_secret.txt', 'r') as file:
    client_secret = file.read().rstrip()

# Set up the authorization flow
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
    client_id=client_id,
    client_secret=client_secret,
    redirect_uri=redirect_uri,
    scope=scope,
    requests_timeout=10))
