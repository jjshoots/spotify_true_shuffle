# My Scripts to Automate My Spotify

This repo expects there to be a directory called `credentials/` with in the same directory as `main.py`.
The structure of the directory is as follows:

```
credentials/
|  user1/
|  |  credentials.json
|  user2/
|  |  credentials.json
| ...
```

Each user, `user1` and `user2`, can be named anything for your convenience, they stand for basically how many users you want true shuffle to be implemented for.
The `.json` files must have the following format:

```json
{
  "id": "SPOTIFY_ID",
  "secret": "SPOTIFY_SECRET",
  "playlist_ids": ["ID1", "ID2"]
}
```

You can obtain `SPOTIFY_ID` and `SPOTIFY_SECRET` by following [these set of instructions](https://support.heateor.com/get-spotify-client-id-client-secret/).
To find the Spotify playlist id enter the playlist page, click the (...) button near the play button, and click "Copy Playlist Link" under the Share menu. The playlist id is the string right after `playlist/` and before `?`.

You can add as many playlist IDs for as many playlists that you want true shuffle to be implemented for.

## OAuth is Weird

For a new machine, when you first run the code, it will open a browser window that will show `this site can't be reached`.

**This is Normal.**

What you need to do is to copy the link in the address bar, and paste that into the console to authenticate the machine.
I don't make the rules.

## Python Requirements

If using systemd to automate the scripts, it's necessary to know that systemd's Python environment is run at root, so installing the packages requires:
```
python3 -m pip install -r requirements.txt
```
Or some other funky thing with changing venv.
