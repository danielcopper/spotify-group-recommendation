__author__ = 'Numan Tok'


import numpy as np


class GraphModel:
    """Graph model that finds a group playlist.

    Based on the existing playlists of all group members a weight 
    vector for the audio features of the tracks is calculated. Then for a given 
    list of starting points a sub-playlist (aka path) is created for each, 
    which together form the group playlist. The weight vector is used to 
    successively find the best next track (aka point in the graph) for the 
    sub-playlists. 

    Attributes:
        users_playlists (list(list(pandas.core.frame.DataFrame(float64)))): 
            Includes all retrieved playlists (with tracks) of all users in a 
            DataFrame with 'id' and  the audio features as columns.
        selectable_tracks (pandas.core.frame.DataFrame(float64)): The pool of 
            tracks to select from (aka track universe) with 'id' and  the audio 
            features as columns.
        num_tracks_to_find (int): The desired group playlist length.
        start_points (pandas.core.frame.DataFrame(float64)): Top tracks of all 
            users with 'id' and  the audio features as columns.

    """

    def __init__(self, users_playlists, selectable_tracks, num_tracks_to_find,
                 start_points) -> None:
        self.users_playlists = users_playlists
        self.selectable_tracks = selectable_tracks
        self.num_tracks_to_find = num_tracks_to_find
        self.start_points = start_points
        self.num_features = len(
            self.selectable_tracks.columns) - 1  # -1 for the id
        self.num_selectable_tracks = len(
            self.selectable_tracks.index)  # number of rows
        self.feature_weights = self.calc_feature_weights()

    def calc_feature_weights(self):
        """Calculate a feature weight vector from the user playlists. 

        Depending on the differences between the features of each pair of 
        consecutive tracks from the user playlists, feature importances are 
        calculated. A lower difference is interpreted as a higher importance. 
        More important features get a higher weight.

        Returns:
            A numpy ndarray of size self.num_features including a weighting 
            factor (float) for each feature.

        """

        overall_distances = np.zeros(self.num_features)
        for user in self.users_playlists:
            for playlist in user:
                for i in range(len(playlist.index)-1):
                    # Get 2 consecutive tracks
                    current_track_features = playlist.iloc[[i]].drop(
                        columns=['id'], axis=1).values[0]
                    next_track_features = playlist.iloc[[
                        i+1]].drop(columns=['id'], axis=1).values[0]
                    # Calculate the distances between 2 tracks and add them up
                    dist_to_next_track = np.absolute(
                        next_track_features - current_track_features)
                    overall_distances += dist_to_next_track

        dist_sum = np.sum(overall_distances)
        dist_weights = overall_distances / dist_sum
        feature_weights = 1 / dist_weights

        return feature_weights

    def find_group_playlist(self):
        """Creates a list of track IDs.

        The output list should form the group playlist. The list consists of 
        the best sub-playlists in terms of weighted feature distances where 
        each sub-playlist is created with one of the starting tracks in self.
        start_points. The sub-playlists have almost the same length and are 
        concatenated in the order of the starting tracks.

        Returns:
            A list including a number of self.num_tracks_to_find track IDs 
            (strings).

        """

        # Determine the number of tracks to find for each starting point
        num_paths = len(self.start_points)
        tracks_per_path = [self.num_tracks_to_find // num_paths]*num_paths
        for i in range(self.num_tracks_to_find % num_paths):
            tracks_per_path[i] += 1

        # For each starting point, find an own path through the graph
        # (=playlist part) and connect them together
        paths = []
        for i in range(num_paths):
            start_point = self.start_points.iloc[[i]]
            path_lenght = tracks_per_path[i]
            path_i = self.find_path(start_point, path_lenght)
            paths.extend(path_i)

        return paths

    def find_path(self, start_point, path_length):
        """Finds a path of length path_length that starts with start_point.

        Successively adds the next nearest point (compared to the last added 
        point) to the path until the desired length is reached. The nearest 
        point is the one with the smallest weighted feature distance.

        Args:
            start_point (pandas.core.frame.DataFrame(float64)): A track that 
                serves as starting point for the path with 'id' and  the audio 
                features as columns.
            path_length (int): Length of the path.

        Returns:
            A list including a number of path_length track IDs (strings).

        """

        path = [start_point['id'].values[0]]
        current_point = start_point
        current_point_feature_vec = current_point.iloc[:, 1:].to_numpy()

        for i in range(path_length-1):
            # Calculate the weighted feature distances between the last added
            # point/track and all other points/tracks
            neighbor_features = self.selectable_tracks.iloc[:, 1:].to_numpy()
            neighbor_feature_distances = \
                neighbor_features - current_point_feature_vec
            weighted_neighbor_feature_distances = \
                neighbor_feature_distances*self.feature_weights
            neighbor_distance_vec = np.sum(
                weighted_neighbor_feature_distances, axis=0)

            # Find the nearest point and add it to the path
            nearest_point_idx = np.argmin(neighbor_distance_vec)
            nearest_point = self.selectable_tracks.iloc[[nearest_point_idx]]
            nearest_point_id = nearest_point['id'].values[0]
            path.append(nearest_point_id)

            # Update the current point and delete it from the selectable_tracks
            current_point_feature_vec = nearest_point.iloc[:, 1:].to_numpy()
            self.selectable_tracks = self.selectable_tracks.drop(
                index=nearest_point_idx).reset_index(drop=True)

        return path
