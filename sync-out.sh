#!/bin/bash

rsync -rav --progress ./credentials/ pi@192.168.0.180:~/spotify_scripts/credentials
