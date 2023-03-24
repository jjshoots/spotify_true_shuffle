#!/usr/bin/env python
from __future__ import annotations

import os
import random
import json

import spotipy
from spotipy.oauth2 import SpotifyOAuth


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
                cache_handler=spotipy.CacheFileHandler(cache_path=os.path.join(credentials_dir, ".cache")),
                redirect_uri="http://localhost:8888/callback",
                scope="streaming,user-modify-playback-state,user-read-playback-state,user-read-currently-playing,user-library-read",
                open_browser=False,
            )
        )

        # get the playlist id and all the songs
        self.main_playlist_id = self.credentials["playlist_id"]
        self.all_song_uris = self.get_all_uris_from_playlist(self.main_playlist_id)

        # runtime variables
        self.queued_song = "null"
        self.current_playback = self.spotify.current_playback()

        # we don't wanna replay songs we've already played, so we track the songs played
        self.unplayed_uri_ids = []

        # printout
        self.update_current_playback()
        print(f"Initialized True Shuffle with {len(self.all_song_uris)} songs for {self.alias}.")

    def get_all_uris_from_playlist(self, playlist_id) -> list[str]:
        # returns all uris in the playlist as a list of string
        tracks_response = self.spotify.playlist_tracks(playlist_id)
        uris = [track["track"]["uri"] for track in tracks_response["items"]]
        while tracks_response["next"]:
            tracks_response = self.spotify.next(tracks_response)
            uris.extend([track["track"]["uri"] for track in tracks_response["items"]])

        return uris

    def update_current_playback(self) -> bool:
        # get the currently playing song
        try:
            self.current_playback = self.spotify.current_playback()
            return True
        except Exception as e:
            print(e)
            return False

    def is_playing(self) -> bool:
        # no playback info means no song played for awhile
        if self.current_playback is None:
            return False

        # check whether we're really playing
        return self.current_playback.get("is_playing")

    def playback_is_playlist(self) -> bool:
        if self.current_playback is None:
            return False

        return (
            self.current_playback["context"]["uri"].split(":")[-1]
            == self.main_playlist_id
        )

    def check_add_queue(self):
        try:
            queue = self.spotify.queue()
        except Exception as e:
            queue = None
            print(e)

        # something went wrong here
        if queue is None:
            return

        # get all the uris for songs in the current queue
        all_queued_uris = [track["uri"] for track in queue["queue"]]

        # if the queued song is not what we queued, add a new one to queue
        if self.queued_song in all_queued_uris:
            print(f"Queued song already in queue for {self.alias}, skipping add...")
            return

        print(f"Adding to queue for {self.alias} ...")

        # if no songs are in the unplayed list, reset the list
        if len(self.unplayed_uri_ids) == 0:
            self.unplayed_uri_ids = list(range(len(self.all_song_uris)))
            random.shuffle(self.unplayed_uri_ids)

        # queues one song and stores the queued song
        random_uri_id = self.unplayed_uri_ids.pop(-1)
        self.queued_song = self.all_song_uris[random_uri_id]
        self.spotify.add_to_queue(self.queued_song)
