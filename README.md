# NetAgri

NetAgri is a Django web application (the repository is named GoldShip). It is a regional agricultural platform for North East India: farmers list crops by region, buyers search and contact them, and a weather and climate dashboard helps with day-to-day decisions. The site also includes directories for storage, transport and sourced farming guidance.

It was built around four problem areas: market connectivity, climate variability, post-harvest management and agricultural productivity. The whole area is split into regions (towns and districts), and most features are filtered by region.

## Current features

**Accounts**
- Registration with username, email and password (the email is shared with the other party only after an inquiry is accepted)
- Login and logout using Django's built-in authentication

**Crop marketplace**
- Browse available crops, with search by crop name and filter by region
- Sellers add, edit and mark their own crops as sold
- Sold crops disappear from the public marketplace
- A current-weather alert for the selected region, shown above the listings

**Buyer inquiries**
- Buyers send an inquiry (quantity and message) about a listing
- Sellers accept or decline inquiries
- Contact emails are revealed to both sides once an inquiry is accepted

**Weather and climate dashboard** (`/dashboard/`)
- Map with a state and place picker for the North Eastern states
- Weather, forecast and flood information for the chosen location

**Resources** (`/resources/`)
- Storage facility directory (post-harvest management)
- Transport offers by origin and destination
- Farming tips by crop and region, each with a required source link

**Price insights**
- Each listing page compares the asking price with the median asking price of other listings of the same crop (same region when there are at least 3 comparables, otherwise all regions; no comparison with fewer than 3)
- Stock value and inquiry totals are shown in rupees, and "My listings" shows total active stock value and the value of accepted inquiries
- These are asking prices, not market rates or confirmed sales. Crop names are free text, so "Rice" and "Paddy" do not match

**Pest watch** (`/resources/pests/`)
- Users report pest sightings by region and crop, and the reports are shown to others

**Climate trends** (`/resources/trends/`)
- Average monthly temperature and rainfall, plus yearly rainfall totals, for the last 5 full years in the chosen region
- Modelled historical data from Open-Meteo's archive, cached for 24 hours. It is not a forecast

**Planning insights** (`/resources/advisor/`, login required)
- Summarises a region's wettest, driest, warmest and coolest months and the local median asking price for a crop
- Works without any API. If an AI provider key is set as an environment variable (see `resources/advisor.py`), an AI model answers the question instead of the summary

