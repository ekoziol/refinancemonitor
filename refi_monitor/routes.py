"""Routes for parent Flask app."""
import os
from flask import render_template
from flask import current_app as app
from flask import send_from_directory


@app.route('/')
def home():
    """Landing page."""
    return render_template(
        'index.jinja2',
        title='Refinance Monitor',
        description='Set it and forget it!',
        template='home-template',
        body="We watch mortgage rates so you don't have to",
    )


@app.route('/setalert/')
def setalert():
    """Set alert page"""
    return render_template(
        'setalert.jinja2',
        title='Set Refinance Alert',
        description='Set your alert!',
        template='home-template',
        body="We watch mortgage rates so you don't have to",
    )


@app.route('/favicon.ico')
def favicon():
    return send_from_directory(
        os.path.join(app.root_path, 'static'),
        'favicon.ico',
        mimetype='image/vnd.microsoft.icon',
    )
