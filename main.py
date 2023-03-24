#!/usr/bin/env python
from __future__ import annotations

import os
import time

from true_shuffler import TrueShuffler

SpotifyUser = str
_CHECK_INTERVAL_ = 180


if __name__ == "__main__":
    # the credentials directory
    credentials_dir = os.path.join(os.path.dirname(__file__), "credentials")

    clients: dict[SpotifyUser, TrueShuffler] = dict()
    for alias in os.listdir(credentials_dir):
        clients[alias] = TrueShuffler(os.path.join(credentials_dir, alias), alias)

    while True:
        # sleep a bit
        time.sleep(_CHECK_INTERVAL_)

        # iterate through all clients
        for alias, client in clients.items():
            # update our status
            if not client.update_current_playback():
                continue

            # override the queue if conditions are right
            if client.is_playing() and client.playback_is_playlist():
                print(f"Playlist being played for {alias}, checking queue...")
                client.check_add_queue()
            else:
                print(f"{alias} not playing anything, waiting...")
