rdmo-chatbot
============

Setup
-----

The setup assumes that `rdmo-app` is already configured. First, install the plugin

```bash
# directly from github
pip install git+https://github.com/rdmorganiser/rdmo-plugins-chatbot

# alternatively, from a local copy
git clone git@github.com:rdmorganiser/rdmo-plugins-llm-views
pip install -e rdmo-plugins-chatbot[openai]
pip install -e rdmo-plugins-chatbot[ollama]  # alternatively
```

Add the following to your `config/settings/local.py`:

```python
INSTALLED_APPS = ['rdmo_chatbot', *INSTALLED_APPS]
SETTINGS_EXPORT += ['CHATBOT_URL']

MIDDLEWARE.append('rdmo_chatbot.middleware.ChatbotMiddleware')

CHATBOT_URL = 'http://localhost:8080'
CHATBOT_AUTH_SECRET = ''  # secret long random string

CHATBOT_SYSTEM_PROMPT = '''
You are a knowledgeable assistant specializing in writing data management plans (DMPs).

- Take the provided context data into account.
- Keep your response concise, not exceeding 100 words.
- Maintain a professional, clear, and concise writing style.

The name of the user is: {user}.
'''
```

For the `OpenAIAdapter` add:

```python
CHATBOT_ADAPTER = 'rdmo_chatbot.chatbot.adapter.openai.OpenAIAdapter'
CHATBOT_OPENAI_API_KEY = ''
CHATBOT_OPENAI_BASE_URL = ''  # or None for the default OpenAI API
CHATBOT_OPENAI_ARGS = {
   "model": 'gpt-4.1-nano'
}
```

and install the additional dependency with `pip install openai`.

Alternatively, for the `OpenAILangChainAdapter`:

```python
CHATBOT_ADAPTER = 'rdmo_chatbot.chatbot.adapter.langchain.OpenAILangChainAdapter'
CHATBOT_LLM_ARGS = {
   "openai_api_key": '',
   "openai_api_base": ''  # or None for the default OpenAI API
   "model": 'gpt-4.1-nano'
}
```

and install the additional dependencies with `pip install langchain langchain-openai`.

Alternatively, for the `OllamaLangChainAdapter`:

```python
CHATBOT_ADAPTER = 'rdmo_chatbot.chatbot.adapter.langchain.OllamaLangChainAdapter'
CHATBOT_LLM_ARGS = {
    "model": 'mistral:7b'
}
```

and install the additional dependencies with `pip install langchain langchain-ollama`.

For starters use:

```python
CHATBOT_STARTERS = [
    {
        'label': 'What is a DMP?',
        'message': 'What is a Data Management Plan (DMP)? How can I create a Data Management Plan with RDMO?',
        'icon': None
    }
]
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
