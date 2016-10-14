from fabric.api import *
from fabric.contrib.files import exists

class FabricException(Exception):
    pass

def init():
    sudo('apt-get update')
    sudo('apt-get install -y postgresql postgresql-server-dev-all git')
    sudo('apt-get install -y python-virtualenv python-dev libjpeg-dev libjpeg8-dev')

    with settings(abort_exception = FabricException):
        # create roles if they don't already exist
        # env.user for developer login
        # # www-data is for the gunicorn process
        try:
            sudo("psql -t -c '\du' | cut -d \| -f 1 | grep -qw %s" % env.user, user='postgres')
        except FabricException:
            sudo('createuser %s' % env.user, user='postgres')
        try:
            sudo("psql -t -c '\du' | cut -d \| -f 1 | grep -qw www-data", user='postgres')
        except FabricException:
            sudo('createuser www-data', user='postgres')

        # create a database if it doesn't already exist
        try:
            sudo("psql -lqt | cut -d \| -f 1 | grep -qw wagtaildemo", user='postgres')
        except FabricException:
            sudo('createdb wagtaildemo -O "%s"' % env.user, user='postgres')

        # Grant www-data to the wagtaildemo database
        sudo('psql -c \'GRANT "%s" TO "www-data"\'' % env.user, user='postgres')

    if not exists('/wagtaildemo'):
        sudo('git clone https://github.com/torchbox/wagtaildemo.git /wagtaildemo')
        sudo('chown -R %s /wagtaildemo' % env.user)

    with cd('/wagtaildemo'):
        run('virtualenv venv')

        with prefix('source venv/bin/activate'):
            run('pip install -r requirements.txt')
            run('./manage.py migrate')
            run('./manage.py load_initial_data')
            run('./manage.py collectstatic --no-input')
            run('chmod 777 static')
            run('chmod 777 media')
            # automated createsuperuser
            run('echo "from django.contrib.auth.models import User; User.objects.create_superuser(\'admin\', \'admin@example.com\', \'excella\')" | ./manage.py shell')

    sudo('apt-get install -y nginx gunicorn')

    put('wagtail-gunicorn.conf', '/etc/gunicorn.d/wagtail.conf', use_sudo=True)
    put('wagtail-nginx.conf', '/etc/nginx/sites-available/wagtail', use_sudo=True)
    sudo('ln -sf /etc/nginx/sites-available/wagtail /etc/nginx/sites-enabled/wagtail')
    sudo('rm -f /etc/nginx/sites-enabled/default')
    sudo('service nginx restart')
    sudo('service gunicorn restart')

def deploy():
    with cd('wagtaildemo'):
        run('git pull')
        with prefix('source venv/bin/activate'):
            run('pip install -r requirements.txt')
            run('./manage.py migrate')
