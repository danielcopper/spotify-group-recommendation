import spotify_api


def sendit(sp, group_playlist, username):
    for sp, user_id in zip(sp, username):
        playlist = sp.user_playlist_create(user=user_id, name="mixr", public=True,
                                           collaborative=False,
                                           description="Trapaholics! Damn, son! Where did you find this?")
        playlist_id = playlist["id"]
        print(playlist_id)
        upload = sp.user_playlist_add_tracks(user=user_id, playlist_id=playlist_id, tracks=group_playlist,
                                             position=0)
    return "done"



