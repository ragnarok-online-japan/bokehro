# bokehro
bokehro

## Setup
```bash
cd /opt/bokehro
pip3 install -U -r requirements.txt
cp -p bokehro-webui.service ~/.config/systemd/user/
systemctl --user enable --now bokehro-webui.service
scrapy deploy
```
