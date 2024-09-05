#!/usr/bin/env python
from __future__ import annotations

import os
import time

from true_shuffler import TrueShuffler, SpotifyUser

_CHECK_INTERVAL_ = 180


if __name__ == "__main__":
    # the credentials directory
    credentials_dir = os.path.join(os.path.dirname(__file__), "credentials")

    clients: dict[SpotifyUser, TrueShuffler] = dict()
    for alias in os.listdir(credentials_dir):
        full_path = os.path.join(credentials_dir, alias)
        if os.path.isdir(full_path):  # Check if it's a directory
            clients[alias] = TrueShuffler(full_path, alias)

    print(f"Master service started, checking playbacks every {_CHECK_INTERVAL_} seconds...")

    while True:
        # sleep a bit
        time.sleep(_CHECK_INTERVAL_)

        # iterate through all clients
        for alias, client in clients.items():
            # update our status
            if not client.update_current_playback():
                continue

            # override the queue if conditions are right
            if (
                client.is_playing()
                and client.playback_is_playlist()
                and client.is_shuffling()
            ):
                print(f"Playlist being played for {alias}, checking queue...")
                client.check_add_queue()
            else:
                print(f"{alias} not playing anything, waiting...")
