FROM debian:trixie-slim

RUN apt update && apt install -y curl

RUN cd /tmp && curl -fsSL https://deb.nodesource.com/setup_22.x -o nodesource_setup.sh && bash nodesource_setup.sh

RUN apt install -y --no-install-recommends build-essential python3.12-dev python3.12-venv nodejs && rm -rf /var/lib/apt/lists/*

WORKDIR /srv/app

RUN npm install @babel/parser fs
COPY requirements.pip .
RUN python3 -m venv .env && .env/bin/pip install -r requirements.pip
COPY . .
