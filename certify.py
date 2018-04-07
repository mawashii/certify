#!/usr/bin/env python

import ConfigParser
import os
import socket
import ssl
import subprocess
import sys
import uuid

config = ConfigParser.ConfigParser()

def exit(status, msg=""):
    if len(msg):
        print(msg)
    sys.exit(status)

def reload():
    def send(msg):
        sslsock.send(msg)
        print(sslsock.recv(2048))

    host = config.get('irc', 'host')
    port = int(config.get('irc', 'port'))
    oper_user = config.get('irc', 'oper_user')
    oper_pass = config.get('irc', 'oper_pass')

    # connect to host+port with ssl without checking certificate validity
    # this could/should be set to actually verify the cert at a later stage
    # when everything is migrated to let's encrypt properly
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(60)
    sslsock = ssl.wrap_socket(sock, cert_reqs=ssl.CERT_NONE)
    sslsock.connect((host, port))

    # ensure random nickname to not run into duplicate nickname errors
    username = '_' + str(uuid.uuid4()).split('-')[-1]
    send("USER {0} {0} {0} :Let's Encrypt Bot\r\n".format(username))
    send("NICK {}\r\n".format(username))
    send("OPER {} {}\r\n".format(oper_user, oper_pass))
    send("REHASH\r\n")
    send("QUIT\r\n")

    sslsock.close()

def run_cmd(args):
    return subprocess.call(args) == 0

if __name__ == '__main__':
    script = os.path.realpath(__file__)
    path = os.path.dirname(script)
    config.readfp(open(os.path.join(path, 'config')))

    if len(sys.argv) > 1:
        if sys.argv[1] == 'reload':
            reload()
        else:
            exit(4, 'No such argument, call with either reload or no argument at all')
    else:
        acme_home = os.path.join(path, '.acme.sh')

        if not os.path.exists(acme_home):
            # first run of this script - set acme.sh up without the default cronjob
            fullchain_path = config.get('irc', 'cert_path')
            privkey_path = config.get('irc', 'key_path')

            domains = []
            for domain in config.get('cert', 'domains').split():
                domains.append('--domain')
                domains.append(domain)
            email = config.get('cert', 'email')

            acme_git = os.path.join(path, 'acme.sh')
            acme = os.path.join(acme_git, 'acme.sh')
            os.chdir(acme_git)
            if not run_cmd([acme, '--install', '--staging', '--home', acme_home, '--accountemail', email, '--nocron']):
                exit(1, 'Setting up acme.sh failed')
            os.chdir(acme_home)
            acme = os.path.join(acme_home, 'acme.sh')
            if not run_cmd([acme, '--issue', '--staging', '--standalone', '--home', acme_home, '--fullchain-file', fullchain_path, '--key-file', privkey_path, '--reloadcmd', "{} reload".format(script)] + domains):
                exit(2, 'Issuing certificate for {} failed.'.format(domain))
            exit(0)

        os.chdir(acme_home)
        acme = os.path.join(acme_home, 'acme.sh')
        if not run_cmd([acme, '--staging', '--renew-all', '--home', acme_home]):
            exit(3, 'Certificate renewal failed')
    exit(0)
