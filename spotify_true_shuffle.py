#!/usr/bin/env python
from __future__ import annotations

import os
import time

from .true_shuffler import TrueShuffler

_CHECK_INTERVAL_ = 180


if __name__ == "__main__":
    # load spotify credentials
    credentials_dir = os.path.join(os.path.dirname(__file__), "credentials/zoey")

    # initiate the client
    client = TrueShuffler(credentials_dir=credentials_dir)

    while True:
        # sleep a bit
        time.sleep(_CHECK_INTERVAL_)

        # update our status
        if not client.update_current_playback():
            continue

        # override the queue if conditions are right
        if client.is_playing() and client.playback_is_playlist():
            print("Playlist being played, checking queue...")
            client.check_add_queue()
        else:
            print("Not playing ATM, waiting...")
