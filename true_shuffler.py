#!/usr/bin/env python
from __future__ import annotations

import json
import os
import random

import spotipy
from spotipy.oauth2 import SpotifyOAuth

SpotifyUser = str
TrackID = str
PlaylistID = str


class TrueShuffler:
    def __init__(self, credentials_dir: str, alias: None | str = None):
        # store the alias for easy recognition later
        self.alias = alias

        # read our credentials
        with open(os.path.join(credentials_dir, "credentials.json")) as f:
            self.credentials = json.loads(f.read())

        # the handler
        self.spotify = spotipy.Spotify(
            auth_manager=SpotifyOAuth(
                client_id=self.credentials["id"],
                client_secret=self.credentials["secret"],
                cache_handler=spotipy.CacheFileHandler(
                    cache_path=os.path.join(credentials_dir, ".cache")
                ),
                redirect_uri="http://localhost:8888/callback",
                scope="streaming,user-modify-playback-state,user-read-playback-state,user-read-currently-playing,user-library-read",
                open_browser=False,
            )
        )

        # get the playlist ids
        self.playlist_ids: list[PlaylistID] = self.credentials["playlist_ids"]

        # the dictionary of unplayed track ids that we are waiting to add to queue
        self.unplayed_track_ids: dict[PlaylistID, list[TrackID]] = dict()

        # runtime variables
        self.queued_track_id: TrackID = "null"
        self.current_playback = self.spotify.current_playback()

        # printout
        self.update_current_playback()
        all_track_ids = {
            playlist_id: self.get_all_track_ids_from_playlist(playlist_id)
            for playlist_id in self.playlist_ids
        }
        print(
            f"Initialized True Shuffle with {len(all_track_ids)} playlists for {self.alias}, "
            f"totalling {sum([len(v) for _, v in all_track_ids.items()])} tracks."
        )

    def get_all_track_ids_from_playlist(self, playlist_id) -> list[TrackID]:
        # returns all ids in the playlist as a list of strings
        tracks_response = self.spotify.playlist_tracks(playlist_id)
        if not tracks_response:
            print(
                f"Something went wrong when retrieving all tracks for {playlist_id}, the playlist doesn't seem to exist."
            )
            return []

        # iterate through the playlist in chunks to accumulate track ids
        ids = [track["track"]["uri"] for track in tracks_response["items"]]
        while tracks_response := self.spotify.next(tracks_response):
            ids.extend([track["track"]["uri"] for track in tracks_response["items"]])

        return ids

    def update_current_playback(self) -> bool:
        # get the currently playing track
        try:
            self.current_playback = self.spotify.current_playback()
            return True
        except Exception as e:
            print(e)
            return False

    @property
    def is_playing(self) -> bool:
        # no playback info means no track played for awhile
        if self.current_playback is None:
            return False

        # check whether we're really playing
        return self.current_playback.get("is_playing", False)

    @property
    def playback_is_playlist(self) -> bool:
        if self.current_playback is None:
            return False

        return self.current_playlist_id in self.playlist_ids

    @property
    def is_shuffling(self) -> bool:
        if self.current_playback is None:
            return False

        return self.current_playback.get("shuffle_state", False)

    @property
    def current_playlist_id(self) -> PlaylistID | None:
        # make sure we have playback
        if not self.current_playback:
            return None

        # make sure we have context
        if not (context := self.current_playback.get("context")):
            return None

        # make sure we have uri
        if not (uri := context.get("uri")):
            return None

        # return the uri at this point
        return uri.split(":")[-1]

    @property
    def current_track_id(self) -> TrackID | None:
        # make sure we have playback
        if not self.current_playback:
            return None

        # make sure we have item
        if not (item := self.current_playback.get("item")):
            return None

        # make sure we have uri
        if not (uri := item.get("uri")):
            return None

        return uri

    def check_add_queue(self) -> None:
        try:
            queue = self.spotify.queue()
        except Exception as e:
            queue = None
            print(e)

        # something went wrong here
        if not queue:
            return

        # get the first 5 uris for songs in the current queue
        queued_uris = [track["uri"] for track in queue["queue"][:5]]

        # if the most recently queued track is inside the queue just exit for now
        if self.queued_track_id in queued_uris:
            print(f"Queued track already in queue for {self.alias}, skipping add...")
            return

        # get the ID of the current playlist
        current_playlist_id = self.current_playlist_id
        assert (
            current_playlist_id in self.playlist_ids
        ), f"Attempting to add a track from a playlist {current_playlist_id} not specified in the managed playlists {self.playlist_ids}."
        if not current_playlist_id:
            print(
                f"No playlist detected for {self.alias}, skipping attempt to add track..."
            )
            return

        # if no songs are in the unplayed list, reset the list
        if len(self.unplayed_track_ids.get(current_playlist_id, [])) == 0:
            self.unplayed_track_ids[current_playlist_id] = (
                self.get_all_track_ids_from_playlist(current_playlist_id)
            )
            random.shuffle(self.unplayed_track_ids[current_playlist_id])

        # queues one track and stores the queued track
        self.queued_track_id = self.unplayed_track_ids[current_playlist_id].pop(-1)

        # if the queued track is the same as the currently playing song, skip it
        while self.queued_track_id == self.current_track_id:
            self.queued_track_id = self.unplayed_track_ids[current_playlist_id].pop(-1)

        # try to update the queue
        try:
            self.spotify.add_to_queue(self.queued_track_id)
            print(f"Added to queue for {self.alias}.")
        except spotipy.exceptions.SpotifyException as e:
            print(f"Something went wrong: {e}")