**Demo data** (`python manage.py seed_demo`, development and demo sites only)
- Fills a database with invented sample users, listings, inquiries, storage, transport, tips and pest reports, all clearly marked as demo. See [Demo data and the demo site](#demo-data-and-the-demo-site)

**Admin**
- Django Admin for regions, listings, inquiries, storage, transport, farming tips and pest reports. Staff review pest reports and add an advisory with a source before they appear publicly

## What is not built yet

- Payments, checkout and delivery tracking
- Stock reservation: accepting an inquiry does **not** reduce a listing's quantity, so an accepted inquiry is an agreement to talk, not a completed sale
- Separate buyer and seller roles: any logged-in user can list crops and send inquiries, except on their own listings
- Storage booking and transport booking (the directories are for browsing and contact only)
- Climate projections: the trends page shows past averages only, and the dashboard and marketplace alert show current conditions and short-term forecasts
- Real AI advice: planning insights are a data summary unless an API key is configured
- Email sending, such as password reset
- Login throttling: nothing limits repeated password guesses on `/accounts/login/` or `/admin/`
- Production security settings: secure cookies, forced HTTPS and HSTS are not configured (see [Before you deploy](#before-you-deploy))
- Rate limiting on planning insights: when an AI key is set, any logged-in user can trigger paid API calls
- A visible "demo site" notice on the pages

## Tech stack

- **Python** and **Django 6.1**: backend, templates, authentication, database layer
- **HTML, CSS and JavaScript**: page content, styling and the dashboard
- **Leaflet** with OpenStreetMap tiles: the dashboard map
- **Open-Meteo**: weather data source
- **SQLite**: the default local development database created by Django

PostgreSQL is not required. `psycopg` appears in `requirements.txt`, but the project settings use SQLite.

## External services and APIs

NetAgri calls these external services. Only the OpenAI one needs a key, and it is optional.

| Service | Endpoint | Used for | Called from | Key needed |
|---|---|---|---|---|
| Open-Meteo Forecast API | `https://api.open-meteo.com/v1/forecast` | Current conditions and short-term forecast: the marketplace weather alert (server, `pages/climate_service.py`; the URL can be overridden with `WEATHER_API_URL`) and the dashboard (browser, `climate.js`) | Server and browser | No |
| Open-Meteo Flood API (GloFAS) | `https://flood-api.open-meteo.com/v1/flood` | River discharge and flood information on the dashboard | Browser (`climate.js`) | No |
| Open-Meteo Historical Weather API | `https://archive-api.open-meteo.com/v1/archive` | Five years of daily history for the climate trends page and planning insights | Server (`resources/trends.py`) | No |
| OpenAI Chat Completions API | `https://api.openai.com/v1/chat/completions` | Optional AI answers on the planning insights page | Server (`resources/advisor.py`) | Yes, `OPENAI_API_KEY` |
| OpenStreetMap tile server | `https://tile.openstreetmap.org/{z}/{x}/{y}.png` | Map background on the dashboard | Browser (Leaflet) | No |

Also loaded from the internet, but not an API: the Leaflet library (CSS and JavaScript) from `https://unpkg.com/leaflet@1.9.4/`, on the dashboard page.

Things to know:
- Open-Meteo's free service is for non-commercial use. Check its terms before any commercial deployment.
- Dashboard requests come from the visitor's browser, so Open-Meteo and the tile server see the visitor's IP address and the coordinates of the chosen place.
- If an OpenAI key is set, the selected region, its climate averages, the crop's local median asking price and the question the user typed (up to 500 characters) are sent to OpenAI. Do not type personal details into that box.
- If any service is unreachable, the related feature shows a message or hides itself. Planning insights falls back to the local summary.

## Requirements

- Python 3.12 or newer (Django 6.1 supports Python 3.12, 3.13 and 3.14)
- `pip`
- Git
- An internet connection when using the dashboard or the marketplace weather alert (weather data, map tiles and the Leaflet library are loaded from external services)
- Node.js, only if you want to run the dashboard's JavaScript tests (optional)

## Project structure

```
GoldShip/
├── README.md
├── requirements.txt
├── .gitignore
└── NetAgri/
    ├── manage.py
    ├── .env                      # local settings, NOT committed
    ├── Smolpage/                 # project settings and root URLs
    │   ├── settings.py
    │   ├── urls.py
    │   ├── asgi.py
    │   └── wsgi.py
    ├── pages/                    # home, about, register, dashboard
    │   ├── views.py
    │   ├── urls.py
    │   ├── forms.py              # registration form with email
    │   ├── regions.py            # North East places and coordinates
    │   ├── climate_service.py    # server-side weather fetch and rating
    │   ├── templates/pages/      # base.html, home.html, about.html,
    │   │                         # register.html, dashboard.html, login
    │   └── static/pages/         # style.css, dashboard.css,
    │                             # dashboard.js, climate.js, climate.test.js
    ├── marketplace/              # crops, regions, inquiries
    │   ├── models.py             # Region, CropListing, Inquiry
    │   ├── views.py
    │   ├── forms.py
    │   ├── urls.py
    │   ├── weather.py            # cached region weather alert
    │   ├── pricing.py            # price check against similar listings
    │   ├── geo.py                # distance between regions
    │   ├── test_pricing.py
    │   ├── management/commands/seed_regions.py   # real reference data: required everywhere
    │   ├── management/commands/seed_demo.py      # invented sample data: development and demo sites only
    │   ├── migrations/
    │   └── templates/marketplace/
    └── resources/                # storage, transport, farming tips
        ├── models.py             # StorageFacility, TransportOffer, FarmingTip, PestReport
        ├── views.py
        ├── urls.py
        ├── pest_views.py         # pest reports
        ├── trends.py             # Open-Meteo history, monthly averages
        ├── trend_views.py        # climate trends page
        ├── advisor.py            # planning insights, optional AI call
        ├── advisor_views.py
        ├── test_trends.py
        ├── test_advisor.py
        └── templates/resources/
```

Django creates additional files inside each app (for example `apps.py` and `__init__.py`); they are omitted here for readability.

## Pages and URLs

| URL | What it does | Login needed |
|---|---|---|
| `/` | Home page | No |
| `/about/` | About page | No |
| `/dashboard/` | Weather and climate dashboard with map | No |
| `/register/` | Create an account | No |
| `/accounts/login/` | Log in | No |
| `/crops/` | Browse crops (`?region=<id>&q=<text>`) | No |
| `/crops/add/` | Add a crop listing | Yes |
| `/crops/mine/` | Manage your own listings | Yes |
| `/crops/listing/<id>/edit/` | Edit your listing | Yes (owner only) |
| `/crops/listing/<id>/sold/` | Mark your listing as sold (POST only) | Yes (owner only) |
| `/crops/listing/<id>/inquire/` | Send an inquiry about a listing | Yes |
| `/crops/inquiries/` | Inquiries you sent and received | Yes |
| `/crops/inquiries/<id>/respond/` | Accept or decline an inquiry (POST only) | Yes (seller only) |
| `/resources/storage/` | Storage facility directory | No |
| `/resources/transport/` | Transport offers | No |
| `/resources/tips/` | Farming tips | No |
| `/resources/pests/` | Pest watch: reports by region | No |
| `/resources/pests/report/` | Report a pest | Yes |
| `/resources/trends/` | Historical climate trends (`?region=<id>`) | No |
| `/resources/advisor/` | Planning insights | Yes |
| `/admin/` | Django Admin | Staff account |

## Data model

- **Region**: name, district (optional), state, latitude and longitude. Loaded from `pages/regions.py` by the `seed_regions` command.
- **CropListing**: seller, region, crop name, variety, quantity (kg), price per kg, status (available or sold), created time.
- **Inquiry**: buyer, listing, requested quantity (kg), message, status (pending, accepted or declined), created time.
- **StorageFacility**: name, type, region, capacity, contact, notes.
- **TransportOffer**: provider, origin region, destination region, vehicle type, capacity, available-from date, contact, notes.
- **FarmingTip**: crop name, optional region, season, content, required source URL, updated time.
- **PestReport**: reporter, region, crop name, observed on, symptoms, status, advisory, source url, created at.

## Setup

### 1. Clone the repository

```bash
git clone https://github.com/bum-head/GoldShip.git
cd GoldShip
```

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

Run this from the repository root, where `requirements.txt` lives:

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### 4. Create your local settings file

The project reads its secret key and debug flag from a `.env` file inside `NetAgri/`. Without it, Django refuses to start with `Set the SECRET_KEY environment variable`.

On Linux or macOS:

```bash
cd NetAgri
printf 'DEBUG=True\nSECRET_KEY=%s\n' "$(python -c 'import secrets; print(secrets.token_urlsafe(50))')" > .env
```

On Windows, generate a key with `python -c "import secrets; print(secrets.token_urlsafe(50))"`, then create `NetAgri\.env` containing these two lines:

```
DEBUG=True
SECRET_KEY=paste-the-generated-key-here
```

Supported settings:

| Variable | Default | Meaning |
|---|---|---|
| `SECRET_KEY` | none, required | Django's signing key. Every machine should have its own. |
| `DEBUG` | `False` | Use `True` for local development only. |
| `ALLOWED_HOSTS` | `localhost,127.0.0.1` | Comma-separated hosts the site may be served on. |
| `OPENAI_API_KEY` | none, optional | Turns on AI answers for planning insights. Never commit it. |
| `ADVISOR_MODEL` | `gpt-4o-mini` | Optional OpenAI model name for AI mode. |
| `WEATHER_API_URL` | Open-Meteo forecast URL | Optional override for the server-side weather source. |
| `DATABASE_PATH` | `NetAgri/db.sqlite3` | Path of the SQLite database file. Set it to give a demo site, or a local demo, its own database. Never commit database files. |

Never commit `.env`. It is listed in `.gitignore`.

### 5. Check the project and set up the database

Run the following from the `NetAgri/` directory (the one containing `manage.py`):

```bash
python manage.py check
python manage.py migrate
python manage.py seed_regions
python manage.py createsuperuser
```

- `migrate` creates all tables in a local SQLite file, `db.sqlite3`.
- `seed_regions` loads the North East places and coordinates into the `Region` table. Without it, the region dropdowns are empty. It is safe to run more than once.
- `createsuperuser` creates the administrator account for `/admin/`.

### 6. Start the development server

```bash
python manage.py runserver
```

Open <http://127.0.0.1:8000/> in your browser. Stop the server with `Ctrl+C`.

### 7. Add demo data (optional, development only)

A fresh database is empty. To fill it with invented sample data, run this from `NetAgri/`:

```bash
python manage.py seed_demo
```

It prints a password for the demo accounts (`demo_seller` and `demo_buyer` are the two to log in with). Read [Demo data and the demo site](#demo-data-and-the-demo-site) before using it anywhere except your own machine. Never run it against a production database.


## Demo data and the demo site

The `seed_demo` command fills a database with a large set of **invented** sample data, so every page has something to show. It is for development machines and separate demo sites only.

### What it creates

About 195 crop listings across 20 crops and 13 regions (some already sold), 18 accounts, about 40 inquiries in all three states, 12 storage facilities, 14 transport offers, 10 farming tips and 16 pest reports (about two thirds reviewed, so they appear publicly). Usernames start with `demo_`, emails use `example.com`, and storage, transport and tip records are marked "Demo". The data is generated with a fixed seed, so every run produces the same result.

### Commands

Run these from `NetAgri/`, after `migrate` and `seed_regions`:

```bash
python manage.py seed_demo                   # create the data (refuses if demo data already exists)
python manage.py seed_demo --reset           # delete the old demo data, then create it again
python manage.py seed_demo --password XYZ    # choose the password shared by all demo accounts
python manage.py seed_demo --demo-site       # only for a separate demo deployment where DEBUG is off
```

If you do not pass `--password`, a random one is printed once at the end. Log in as `demo_seller` (a Jorhat seller with many listings and inquiries) or `demo_buyer`.

### Warnings

- **Everything is invented.** Prices, quantities, contacts, pest reports and tips are made up. Say so when you show it. The tips are placeholders marked "[Demo]" that point to the ICAR home page. Replace them with real, sourced guidance before real use.
- **Never put demo data in a production database.** Fake prices would feed the real price check and planning insights, real buyers could contact sellers who do not exist, and all demo accounts share one password. For this reason `seed_demo` refuses to run when `DEBUG` is off unless you add `--demo-site`.
- **The shared password is a risk on any public server.** Use a strong one with `--password` and give it only to people who ask to see the demo.
- **Do not commit databases.** `*.sqlite3` is listed in `.gitignore`. Keep it that way, demo databases included.
- **`--reset` and the clean-up below only touch records marked as demo**: usernames starting with `demo_`, and storage, transport and tip records marked "Demo". Do not give a real account a `demo_` username.
- **Deleting `seed_demo.py` does not remove the data.** The records live in the database file.

### Removing demo data

From `NetAgri/`:

```bash
python manage.py shell -c "
from django.contrib.auth import get_user_model
from resources.models import StorageFacility, TransportOffer, FarmingTip
get_user_model().objects.filter(username__startswith='demo_').delete()
StorageFacility.objects.filter(name__startswith='Demo ').delete()
TransportOffer.objects.filter(provider__startswith='Demo ').delete()
FarmingTip.objects.filter(content__startswith='[Demo]').delete()
"
```

Deleting the demo users also deletes their listings, inquiries and pest reports. Regions are kept, because they are real reference data. Real accounts are untouched.

### Showing the demo on your own machine

To keep your development database clean, give the demo its own database file. Run these from `NetAgri/`, because a relative path is resolved from the folder you run in.

On Linux or macOS:

```bash
export DATABASE_PATH=demo.sqlite3
```

On Windows PowerShell:

```powershell
$env:DATABASE_PATH="demo.sqlite3"
```

Then:

```bash
python manage.py migrate
python manage.py seed_regions
python manage.py seed_demo
python manage.py runserver
```

To go back to your normal database, unset the variable (`unset DATABASE_PATH`, or `Remove-Item Env:DATABASE_PATH` in PowerShell). Before presenting, open the climate trends page for the regions you will show: the first load fetches five years of history and is slow, then it is cached for 24 hours. Planning insights works without an AI key.

### Running a public demo site

Visitors who want to see the demo should get a **separate deployment** with its own database, never the production site.

1. Deploy the same code a second time, for example at `demo.example.org`.
2. Give it its own `.env`: a **different** `SECRET_KEY` from production, `ALLOWED_HOSTS` set to the demo domain, and `DATABASE_PATH` pointing to its own SQLite file on persistent storage.
3. On that deployment only, run `python manage.py migrate`, `python manage.py seed_regions`, then `python manage.py seed_demo --demo-site --password <a strong password>`.
4. Leave `OPENAI_API_KEY` unset so the demo cannot run up an API bill. Planning insights then shows the free summary.
5. Re-run `seed_demo --demo-site --reset` now and then, because anyone with the password can add junk.
6. Add a visible "demo site, sample data" notice to the pages so nobody mistakes it for the real service. This is not built in yet.
7. Never copy real user data into it, and never copy demo data into production.

## How the weather features work

There are two separate weather implementations:

1. **Dashboard** (`/dashboard/`): the page's JavaScript (`pages/static/pages/climate.js` and `dashboard.js`) fetches forecast and flood data directly from public weather APIs in the browser. It also caches the last result locally in the browser.
2. **Marketplace alert**: when you filter `/crops/` by region, the server (`pages/climate_service.py`, `marketplace/weather.py`) fetches the **current conditions** for that region's coordinates from Open-Meteo, rates them from Good to Bad, and caches the result for 10 minutes. If the weather service is unavailable, the alert is simply hidden.

The two use different data and scoring, so they can disagree. Merging them into one approach is a planned improvement.

A third, separate piece is the **climate trends** page (`/resources/trends/`). The server (`resources/trends.py`) fetches five years of daily history from Open-Meteo's archive, averages it by month and caches it for 24 hours. It shows past averages, not forecasts.

The server-side rating starts at 100 and subtracts points for temperature outside 15 to 30 °C, wind above 15 km/h, precipitation, very high or low humidity, and the weather condition code. Scores of 80 or more are Good, 60 to 79 Fair, 40 to 59 Poor, and below 40 Bad.

## Running tests

From `NetAgri/`:

```bash
python manage.py test
```

This runs the Python test suites for the marketplace (region filter, inquiries, seller permissions), registration, the climate rating, price insights, climate trends and planning insights.

The dashboard's JavaScript has its own tests, which need Node.js:

```bash
node pages/static/pages/climate.test.js
```


## Before you deploy

For a real deployment, run only these data commands:

```bash
python manage.py migrate
python manage.py seed_regions      # required reference data, not demo data
python manage.py createsuperuser
```

Do **not** run `seed_demo` on a production database. Use a separate demo site instead (see above).

The repository is set up for local development. The items below are **not configured yet** and should be done before real users rely on the site:

- Set `DEBUG=False`, a unique `SECRET_KEY` and the real `ALLOWED_HOSTS` in the server's environment. Never reuse a development or demo key.
- Serve the site over HTTPS and add `SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE`, `SECURE_SSL_REDIRECT` and HSTS settings. Run `python manage.py check --deploy` and fix what it reports.
- Add login throttling (for example `django-axes`) and move the admin away from the default `/admin/` path.
- Rate-limit planning insights, or leave `OPENAI_API_KEY` unset, so users cannot run up an API bill.
- Replace SQLite with a production database, set up a real email backend, and configure static file serving (there is no `STATIC_ROOT` yet).
- Check Open-Meteo's terms: its free service is for non-commercial use.
- Keep secrets out of git. A key or database committed once stays in the history even after it is deleted, so treat it as leaked and replace it.

## Rules regarding contributing:
- Commit Django migration files whenever you change a model.
- Do not commit `.env`, your virtual environment, any `*.sqlite3` database file (demo databases included), or `__pycache__` folders. Each developer has their own local database.
- Never commit API keys or passwords. If one is committed by mistake, treat it as leaked and replace it: deleting it in a later commit does not remove it from the history.
- Work on a branch and open a pull request instead of pushing to `master` directly.

If you had a copy of this repository from before the database file was removed from version control, pulling may delete your local `db.sqlite3`. Copy it somewhere first if it holds data you need, then run `migrate`, `seed_regions` and `createsuperuser` again.

## Dependencies

`requirements.txt` pins exact versions, including Django 6.1.2 and `django-environ` (for reading `.env`). It also lists several packages the current code does not appear to use, such as `pandas`, `numpy`, `pydantic`, `pillow` and `psycopg`. They are harmless but slow down installation, and they can be pruned once the team confirms nothing needs them. Update `requirements.txt` whenever a dependency is added or removed.

## Troubleshooting

### `Set the SECRET_KEY environment variable`

The `.env` file is missing or in the wrong folder. It must be at `NetAgri/.env`, next to `manage.py`, not in the repository root. See step 4 of Setup.

### `no such table: ...` (for example `auth_user` or `marketplace_region`)

The database has not been migrated. From `NetAgri/`, run `python manage.py migrate`.

### The region dropdown is empty

Run `python manage.py seed_regions`.

### `python: command not found`

Depending on your operating system, use `python3` instead of `python`.

### Django cannot be imported

Make sure your virtual environment is activated, then reinstall dependencies from the repository root:

```bash
python -m pip install -r requirements.txt
```

### `Could not open requirements file`

Run the install command from the repository root, where `requirements.txt` is located, not from inside `NetAgri/`.

### The dashboard shows no map, or the dropdowns do nothing

- Check your internet connection. The map library and tiles load from external servers.
- Hard refresh the page (Ctrl+Shift+R).
- Open the browser developer tools (F12) and look at the Console and Network tabs for errors or files returning 404 or 403.
- Map tiles can be blocked if Django does not send a referrer. `Smolpage/settings.py` sets `SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'` for this reason, so do not remove it.

### The CSS or JavaScript does not load

Static files are served by Django's development server only when `DEBUG=True`. Check your `.env` file. Files live under `pages/static/pages/`.

### The marketplace weather alert does not appear

The alert shows only after you choose a region. The region must have coordinates (run `seed_regions`) and the server must be able to reach the weather service. If the service is down, the alert is hidden on purpose.

### "(no email on file)" after accepting an inquiry

The user has no email address. New registrations require one. For older accounts, add an email in Django Admin.

### `Demo data already exists. Run with --reset to replace it.`

`seed_demo` found accounts starting with `demo_`. Run `python manage.py seed_demo --reset` to delete the old demo data and create it again.

### `Refusing to create demo data while DEBUG is off`

This is a safeguard: `DEBUG` is off, so the command assumes this is a real deployment. Only add `--demo-site` if this is a separate demo site that holds no real data.

### I can see demo data on a site that should be real

Remove it with the clean-up commands in [Removing demo data](#removing-demo-data), then check how the data got there. Demo data must never share a database with real users.

### The server reports a database connection error

The project is intended to use the default SQLite configuration. Check the `DATABASES` setting in `Smolpage/settings.py`, and the `DATABASE_PATH` variable if you set one.

## Project status and next steps

The project covers the core journey: a user registers, a seller lists a crop, a buyer finds it by region, sees current weather for the area, and sends an inquiry that the seller can accept. Directories for storage and transport and a sourced farming-tips page are in place.

Planned next steps:
- Merging the dashboard and marketplace weather logic into one approach
- Buyer and seller roles
- Stock handling when inquiries are accepted
- Storage and transport booking
- A production deployment configuration (HTTPS, real email backend, production database)
- Login throttling, secure cookie settings and rate limiting on planning insights (see [Before you deploy](#before-you-deploy))
- A visible "demo site" notice
- Pruning unused dependencies

Features should be described as implemented only after they exist in the code.

## License

No license has been verified for this repository. Until a `LICENSE` file or explicit license statement is added, do not assume the code is licensed for unrestricted reuse or redistribution.
