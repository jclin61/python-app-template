# Copyright 2020 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from flask import session, request, redirect, url_for
from flask_babel import Babel
import os
import re
import unicodedata

import flask
import markupsafe
import mistune
import securescaffold


app = securescaffold.create_app(__name__)
app.config.from_pyfile('config.py')
babel = Babel(app)


@app.route("/")
def about():
    """One-page introduction to Secure Scaffold.

    This renders Markdown to HTML on-the-fly, trusting the Markdown content
    can be used to generate <a> tags. Do not do this on production sites!
    """

    # The Anchors renderer trusts the headers in the Markdown file.
    with open("README-secure-scaffold.md") as fh:
        m = mistune.Markdown(renderer=Anchors())
        readme = m.render(fh.read())
        readme = markupsafe.Markup(readme)

    context = {
        "page_title": "Secure Scaffold",
        "readme": readme,
    }

    return flask.render_template("about.html", **context)


@app.route("/csrf", methods=["GET", "POST"])
def csrf():
    """Demonstration of using CSRF to protect a form."""
    context = {
        "page_title": "CSRF protection",
        "message": "",
    }

    if flask.request.method == "POST":
        first_name = flask.request.form.get("first-name")

        if first_name:
            context["message"] = f"Hello {first_name}!"

    return flask.render_template("csrf.html", **context)


@app.route("/headers")
def headers():
    """Show HTTP headers for the request."""
    context = {
        "page_title": "App Engine request headers",
        "headers": list(flask.request.headers),
    }

    return flask.render_template("headers.html", **context)


class Anchors(mistune.Renderer):
    """Adds id attributes to <h*> elements.

    This is not safe if you cannot trust the Markdown content.
    """

    def header(self, text, level, raw=None):
        name = self.choose_name(text)
        class_ = f"title is-{level}"

        return f'<h{level} id="{name}" class="{class_}">{text}</h{level}>'

    def choose_name(self, text):
        text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore")
        text = re.sub(r"[^\w\s-]", "", text.decode("ascii")).strip().lower()
        text = re.sub(r"[-\s]+", "-", text)

        return text

@app.route('/language/<language>')
def set_language(language=None):
    session['language'] = language
    return redirect(url_for('about'))

# Use the browser's language preferences to select an available translation
@babel.localeselector
def get_locale():
    # if the user has set up the language manually it will be stored in the session,
    # so we use the locale from the user settings
    try:
        language = session['language']
    except KeyError:
        language = None
    if language is not None:
        return language
    return request.accept_languages.best_match(app.config['LANGUAGES'])

@app.context_processor
def inject_conf_var():
    return dict(
                AVAILABLE_LANGUAGES=app.config['LANGUAGES'],
                CURRENT_LANGUAGE=session.get('language',request.accept_languages.best_match(app.config['LANGUAGES'])))

app.jinja_env.globals['get_locale'] = get_locale