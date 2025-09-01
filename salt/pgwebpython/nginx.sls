# Salt state for deploying Nginx as reverse proxy (Ubuntu 20+)

nginx:
  pkg.installed:
    - name: nginx

/etc/nginx/sites-available/pgwebpython:
  file.managed:
    - source: salt://pgwebpython/nginx.conf
    - mode: '0644'

/etc/nginx/sites-enabled/pgwebpython:
  file.symlink:
    - target: /etc/nginx/sites-available/pgwebpython
    - require:
      - file: /etc/nginx/sites-available/pgwebpython

# Remove the default site to avoid port 80 conflicts
/etc/nginx/sites-enabled/default:
  file.absent: []

nginx_service:
  service.running:
    - name: nginx
    - enable: True
    - reload: True
    - watch:
      - file: /etc/nginx/sites-available/pgwebpython
      - file: /etc/nginx/sites-enabled/pgwebpython
