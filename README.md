# PGWebPython

A Flask web app to graph Postgres connection times, with API endpoint to write records, auto-refresh (configurable), Nginx reverse proxy, Salt deployment, Monokai Pro theme, and deployment info stored in Postgres.

## Features
- Setup and store Postgres connection info
- Graph connection times (Plotly, up to 1000 points by default)
- API to add/test connection records
- Configurable auto-refresh interval
- Show DB/user info (password visible, admin only)
- Nginx reverse proxy
- Salt deployment states
- Deployment info stored in Postgres for redeployment

## Quickstart
1. Install Python 3, pip, and virtualenv
2. `python3 -m venv venv && source venv/bin/activate`
3. `pip install -r requirements.txt`
4. `FLASK_APP=app/__main__.py flask run`

Tuning:
- Set `MAX_POINTS` env var to change the number of points returned to the chart (default 1000).

## Salt Deployment
- See `salt/pgwebpython/flask_app.sls` and `salt/pgwebpython/nginx.sls` for deployment automation

## Nginx
- See `salt/pgwebpython/nginx.conf` for sample config

## Update workflow (Salt)
1. Push your changes to GitHub (branch `main` by default).
2. On the target host, re-run the Salt states to pull latest and restart as needed:
		- `salt-call state.apply pgwebpython` (includes nginx and app)
		- or `salt-call state.apply pgwebpython.flask_app` (just the app)

Configurable via pillar (optional):

```
pgwebpython:
	url: https://github.com/peteha/pgwebpython.git
	rev: main
```

## Security
- Password is shown in clear text for admin only
- Use HTTPS in production

## Created by Peteha ([GitHub @peteha](https://github.com/peteha))
