import collections
import datetime
import hashlib
import os
from pathlib import Path

from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from caddy.caddy import LANGS
from caddy.challenges import CHALLENGES

HERE = Path(__file__).resolve().parent


class Base(DeclarativeBase):
    ...


db = SQLAlchemy(model_class=Base)
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('CADDY_DB', f'sqlite:///{HERE / "instance" / "db.sqlite3"}')
db.init_app(app)


class Submission(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(nullable=False)
    challenge: Mapped[str] = mapped_column(nullable=False)
    language: Mapped[str] = mapped_column(nullable=False)
    src: Mapped[str] = mapped_column(nullable=False)
    src_hash: Mapped[str] = mapped_column(nullable=False)
    chars: Mapped[int] = mapped_column(nullable=False)
    tests_ok: Mapped[bool] = mapped_column(nullable=False)
    stamp: Mapped[datetime.datetime] = mapped_column(default=datetime.datetime.now)

    @property
    def as_dict(self):
        return dict(handle=self.username, chars=self.chars, stamp=self.stamp.isoformat())

    @staticmethod
    def get_src_hash(src):
        return hashlib.md5(src.encode()).hexdigest()

    @staticmethod
    def already_submitted(username, challenge, language, src):
        return db.session.execute(db.select(Submission).filter_by(username=username,
                                                                  language=language,
                                                                  src_hash=Submission.get_src_hash(src),
                                                                  challenge=challenge)).first()

    @staticmethod
    def get_submissions(challenge, language, limit=3):
        return db.session.execute(db.select(Submission)
            .filter_by(language=language,
                       challenge=challenge,
                       tests_ok=True)
            .order_by('chars')
            .limit(limit)).scalars().all()

    @staticmethod
    def get_top_by_challange(language, challenge, limit=1000):
        return db.session.execute(db.select(Submission)
                        .filter_by(tests_ok=True, language=language, challenge=challenge)
                        .order_by('chars', 'stamp')
                        .limit(limit)).scalars().all()


with app.app_context():
    db.create_all()


def check_submission(challenge, language, src):
    challenge, language = CHALLENGES.get(challenge), LANGS.get(language)
    if challenge and language:
        return language['test'](src, challenge), len(src)


@app.route('/submit', methods=['POST'])
def submission():
    username, challenge = request.form['username'], request.form['challenge']
    language, src = request.form['language'], request.form['src']
    ok, chars = check_submission(challenge, language, src)

    if not Submission.already_submitted(username, challenge, language, src):
        sub = Submission(src_hash=Submission.get_src_hash(src), chars=chars, tests_ok=ok, **request.form)
        db.session.add(sub)
        db.session.commit()

    return jsonify({'tests': ok, 'chars': chars, **request.form})


@app.route('/leaderboards')
def leaderboards():
    limit = request.args.get('limit', default=1000, type=int)

    top = {}
    for chcode in CHALLENGES:
        top[chcode] = collections.defaultdict(list)
        for lang in LANGS.keys():
            for one in Submission.get_top_by_challange(lang, chcode, limit=limit):
                top[chcode][lang].append(dict(username=one.username,
                                              chars=one.chars))

    return top
