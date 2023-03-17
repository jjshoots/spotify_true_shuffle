#!/usr/bin/env python
from __future__ import annotations

import os
import time

import dotenv
import spotipy
from spotipy.oauth2 import SpotifyOAuth

_THIS_DEVICE_NAME_ = "Pi Spotify"
_CHECK_INTERVAL_ = 900
_TIMEOUT_TO_TAKEOVER_ = 1800


class Spotify:
    def __init__(self, this_device_name):
        self.spotify = spotipy.Spotify(
            auth_manager=SpotifyOAuth(
                client_id=os.environ.get("ID"),
                client_secret=os.environ.get("SECRET"),
                redirect_uri="http://localhost:8888/callback",
                scope="streaming,user-modify-playback-state,user-read-playback-state,user-read-currently-playing,user-library-read",
                open_browser=False,
            )
        )

        # constants
        self.this_device_name = this_device_name

        # printout
        self.update_current_playback()
        print(f"Initialized Autoplayer on device {this_device_name}.")

    def get_this_device(self) -> dict | None:
        try:
            devices = self.spotify.devices()
        except Exception as e:
            devices = None
            print(e)

        # something went wrong here
        if devices is None:
            return None

        # returns a string for this device
        all_devices = devices["devices"]

        for device in all_devices:
            if device["name"].lower() == self.this_device_name.lower():
                return device

        # we're not supposed to end up here
        print("This device not on available devices, likely Raspotify failed!")
        return None

    def update_current_playback(self):
        # get the currently playing song
        self.current_playback = self.spotify.current_playback()

    def is_playing(self) -> bool:
        # no playback info means no song played for awhile
        if self.current_playback is None:
            return False

        # check whether we're really playing
        return self.current_playback.get("is_playing")

    def play(self):
        this_device = self.get_this_device()

        # check that we actually have this device
        if this_device is None:
            print("Failed to play: device not found!")
            return

        self.spotify.volume(0, device_id=this_device["id"])
        self.spotify.transfer_playback(device_id=this_device["id"], force_play=True)


if __name__ == "__main__":

    # load spotify credentials
    dotenv_path = os.path.join(os.path.dirname(__file__), "credentials")
    dotenv.load_dotenv(dotenv_path)

    # initiate the client and test the connection
    client = Spotify(_THIS_DEVICE_NAME_)

    # restart the timeout
    total_timeout = 0

    while True:
        # sleep a bit
        time.sleep(_CHECK_INTERVAL_)

        # update our status
        client.update_current_playback()

        # if not playing, continue waiting until play
        if client.is_playing():
            print("Playing somewhere, ignoring...")
            total_timeout = 0
            continue

        # if not playing for more than the takeover time, play
        if total_timeout >= _TIMEOUT_TO_TAKEOVER_:
            print("Taking over playback...")
            client.play()
            continue

        total_timeout += _CHECK_INTERVAL_
        print(f"Haven't been playing for {total_timeout} seconds.")
