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

## MariaDB SQL
```sql
DROP USER 'ro-items'@'localhost';
DROP USER 'ro-items'@'127.0.0.1';
CREATE USER 'ro-items'@'localhost' IDENTIFIED BY 'XXXXXXXXXXXXXXXXXXXXXXXX';
GRANT ALL PRIVILEGES ON `ro-items`.* TO 'ro-items'@'localhost';
CREATE USER 'ro-items'@'127.0.0.1' IDENTIFIED BY 'XXXXXXXXXXXXXXXXXXXXXXXX';
GRANT ALL PRIVILEGES ON `ro-items`.* TO 'ro-items'@'127.0.0.1';
FLUSH PRIVILEGES;
```
