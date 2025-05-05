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

cat << '_EOL_' > ~/.scrapyd.conf
[scrapyd]
eggs_dir  = /home/ec2-user/scrapyd/eggs
logs_dir  = /home/ec2-user/scrapyd/logs
dbs_dir   = /home/ec2-user/scrapyd/dbs
items_dir = /home/ec2-user/scrapyd/items
jobs_to_keep = 2
max_proc = 2
max_proc_per_cpu = 1
finished_to_keep = 100
poll_interval = 10.0
bind_address = 127.0.0.1
http_port   = 6800
debug       = off
runner      = scrapyd.runner
application = scrapyd.app.application
launcher    = scrapyd.launcher.Launcher
webroot     = scrapyd.website.Root

[services]
schedule.json     = scrapyd.webservice.Schedule
cancel.json       = scrapyd.webservice.Cancel
addversion.json   = scrapyd.webservice.AddVersion
listprojects.json = scrapyd.webservice.ListProjects
listversions.json = scrapyd.webservice.ListVersions
listspiders.json  = scrapyd.webservice.ListSpiders
delproject.json   = scrapyd.webservice.DeleteProject
delversion.json   = scrapyd.webservice.DeleteVersion
listjobs.json     = scrapyd.webservice.ListJobs
daemonstatus.json = scrapyd.webservice.DaemonStatus
_EOL_

echo "export PYTHONPATH=/opt/bokehro:\$PYTHONPATH" >> ~/.bash_profile
source ~/.bash_profile
mkdir -p ~/scrapyd/{eggs,logs,dbs,items}
python3.13 scrapyd_setup.py sdist
scrapyd-deploy

# local execute
scrapy crawl ItemSalesHistorySpider --loglevel WARNING

# execute
curl http://localhost:6800/schedule.json -d project=bokehro -d spider=ItemSalesHistorySpider
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
