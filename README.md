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
INSTALLED_APPS = ['rdmo_chatbot.plugin', *INSTALLED_APPS]
SETTINGS_EXPORT += ['CHATBOT_URL']

MIDDLEWARE.append('rdmo_chatbot.plugin.middleware.ChatbotMiddleware')

CHATBOT_URL = 'http://localhost:8080'
CHATBOT_AUTH_SECRET = ''  # secret long random string

CHATBOT_SYSTEM_PROMPT = '''
You are a knowledgeable assistant specializing in writing data management plans (DMPs).

- Take the provided context data into account.
- Keep your response concise, not exceeding 100 words.
- Maintain a professional, clear, and concise writing style.

The name of the user is: {user}.
'''

CHATBOT_STREAM = True  # whether the responses should be streamed character by character from the llm

CHATBOT_LANGUAGES = {
    "en": "en-US",
    "de": "de-DE"
}
```
In addition, the chatbot endpoint needs to be added to the `config/urls.py`

```python
urlpatterns += [path("api/v1/chatbot/", include("rdmo_chatbot.plugin.urls"))]
```

### Adapter

The connection to the LLM is encapsulated using the adapter classes in `adapter.py`.

For the `OpenAILangChainAdapter`:

```python
CHATBOT_ADAPTER = 'rdmo_chatbot.chatbot.adapter.langchain.OpenAILangChainAdapter'
CHATBOT_LLM_ARGS = {
   "openai_api_key": '',
   "openai_api_base": '',  # or None for the default OpenAI API
   "model": 'gpt-4.1-nano'
}
```

and install the additional dependencies with `pip install langchain langchain-openai`.

Alternatively, for the `OllamaLangChainAdapter`:

```python
CHATBOT_ADAPTER = 'rdmo_chatbot.chatbot.adapter.OllamaLangChainAdapter'
CHATBOT_LLM_ARGS = {
    "model": 'mistral:7b'
}
```

and install the additional dependencies with `pip install langchain langchain-ollama`.

### Storage

In order to persist the chat messages, the history can be stored in one of the storage backends in `store.py`.

For a simple in memory store, which will not persist when the server restarts use:

```python
CHATBOT_STORE = 'rdmo_chatbot.chatbot.stores.locmem.LocMemStore'
```

For Redis use, e.g.:

```python
CHATBOT_STORE = 'rdmo_chatbot.chatbot.stores.redis.RedisStore'
CHATBOT_STORE_CONNECTION = {
    "host": "127.0.0.1",
    "port": 6379,
    "db": 0
}
CHATBOT_STORE_TTL = 86400  # omit if not required
```

To store the messages in Sqlite use, e.g.:

```python
CHATBOT_STORE = 'rdmo_chatbot.chatbot.stores.sqlite3.Sqlite3Store'
CHATBOT_STORE_CONNECTION = '/tmp/chatbot.sqlite3'  # path to the database
```

For PostgreSQL:

```python
CHATBOT_STORE = 'rdmo_chatbot.chatbot.stores.postgres.PostgresStore'
CHATBOT_STORE_CONNECTION = {
    'dbname': "rdmo_chatbot",
    "user": "rdmo_chatbot",
    "password": "<super secret>",
    'host': '127.0.0.1',
    "port": 5432,
}
```

For MySQL or MariaDB:

```python
CHATBOT_STORE = 'rdmo_chatbot.chatbot.stores.mysql.MysqlStore'
CHATBOT_STORE_CONNECTION = {
    'db': "rdmo_chatbot",
    'user': "rdmo_chatbot",
    'passwd': "<super secret>",
    'host': '127.0.0.1',
    "port": 3306
}
```

## Theme

In order to customize the chatbot the `.chainlit` and `public` have to be copied and adjusted and `CHATBOT_PATH` has to be set in `config/settings/local.py`:

```
CHATBOT_PATH = '/path/to/chainlit/workdir/'
```

Most files in `public` can be updated. `custom.js` and `elements/InputSelect.jsx` should be kept as they are. The chainlit config can be found in `.chainlit/config.toml`.


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

Acknowledgement
---------------

We would like to thank the Federal Government and the Heads of Government of the Länder, as well as the
Joint Science Conference (GWK), for their funding and support within the framework of the NFDI4ING consortium.
Funded by the German Research Foundation (DFG) - project number 442146713."
