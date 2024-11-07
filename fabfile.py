from fabric import task


@task(hosts=['rotor@starenka.net'],
      help={'branch': 'branch to deploy (=master)'})
def deploy(c, branch='master'):
    with c.cd('/www/mbgolf.starenka.net'):
        c.run("sudo -u starenka ssh-agent bash -c 'ssh-add ~/.ssh/github_caddy && git fetch'")
        c.run('sudo -u starenka git reset --hard origin/%s' % branch)
        c.run('sudo -u root make build')
        c.run('sudo -u root supervisorctl restart mbgolf.starenka.net')


@task(hosts=['rotor@starenka.net'])
def wipe_db(c):
    with c.cd('/www/mbgolf.starenka.net'):
        c.run('sudo -u root supervisorctl stop mbgolf.starenka.net')
        c.run('sudo -u root rm -f instance/db.sqlite3')
        c.run('sudo -u root supervisorctl start mbgolf.starenka.net')
