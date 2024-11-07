#!/usr/bin/env python3

from pathlib import Path

import click
import tabulate
from art import text2art

from caddy.caddy import (SERVER, bootstrap_challanges, get_leaderboards,
                         submit_implementations, test_implementations)
from caddy.challenges import CHALLENGES, WELCOME
from caddy.utils import get_user

HERE = Path(__file__).resolve().parent
PATH_CHALLENGES = HERE / 'challenges'


@click.group
def cli():
    ''' caddy CLI '''


@cli.command
@click.option('--path', help='challenges path', default=PATH_CHALLENGES)
@click.option('--username', help='username', default=lambda: get_user())
def test(path, username):
    ''' discover & test challenge attempts '''
    test_implementations(Path(path))


@cli.command
@click.option('--path', help='challenges path', default=PATH_CHALLENGES)
@click.option('--username', help='username', default=lambda: get_user())
@click.option('--server', help='submission server URL', default=SERVER)
def submit(path, username, server):
    ''' submits challange files '''

    submit_implementations(Path(path), username=username, server=server)


@cli.command
@click.option('--server', help='submission server URL', default=SERVER)
@click.option('--limit', help='limit to top x', default=10, type=int)
def leaderboards(server, limit):
    ''' shows leaderboards '''

    scores = get_leaderboards(server=server, limit=limit)

    for ch, lang in scores.items():
        if challenge := CHALLENGES.get(ch):
            print(text2art(challenge['name']))
            print(tabulate.tabulate({l: [f'{sub["chars"]}: {sub["username"]}'
                                         for sub in s]
                                     for l, s in lang.items()},
                                    headers='keys', tablefmt='outline'))


@cli.command
@click.option('--path', help='challenges path', default=PATH_CHALLENGES)
@click.option('--username', help='username', default=lambda: get_user())
def bootstrap(path, username):
    ''' bootstraps challange files '''
    bootstrap_challanges(Path(path))
    print(WELCOME.format(user=username))

if __name__ == '__main__':
    cli()
