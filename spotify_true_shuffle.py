#!/usr/bin/env python
from __future__ import annotations

import random
import time

import os
import dotenv

import spotipy
from spotipy.oauth2 import SpotifyOAuth

_CHECK_INTERVAL_ = 180
_MAIN_PLAYLIST_ID_ = "6LCRCv7hmovwG9hzlqZI7V"


class Spotify:
    def __init__(self, main_playlist_id):
        self.spotify = spotipy.Spotify(
            auth_manager=SpotifyOAuth(
                client_id=os.environ.get("ID"),
                client_secret=os.environ.get("SECRET"),
                redirect_uri="http://localhost:8888/callback",
                scope="streaming,user-modify-playback-state,user-read-playback-state,user-read-currently-playing,user-library-read",
            )
        )

        # constants
        self.main_playlist_id = main_playlist_id
        self.all_song_uris = self.get_all_uris_from_playlist(main_playlist_id)

        # runtime variables
        self.queued_song = "null"
        self.current_playback = self.spotify.current_playback()

        print(f"Initialized with {len(self.all_song_uris)} songs.")

    def get_all_uris_from_playlist(self, playlist_id) -> list[str]:
        # returns all uris in the playlist as a list of string
        tracks_response = self.spotify.playlist_tracks(playlist_id)
        uris = [track["track"]["uri"] for track in tracks_response["items"]]
        while tracks_response["next"]:
            tracks_response = self.spotify.next(tracks_response)
            uris.extend([track["track"]["uri"] for track in tracks_response["items"]])

        return uris

    def update_current_playback(self):
        # get the currently playing song
        self.current_playback = self.spotify.current_playback()

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
            queue = client.spotify.queue()
        except Exception as e:
            queue = None
            print(e)

        # something went wrong here
        if queue is None:
            return

        all_queued_uris = [track["uri"] for track in queue["queue"]]

        # if the queued song is not what we queued, add a new one to queue
        if self.queued_song in all_queued_uris:
            print("Queued song already in queue, skipping add...")
            return

        print("Adding to queue...")

        # queues one song and stores the queued song
        self.queued_song = random.choice(self.all_song_uris)
        self.spotify.add_to_queue(self.queued_song)


if __name__ == "__main__":
    # load spotify credentials
    dotenv_path = os.path.join(os.path.dirname(__file__), "credentials")
    dotenv.load_dotenv(dotenv_path)

    # initiate the client
    client = Spotify(_MAIN_PLAYLIST_ID_)

    while True:
        # sleep a bit
        time.sleep(_CHECK_INTERVAL_)

        # update our status
        client.update_current_playback()

        # override the queue if conditions are right
        if client.is_playing() and client.playback_is_playlist():
            print("Playlist being played, checking queue...")
            client.check_add_queue()
        else:
            print("Not playing ATM, waiting...")
