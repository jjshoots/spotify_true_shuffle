# My Scripts to Automate My Spotify

## OAuth is Weird

For a new machine, when you run the code, it will show `this site can't be reached`.

**This is Normal.**

What you need to do is to copy the link in the address bar, and paste that into the console to authenticate the machine.
I don't make the rules.

## Python Requirements

If using systemd to automate the scripts, it's necessary to know that systemd's Python environment is run at root, so installing the packages requires:
```
python3 -m pip install -r requirements.txt
```
Or some other funky thing with changing venv.
