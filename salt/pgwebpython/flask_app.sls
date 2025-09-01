# Salt state for deploying Flask app on Ubuntu 20+ using gunicorn + systemd
{% set repo_url = salt['pillar.get']('pgwebpython:url', 'https://github.com/peteha/pgwebpython.git') %}
{% set repo_rev = salt['pillar.get']('pgwebpython:rev', 'main') %}
{% set web_user = 'www-data' %}
{% set web_group = 'www-data' %}

/srv/pgwebpython:
  file.directory:
    - makedirs: True

flask_runtime_pkgs:
  pkg.installed:
    - pkgs:
      - python3
      - python3-venv
      - python3-pip

# Ensure git is present for cloning the repository
git_pkg:
  pkg.installed:
    - name: git

# Clone/update the application from GitHub
repo_checkout:
  git.latest:
    - name: {{ repo_url }}
    - target: /srv/pgwebpython/app
    - rev: {{ repo_rev }}
    - depth: 1
    - force_reset: True
    - clean: True
    - require:
      - pkg: git_pkg
      - file: /srv/pgwebpython

# Create venv if missing
flask_create_venv:
  cmd.run:
    - name: python3 -m venv /srv/pgwebpython/venv
    - creates: /srv/pgwebpython/venv/bin/activate
    - require:
      - pkg: flask_runtime_pkgs
      - file: /srv/pgwebpython

# Install/update Python dependencies and ensure gunicorn is installed
flask_install_deps:
  cmd.run:
    - name: |
        source /srv/pgwebpython/venv/bin/activate
  pip install --upgrade pip setuptools wheel
        pip install -r /srv/pgwebpython/app/requirements.txt
        # Ensure gunicorn is always installed for production serving
        pip install gunicorn
    - require:
      - cmd: flask_create_venv
      - git: repo_checkout
    - watch:
      - git: repo_checkout

# Manage systemd unit for gunicorn
/etc/systemd/system/pgwebpython.service:
  file.managed:
  - source: salt://pgwebpython/pgwebpython.service
    - mode: '0644'
  - template: jinja
  - context:
    web_user: {{ web_user }}
    web_group: {{ web_group }}
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
    - require:
      - file: /etc/systemd/system/pgwebpython.service
      - cmd: systemd-daemon-reload
    - watch:
      - git: repo_checkout
      - cmd: flask_install_deps
      - file: /etc/systemd/system/pgwebpython.service
