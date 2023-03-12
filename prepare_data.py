__author__ = 'Numan Tok'


import pandas as pd
from sklearn.preprocessing import MinMaxScaler
import time


class IsufficientUserData(Exception):
    "Raised when there is insufficient user data."
    pass


class DataPreparation:
    """Handles the data retrieval and preparation needed for the graph model.

    Attributes:
        selected_features (list(strings)): Audio features that should be used 
            in the model.
        users (list(<class 'spotipy.client.Spotify'>)): A list that includes a 
            spotify client for each user/group member.
        max_playlists_per_user (int): How many library saved playlists should 
            be retrieved per user. Must be between 1 and 50.
        min_universe_size (int): The desired minimal track universe size.

    """

    def __init__(self, selected_features, users, max_playlists_per_user=50, min_universe_size=1000) -> None:
        self.selected_features = selected_features
        self.users = users
        self.max_playlists_per_user = max_playlists_per_user
        self.min_universe_size = min_universe_size
        self.track_universe = self.prepare_track_universe()
        self.custom_users_playlists = self.prepare_user_playlists()
        self.users_top_tracks = self.prepare_users_top_tracks()
        self.normalize_data()

    def normalize_data(self):
        """Normalizes all track data with a MinMaxScaler.

        A MinMaxScaler is fitted on self.track_universe for the features given in self.selected_features which then transforms self.track_universe, self.custom_users_playlists and self.users_top_tracks.

        """

        # Fit scaler to self.track_universe and use this scale for every data
        scaler = MinMaxScaler()
        scaler.fit(self.track_universe.iloc[:, 1:])

        # Scale self.track_universe
        track_universe_id_col = self.track_universe.iloc[:, 0]
        track_universe_scaled = pd.DataFrame(scaler.transform(
            self.track_universe.iloc[:, 1:]))
        self.track_universe = pd.concat(
            [track_universe_id_col, track_universe_scaled], axis=1)

        # Scale self.custom_users_playlists
        custom_users_playlists_id_col = [
            [playlist.iloc[:, 0]
             for playlist in user_playlists]
            for user_playlists in self.custom_users_playlists
        ]
        custom_users_playlist_scaled = [
            [pd.DataFrame(scaler.transform(playlist.iloc[:, 1:]))
             for playlist in user_playlists]
            for user_playlists in self.custom_users_playlists
        ]
        self.custom_users_playlists = [
            [pd.concat([
                custom_users_playlists_id_col[user_j][playlist_i],
                custom_users_playlist_scaled[user_j][playlist_i]
            ], axis=1)
                for playlist_i in range(len(self.custom_users_playlists[user_j]))]
            for user_j in range(len(self.custom_users_playlists))
        ]

        # Scale self.users_top_tracks
        users_top_tracks_id_col = self.users_top_tracks.iloc[:, 0]
        users_top_tracks_scaled = pd.DataFrame(
            scaler.transform(self.users_top_tracks.iloc[:, 1:]))
        self.users_top_tracks = pd.concat(
            [users_top_tracks_id_col, users_top_tracks_scaled], axis=1)

    def retrieve_audio_features(self, tracks):
        """Retrieves a selection of audio features for tracks.

        For each track given in tracks the audio features are retrieved from 
        the spotify API and stored in a pandas DataFrame together with the 
        track ID.

        Args:
            tracks (dict): A dictionary including track information returned by 
            the spotify API. 

        Returns:
            A pandas DataFrame including values of type float64 for the columns 
            'id' and self.selected_features.

        """

        # Get all track IDs
        track_ids = [track['track']['id']
                     for track in tracks if track['track'] is not None]

        # Split track IDs into chunks of 100 (maximum allowed by the endpoint)
        track_id_chunks = [track_ids[i:i+100]
                           for i in range(0, len(track_ids), 100)]

        # Get the audio features of all tracks in each chunk
        audio_features_chunks = []
        for chunk in track_id_chunks:
            audio_features = self.users[0]._get(
                'audio-features', ids=','.join(chunk))
            audio_features_chunks.append(audio_features)

        # Combine audio features from all chunks into a single list
        audio_features = [
            item for chunk in audio_features_chunks for item in chunk['audio_features']]

        # Filter out None values
        while None in audio_features:
            track_ids.remove(track_ids[audio_features.index(None)])
            audio_features.remove(None)

        # Filter the audio features by self.selected_features
        selected_audio_features = [{
            key: track_features[key] for key in self.selected_features}
            for track_features in audio_features if track_features]

        # Create a DataFrame with columns 'id' and all self.audio_features
        df = pd.DataFrame(
            {'id': track_ids, **{key: [feature[key] for feature in
                                       selected_audio_features] for key in self.selected_features}},
            dtype='float64')

        return df

    def custom_audio_features_playlists(self, playlists):
        """Get a custom playlists representation with audio features.

        Loop through each playlist and retrieve its tracks and their audio 
        features. The playlists include the track IDs and audio features.

        Args:
            playlists (list(dict())): A list of dictionaries including playlist 
            data returned by the spotify API.

        Returns:
            A list of pandas DataFrames including values of type float64 for 
            the columns 'id' and self.selected_features each representing one 
            playlist.

        """

        custom_playlists = []

        for playlist in playlists:
            # Retrieve playlist tracks
            results = self.users[0].playlist_tracks(playlist['id'])
            tracks = results['items']

            while results['next']:
                results = self.users[0].next(results)
                tracks.extend(results['items'])

            if len(tracks) > 0:
                custom_playlists.append(self.retrieve_audio_features(tracks))

            # Filter out empty playlists
            custom_playlists = [
                df for df in custom_playlists if not df.empty]

        return custom_playlists

    def prepare_user_playlists(self):
        """Retrieve the necessary playlist data for each user. 

        Up to self.max_playlists_per_user playlists that a user has saved in 
        their library are retrieved for each user and then prepared with self.
        custom_audio_features_playlists().

        Returns:
            A list including a list for each user that includes pandas 
            DataFrames including values of type float64 for the columns 
            'id' and self.selected_features each representing one playlist.
        """

        users_playlists = [sp_client.current_user_playlists(
            limit=self.max_playlists_per_user) for sp_client in self.users]
        custom_users_playlists = []

        for user in users_playlists:
            custom_playlists = self.custom_audio_features_playlists(
                user['items'])
            if len(custom_playlists) > 0:
                custom_users_playlists.append(custom_playlists)

        # If no user has playlists raise Error
        if custom_users_playlists == []:
            raise IsufficientUserData

        return custom_users_playlists

    def prepare_track_universe(self, limit=50):
        """Prepares a pool of tracks to select from.

        Args:
            limit (int): Specifies how many featured playlists are to be 
                retrieved per call of the Spotify API function 
                featured_playlists().

        Returns:
            A pandas DataFrame including values of type float64 for the columns 
            'id' and self.selected_features representing the pool of tracks to 
            select from (aka track universe).

        """

        all_tracks = []
        all_track_ids = set()
        current_track_count = 0
        offset = 0
        delay = limit * 0  # set to 0 because this method seems to not work
        time_at_last_call = time.time()-delay
        while True:
            before_loop_track_count = current_track_count

            # Use delay to avoid hitting API limits
            time_since_last_call = time.time() - time_at_last_call
            time_at_last_call = time.time()
            time.sleep(max(0, delay-time_since_last_call))

            # Get random playlists available in spotify
            featured_playlists = self.users[0].featured_playlists(
                country='DE', limit=limit, offset=offset)
            playlist_ids = [item['id'] for item in
                            featured_playlists['playlists']['items'] if item is
                            not None]

            # Collect all available tracks
            for playlist_id in playlist_ids:
                results = self.users[0].playlist_tracks(playlist_id, limit=50)
                tracks = [track
                          for track in results['items'] if track['track'] is
                          not None]
                while results['next']:
                    results = self.users[0].next(results)
                    tracks.extend(
                        [track for track in results['items'] if track['track']
                         is not None])

                # Add unique tracks to all_tracks and all_track_ids
                for track in tracks:
                    if track['track']['id'] not in all_track_ids:
                        all_tracks.append(track)
                        all_track_ids.add(track['track']['id'])
                        current_track_count += 1

            # Stop if we have enough tracks or if no tracks were added
            if current_track_count >= self.min_universe_size or \
                    current_track_count == before_loop_track_count:
                break
            offset += limit

        all_tracks = self.retrieve_audio_features(all_tracks)

        return all_tracks

    def prepare_users_top_tracks(self, tracks_per_user=3):
        """Prepares the top tracks of all users.

        Args:
            tracks_per_user (int): Specifies how many top tracks are to be 
                retrieved per user.

        Returns:
            A pandas DataFrame including values of type float64 for the columns 
            'id' and self.selected_features representing the top tracks of all 
            users.

        """

        # Add top tracks from all users/group members
        top_tracks = []
        for sp_client in self.users:
            try:
                tracks = sp_client.current_user_top_tracks(
                    limit=tracks_per_user, time_range='long_term')
                if not None in tracks and tracks is not None:
                    tracks = tracks['items'][:tracks_per_user]
                    tracks = [i for i in tracks if i is not None]
                top_tracks.extend(tracks)
            except:
                continue

        # If no user has top tracks raise Error
        if top_tracks == []:
            raise IsufficientUserData

        top_tracks = [{'track': {'id': track['id']}}
                      for track in top_tracks]
        top_tracks = self.retrieve_audio_features(top_tracks)

        return top_tracks
