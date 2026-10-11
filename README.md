# GoldShip

GoldShip is a Django web application branded as **NetAgri** in its page templates. It is a regional agricultural platform for North East India: farmers list crops by region, buyers search and contact them, and a weather and climate dashboard helps with day-to-day decisions. The site also includes directories for storage, transport and sourced farming guidance.

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

**Pest watch** (`/resources/pests/report/`)
- Users report pest sightings by region and crop, and the reports are shown to others

**Climate trends** (`/resources/trends/`)
- Average monthly temperature and rainfall, plus yearly rainfall totals, for the last 5 full years in the chosen region
- Modelled historical data from Open-Meteo's archive, cached for 24 hours. It is not a forecast

**Planning insights** (`/resources/advisor/`, login required)
- Summarises a region's wettest, driest, warmest and coolest months and the local median asking price for a crop
- Works without any API. If an AI provider key is set as an environment variable (see `resources/advisor.py`), the question is also sent to an AI model

**Admin**
- Django Admin for regions, listings, inquiries, storage, transport and farming tips

## What is not built yet

- Payments, checkout and delivery tracking
- Stock reservation: accepting an inquiry does **not** reduce a listing's quantity, so an accepted inquiry is an agreement to talk, not a completed sale
- Separate buyer and seller roles: any logged-in user can list crops and send inquiries, except on their own listings
- Storage booking and transport booking (the directories are for browsing and contact only)
- Climate projections: the trends page shows past averages only, and the dashboard and marketplace alert show current conditions and short-term forecasts
- Real AI advice: planning insights are a data summary unless an API key is configured
- Email sending, such as password reset

## Tech stack

- **Python** and **Django 6.1**: backend, templates, authentication, database layer
- **HTML, CSS and JavaScript**: page content, styling and the dashboard
- **Leaflet** with OpenStreetMap tiles: the dashboard map
- **Open-Meteo**: weather data source
- **SQLite**: the default local development database created by Django

PostgreSQL is not required. `psycopg` appears in `requirements.txt`, but the project settings use SQLite.

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
    │   ├── management/commands/seed_regions.py
    │   ├── migrations/
    │   └── templates/marketplace/
    └── resources/                # storage, transport, farming tips
        ├── models.py             # StorageFacility, TransportOffer, FarmingTip
        ├── views.py
        ├── urls.py
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
| `ANTHROPIC_API_KEY` or `OPENAI_API_KEY` | none, optional | Turns on AI mode for planning insights. Use the one matching `resources/advisor.py`. Never commit it. |
| `ADVISOR_MODEL` | provider default | Optional model name for AI mode. |

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

### 7. Add sample data (recommended)

A fresh database is empty. Log in at <http://127.0.0.1:8000/admin/> and add:

- A few crop listings in different regions (or register test users and add them through the site)
- A storage facility and a transport offer
- Farming tips. Each needs a source URL. Use real guidance from agricultural extension sources such as ICAR institutes or the local Krishi Vigyan Kendra. Do not invent doses or practices.

Give your test users an email address in Django Admin, otherwise the contact line after an accepted inquiry shows "(no email on file)".

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


## Rules regarding contributing:
- Commit Django migration files whenever you change a model.
- Do not commit `.env`, your virtual environment, `db.sqlite3`, or `__pycache__` folders. Each developer has their own local database.
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

### The server reports a database connection error

The project is intended to use the default SQLite configuration. Check the `DATABASES` setting in `Smolpage/settings.py`.

## Project status and next steps

The project covers the core journey: a user registers, a seller lists a crop, a buyer finds it by region, sees current weather for the area, and sends an inquiry that the seller can accept. Directories for storage and transport and a sourced farming-tips page are in place.

Planned next steps:
- Merging the dashboard and marketplace weather logic into one approach
- Buyer and seller roles
- Stock handling when inquiries are accepted
- Storage and transport booking
- A production deployment configuration (HTTPS, real email backend, production database)
- Pruning unused dependencies

Features should be described as implemented only after they exist in the code.

## License

No license has been verified for this repository. Until a `LICENSE` file or explicit license statement is added, do not assume the code is licensed for unrestricted reuse or redistribution.
