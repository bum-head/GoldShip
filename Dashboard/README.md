# GoldShip

### SLEEP GOYIMS · AI SLOP-RIDERS 🤗

GoldShip is an early-stage Django website. The current version is a basic multi-page site branded as **NetAgri** in its page templates. It provides a starting point for the project before interactive agricultural features are added.

## Current features

- Home page
- About page
- Shared page layout using Django template inheritance (`base.html`)
- Navigation between pages
- Shared CSS served through Django's static-file system

The project does **not** yet implement a crop marketplace, user registration, buyer inquiries, weather data, or other agricultural functionality.

## Tech stack

- **Python** — programming language
- **Django** — web framework
- **HTML and CSS** — page content and styling
- **SQLite** — the default local development database created by Django

PostgreSQL is not required for the current basic website. If `Smolpage/settings.py` has been changed to use PostgreSQL, the database server and matching credentials must be configured separately.

## Requirements

- Python 3.10 or newer
- `pip` (included with standard Python installations)
- Git

## Project structure

The repository root should contain the Django project's `manage.py` file:

```text
GoldShip/
├── manage.py
├── README.md
├── requirements.txt
├── Smolpage/
│   ├── settings.py
│   ├── urls.py
│   ├── asgi.py
│   └── wsgi.py
└── pages/
    ├── views.py
    ├── urls.py
    ├── templates/
    │   └── pages/
    │       ├── base.html
    │       ├── home.html
    │       └── about.html
    └── static/
        └── pages/
            └── style.css
```

Django creates additional files inside `Smolpage/` and `pages/`; they are omitted from this overview for readability.

## Setup

### 1. Clone the repository

```bash
git clone https://github.com/bum-head/GoldShip.git
cd GoldShip
```

Run the following commands from the directory containing `manage.py`.

### 2. Create and activate a virtual environment

On Linux or macOS:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

On Windows PowerShell:

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### 4. Check the project and set up the local database

```bash
python manage.py check
python manage.py migrate
```

The `migrate` command creates Django's standard local database tables. With Django's default settings, the project uses SQLite and does not need a separately running database server.

### 5. Start the development server

```bash
python manage.py runserver
```

Open <http://127.0.0.1:8000/> in your browser.

Available pages:

- Home: <http://127.0.0.1:8000/>
- About: <http://127.0.0.1:8000/about/>
- Django Admin: <http://127.0.0.1:8000/admin/> (requires creating an administrator account first)

To create an administrator account, run:

```bash
python manage.py createsuperuser
```

Stop the development server with `Ctrl+C`.

## Dependencies

The current site only needs Django as an external Python package. Python includes SQLite support, and HTML/CSS do not require separate Python packages.

The `requirements.txt` file should list the Django version/dependency range used by the project. Update it whenever dependencies change so teammates can install the same project requirements.

## Running tests

Run Django's test runner with:

```bash
python manage.py test
```

The current basic site does not yet have a dedicated automated test suite; this command will run any tests added to the project.

## Basic work setup

1. Pull the latest changes from GitHub.
2. Activate your virtual environment.
3. Install any updated dependencies with `python -m pip install -r requirements.txt`.
4. Apply new database migrations with `python manage.py migrate`.
5. Start the site with `python manage.py runserver`.

Commit Django migration files if database models are added later. Do not commit your virtual environment, local secrets, or local database contents.

## Troubleshooting

### `python: command not found`

Depending on your operating system, try `python3` instead of `python`.

### Django cannot be imported

Make sure your virtual environment is activated and install dependencies again:

```bash
python -m pip install -r requirements.txt
```

### The CSS does not load

Check that the stylesheet is located at `pages/static/pages/style.css`, that the template loads Django's static tag library, and that the base template links to `pages/style.css` using the `{% static %}` template tag. The development settings should include `django.contrib.staticfiles` and `DEBUG = True`.

### The server reports a database connection error

The current basic site is intended to use Django's default SQLite configuration. Check the `DATABASES` setting in `Smolpage/settings.py`. If it has been configured for PostgreSQL, PostgreSQL must be running and the configured database credentials must be valid; otherwise restore the default SQLite configuration for local development.

## Project status and next steps

>This is an early-stage project. The immediate goal is to maintain a working, well-documented Django foundation. Potential future features include user accounts, crop listings, regional filtering, buyer-seller inquiries, agricultural guidance, and weather information. These features should be described as implemented only after they are present in the code.

## License

No license has been verified for this repository. Until a `LICENSE` file or explicit license statement is added, do not assume the code is licensed for unrestricted reuse or redistribution.

## Dashboard (weather, location, climate alerts)

The home page is a farm dashboard: location detection (browser GPS, with a state/town picker as fallback),
current weather, humidity, a collapsible map, a 48 h rainfall chart, a 7-day forecast, and automatic
rain / flood alerts with "what to prepare" steps.

- Data: [Open-Meteo](https://open-meteo.com) forecast + GloFAS river-flow APIs (no API key; **non-commercial use only**).
- Alert thresholds live at the top of `pages/static/pages/climate.js` (rainfall classes follow IMD categories).
- Add towns in `pages/regions.py`.
- GPS needs `localhost` or https. The saved location lives in the browser's localStorage only.
- Logic tests (no install needed): `node pages/static/pages/climate.test.js` from the `NetAgri` folder.
- Alerts are model-based estimates, not official warnings.
