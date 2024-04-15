#!/usr/bin/env python
from __future__ import annotations

import json
import os
import random
from copy import deepcopy

import spotipy
from spotipy.oauth2 import SpotifyOAuth

from typings import PlaylistID, SongID


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

        # the dictionary of unplayed song ids that we are waiting to add to queue
        self.unplayed_song_ids: dict[PlaylistID, list[SongID]] = dict()

        # runtime variables
        self.queued_song: SongID = "null"
        self.current_playback = self.spotify.current_playback()

        # printout
        self.update_current_playback()
        all_song_ids = {
            playlist_id: self.get_all_song_ids_from_playlist(playlist_id)
            for playlist_id in self.playlist_ids
        }
        print(
            f"Initialized True Shuffle with {len(all_song_ids)} playlists for {self.alias}, "
            f"totalling {sum([len(v) for _, v in all_song_ids.items()])} songs."
        )

    def get_all_song_ids_from_playlist(self, playlist_id) -> list[SongID]:
        # returns all ids in the playlist as a list of strings
        tracks_response = self.spotify.playlist_tracks(playlist_id)
        if not tracks_response:
            print(
                f"Something went wrong when retrieving all songs for {playlist_id}, the playlist doesn't seem to exist."
            )
            return []

        # iterate through the playlist in chunks to accumulate song ids
        ids = [track["track"]["uri"] for track in tracks_response["items"]]
        while tracks_response := self.spotify.next(tracks_response):
            ids.extend([track["track"]["uri"] for track in tracks_response["items"]])

        return ids

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
        return self.current_playback.get("is_playing", False)

    def playback_is_playlist(self) -> bool:
        if self.current_playback is None:
            return False

        return self.current_playlist_id in self.playlist_ids

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

    def is_shuffling(self) -> bool:
        if self.current_playback is None:
            return False

        return self.current_playback.get("shuffle_state", False)

    def check_add_queue(self) -> None:
        try:
            queue = self.spotify.queue()
        except Exception as e:
            queue = None
            print(e)

        # something went wrong here
        if not queue:
            return

        # get all the uris for songs in the current queue
        all_queued_uris = [track["uri"] for track in queue["queue"]]

        # if the most recently queued song is inside the queue just exit for now
        if self.queued_song in all_queued_uris[:5]:
            print(f"Queued song already in queue for {self.alias}, skipping add...")
            return

        # get the ID of the current playlist
        current_playlist_id = self.current_playlist_id
        assert (
            current_playlist_id in self.playlist_ids
        ), f"Attempting to add a song from a playlist {current_playlist_id} not specified in the managed playlists {self.playlist_ids}."
        if not current_playlist_id:
            print(
                f"No playlist detected for {self.alias}, skipping attempt to add song..."
            )
            return

        # if no songs are in the unplayed list, reset the list
        if len(self.unplayed_song_ids[current_playlist_id]) == 0:
            self.unplayed_song_ids[current_playlist_id] = (
                self.get_all_song_ids_from_playlist(current_playlist_id)
            )
            random.shuffle(self.unplayed_song_ids[current_playlist_id])

        # queues one song and stores the queued song
        self.queued_song = self.unplayed_song_ids[current_playlist_id].pop(-1)
        self.spotify.add_to_queue(self.queued_song)

        print(f"Added to queue for {self.alias}.")
