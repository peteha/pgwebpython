# Salt state for deploying Flask app behind Nginx using gunicorn + systemd

/srv/pgwebpython:
  file.directory:
    - makedirs: True

flask_runtime_pkgs:
  pkg.installed:
    - pkgs:
      - python3-pip
      - python3-venv

# Ship the application artifact (tarball built from this repo)
/srv/pgwebpython/app.tar.gz:
  file.managed:
    - source: salt://pgwebpython/app.tar.gz

# Create venv if missing
flask_create_venv:
  cmd.run:
    - name: python3 -m venv /srv/pgwebpython/venv
    - unless: test -d /srv/pgwebpython/venv
    - require:
      - pkg: flask_runtime_pkgs
      - file: /srv/pgwebpython

# Extract code when tarball changes
flask_extract_code:
  cmd.run:
    - name: tar -xzf /srv/pgwebpython/app.tar.gz -C /srv/pgwebpython/
    - onchanges:
      - file: /srv/pgwebpython/app.tar.gz
    - require:
      - file: /srv/pgwebpython/app.tar.gz

# Install/update Python dependencies (prefers requirements.txt if present) and ensure gunicorn is installed
flask_install_deps:
  cmd.run:
    - name: |
        source /srv/pgwebpython/venv/bin/activate
        if [ -f /srv/pgwebpython/app/requirements.txt ]; then
          pip install -r /srv/pgwebpython/app/requirements.txt
        else
          # Fallback to explicit packages if requirements.txt not present in artifact
          pip install flask flask_sqlalchemy flask_cors psycopg2-binary plotly
        fi
        # Ensure gunicorn is always installed for production serving
        pip install gunicorn
    - require:
      - cmd: flask_create_venv
    - watch:
      - cmd: flask_extract_code

# Manage systemd unit for gunicorn
/etc/systemd/system/pgwebpython.service:
  file.managed:
    - source: salt://pgwebpython/pgwebpython.service
    - mode: '0644'
    - require:
      - cmd: flask_install_deps

# Reload systemd when the unit file changes
systemd-daemon-reload:
  cmd.run:
    - name: systemctl daemon-reload
    - onchanges:
      - file: /etc/systemd/system/pgwebpython.service

# Ensure service is enabled and running; restart on code or unit changes
pgwebpython_service:
  service.running:
    - name: pgwebpython
    - enable: True
    - watch:
      - file: /etc/systemd/system/pgwebpython.service
      - cmd: flask_extract_code
    - require:
      - file: /etc/systemd/system/pgwebpython.service
      - cmd: systemd-daemon-reload
