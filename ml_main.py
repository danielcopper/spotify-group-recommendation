__author__ = 'Numan Tok'


from spotify_api import sp
from prepare_data import DataPreparation
from graph import GraphModel
from requests.exceptions import ReadTimeout
import time


###########################################################################
# ! Avoid !:
# -- num_tracks_to_find >= len(track_universe)
# -- len(start_tracks) >= num_tracks_to_find
# -- max_playlists_per_user > 50
###########################################################################
# Example usage:

clients = [sp]
num_tracks_to_find = 50
selected_features = ['danceability', 'energy',
                     'key', 'loudness', 'mode', 'speechiness', 'acousticness', 'instrumentalness', 'liveness', 'valence', 'tempo', 'duration_ms', 'time_signature']

# handle timeout error and retry until retry_time_seconds is over
retry_time_seconds = 60
try_until = time.time() + retry_time_seconds
while time.time() < try_until:
    try:
        data = DataPreparation(
            selected_features=selected_features,
            users=clients,
            max_playlists_per_user=50,  # max 50
            min_universe_size=1000)

        users_playlists = data.custom_users_playlists
        track_universe = data.track_universe
        start_tracks = data.users_top_tracks
        break
    except ReadTimeout:
        continue

graph_model = GraphModel(users_playlists, track_universe,
                         num_tracks_to_find, start_tracks)
group_playlist_ids = graph_model.find_group_playlist()
print('-'*50)
print('-'*50)
print("Group Playlist (Track IDs):")
print()
print(group_playlist_ids)
print('-'*50)
print('-'*50)


# Create Playlist in Spotify
for client in clients:
    user_name = client.current_user()["id"]
    group_playlist = client.user_playlist_create(
        user=user_name, name="Group Playlist :)", public=False)
    client.user_playlist_add_tracks(
        user=user_name, playlist_id=group_playlist["id"], tracks=group_playlist_ids)
