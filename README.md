rdmo-chatbot
============

Setup
-----

The setup assumes that `rdmo-app` is already configured. First, install the plugin

```
pip install git+https://github.com/rdmorganiser/rdmo-plugins-chatbot
```

Add the following to your `config/settings/local.py`:

```python
INSTALLED_APPS = ['rdmo_chatbot', *INSTALLED_APPS]
SETTINGS_EXPORT += ['CHAINLIT_URL']

CHAINLIT_URL = 'http://localhost:8080/chatbot'

CHAINLIT_OPENAI_URL = None    # this can be an alternative provider
CHAINLIT_OPENAI_API_KEY = ''  # this needs to be obtained from open.ai

CHAINLIT_AUTH_SECRET = ''     # this should be a longer random string

CHAINLIT_SETTINGS = {
    "model": 'gpt-3.5-turbo',
    "max_tokens": 100,
    "temperature": 0.5
}

CHATBOT_STARTERS = [
    {
        'label': 'What is a DMP?',
        'message': 'What is a Data Management Plan (DMP)? How can I create a Data Management Plan with RDMO?',
        'icon': None
    }
]

MIDDLEWARE.append('rdmo_chatbot.middleware.ChatbotMiddleware')
```

Deployment
----------

### Deployment

Run the Django development server as usual:

```bash
python manage.py runserver
```

In a second terminal, also in your `rdmo-app` directory and the same virtual environment,
run the `runchatbot` management script:

```bash
python manage.py runchatbot
```

The chatbot interface then runs at http://localhost:8080

### Production

The chatbot can be deployed using Gunicorn and Systemd:

```
# in /etc/systemd/system/chatbot-chainlit.service

[Unit]
Description=RDMO chatbot chainlit gunicorn daemon
After=network.target

[Service]
User=rdmo
Group=rdmo

WorkingDirectory=/srv/rdmo/rdmo-app/

LogsDirectory=chainlit

Environment="PATH=/srv/rdmo/rdmo-app/env/bin/"
Environment="PYTHONUNBUFFERED=1"

ExecStart=/srv/rdmo/rdmo-app/env/bin/python manage.py runchatbot --root-path=/chatbot

StandardOutput=append:/var/log/chainlit/stdout.log
StandardError=append:/var/log/chainlit/stderr.log

[Install]
WantedBy=multi-user.target
```

Chainlit uses Websockets, this makes the deployment a bit different then for RDMO alone. The following NGINX config can be used:

```
server {
    listen 80;
    server_name localhost;

    location / {
        proxy_pass http://127.0.0.1:8000;

        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /chatbot/ {
        proxy_pass http://127.0.0.1:8080/chatbot/;

        proxy_http_version 1.1;

        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }
}
```

For Apache2, you can use:

```
<VirtualHost *:80>
    ServerAdmin webmaster@localhost
    DocumentRoot /var/www/html

    ErrorLog ${APACHE_LOG_DIR}/error.log
    CustomLog ${APACHE_LOG_DIR}/access.log combined

    ProxyPreserveHost On
    ProxyRequests Off

    <Location />
        ProxyPass "http://localhost:8000/"
        ProxyPassReverse "http://localhost:8000/"
    </Location>

    <Location /chatbot>
        ProxyPass "http://localhost:8080/chatbot"
        ProxyPassReverse "http://localhost:8080/chatbot"
    </Location>

    <Location /chatbot/ws>
        ProxyPass "ws://localhost:8080/chatbot/ws"
        ProxyPassReverse "ws://localhost:8080/chatbot/ws"
    </Location>

    Alias /static /srv/rdmo/rdmo-app/static_root/
    <Directory /srv/rdmo/rdmo-app/static_root/>
        Require all granted
    </Directory>
</VirtualHost>
```
