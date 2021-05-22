# ecuagenera-bot

Small monitoring script for the [ecuagenera.com](https://www.ecuagenera.com/) website.

The `ecuagenera_bot.py` script does the following:

* Open website
* if do_checkout is True:
  * Login
  * Clear basket
* For each configured product ID, send out email if product is available
* if do_checkout is True:
  * Add item to basket in desired quantity
  * Check if any of the items has been ordered before
  * if not, order items

## How to run it  (ad-hoc or scheduled)

There are three ways how you can run the script to get notifications:

1) Ad-hoc execution
2) cron execution (scheduled)
3) Debian package installation (systemd triggered)

Below are the steps for each:

### Prerequisites

#### Install dependencies

You have to install some dependencies to make the script work (on Ubuntu):

```bash
sudo apt install python3-yaml python3-selenium chromium-browser chromium-chromedriver
```

or via pip (hint: this is not enough if you want to install the Debian package due to root scope):

```bash
pip3 install -r requirements.txt
```

#### Create config.yml

In order to work properly, you must create a config file for your credentials.

A file `config.yml` has to be created to read configurations. Here is an example:

```yml
item_ids:
  - 12345
  - 67890
item_quantities: # only needed if do_checkout is True
  - 1
  - 5
username: 'ecua_user@outlook.com'
password: 'pw123'
smtp_server: 'smtp.office365.com'
smtp_port: 587
smtp_user: 'test@outlook.com'
smtp_pw: 'pw123'
to_email: 'test2@outlook.com'
from_email: 'test@outlook.com'
do_checkout: True # if bot should auto checkout
```

Store the file either

* if ad-hoc executed: in project directory
* if installed via Debian package: in `/opt/ecuagenera-bot/` (hint: this has to be done after the installation of the Debian package)

### Option 1) Ad-hoc execution

After cloning and creation of the config file, the script can be easily executed by running

```bash
python3 ecuagenera_bot.py
```

## Option 2) Scheduled execution (via cron)

You can also schedule the script to run e.g. every 10 minutes by adding a cron (via `crontab -e`)

```bash
# add the following line at the end of the file
*/10 * * * * DISPLAY=:0 python3 /path/to/ecuagenera_bot.py
```

## Option 3) Scheduled execution (via GitHub Actions)

You can also schedule the script to run e.g. every 5 minutes by adding a GitHub Action. There is one configured in the `.github/workflows/` folder.

## Option 4) Installation via Debian package

Utilities to create a Debian package are included in the repo and can be called via:

```bash
# for just building
make build

# for building, purge and installation
make clean_install
```
