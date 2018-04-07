# certify.py

This script uses acme.sh to generate Let's Encrypt certificates and REHASH an ircd via user of an OPER login.

### Installation

certify.py depends on socat to run a standalone webserver to reply to the Let's Encrypt challenges.

Copy `config.dist` to `config` and adjust the config values as needed. The script will connect with a random nickname to the specified IRC server, oper up and issue a REHASH command after every certificate renewal.

```sh
$ cd certify
$ git submodule init
$ git submodule update
$ ./certify.py
```

Ideally add a cronjob to run this script every night to make sure you always have current certificates.
