# bokehro
bokehro

## Setup
```bash
cd /opt/bokehro
pip3 install -U -r requirements.txt
mkdir -p ~/.config/systemd/user/
cp -p bokehro-webui.service ~/.config/systemd/user/
systemctl --user daemon-reload
systemctl --user enable --now bokehro-webui.service
python3.13 scrapyd_setup.py sdist
scrapyd-deploy
```
