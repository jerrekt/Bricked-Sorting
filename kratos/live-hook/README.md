# Live hook (CT 150)

Sends each piece that `/identify` recognizes to the Live page. Branden installs it
(it's a root-owned service; Ethan has no sudo). Nothing here changes how `/identify`
answers the Pi.

## Install (as root on CT 150)
1. Copy `live_hook.py` next to the server:
       cp live_hook.py /opt/bricked-sorting/live_hook.py
2. In `/opt/bricked-sorting/brick_server.py`, in the `/identify` route, right after the
   result dict is built and before it is returned, add:
       from live_hook import post_live          # top of the file
       post_live(result, image_bytes)           # result = the dict returned, image_bytes = the uploaded JPEG
   Use the real variable names in that function. Skip it for `?preview=1` requests.
3. Secret file, root only:
       install -m 600 /dev/null /etc/bricked-live.env
       # nano /etc/bricked-live.env  ->  BRICKED_LIVE_TOKEN=<same value as in the bots container>
4. Load it into the service:
       mkdir -p /etc/systemd/system/bricked-server.service.d
       printf '[Service]\nEnvironmentFile=/etc/bricked-live.env\n' > /etc/systemd/system/bricked-server.service.d/live.conf
       systemctl daemon-reload && systemctl restart bricked-server
5. Test: send one photo through `/identify` (or let the Pi send one) and watch the Live page.

## Make the token
Once, anywhere: `python3 -c "import secrets; print(secrets.token_urlsafe(32))"`.
Put the same value in `/etc/bricked-claim/bot.env` (bots container) and `/etc/bricked-live.env` (CT 150).
Never paste it in chat, the repo or the vault. If it leaks, make a new one and replace both.

## Turn off
Remove the drop-in (`rm /etc/systemd/system/bricked-server.service.d/live.conf`), daemon-reload, restart.
`/identify` keeps working without it.
