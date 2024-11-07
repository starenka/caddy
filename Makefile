MAKEFLAGS += --no-print-directory
USER := $(shell if [ -n "$$USER" ]; then echo "$$USER"; else whoami; fi)
UID := $(shell id -u)
GID := $(shell id -g)
MANAGE := docker run -t -v ./challenges:/srv/app/challenges --user $(UID):$(GID) caddy /srv/app/.env/bin/python /srv/app/manage.py

.SILENT:

manage:
	$(MANAGE) $(args) --username=$(USER)
build:
	docker build -t caddy .
web:
	mkdir -p instance
	docker stop -t5 caddy || docker run --rm -p8888:8000 -v ./instance:/srv/app/instance --user $(UID):$(GID) --name caddy caddy /srv/app/.env/bin/gunicorn --bind 0.0.0.0:8000 web:app
init:
	make build
	mkdir -p challenges
	make manage args=bootstrap
test:
	make manage args=test
submit:
	make manage args=submit
	make manage args=leaderboards
