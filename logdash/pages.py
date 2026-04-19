from __future__ import annotations

from flask import Flask


def register_page_routes(app: Flask, render_page):
    @app.route("/")
    def index():
        return render_page("index.html", page_title="pipeline monitoring", active_page="index")

    @app.route("/findings")
    def findings():
        return render_page("findings.html", page_title="findings", active_page="findings")

    @app.route("/campaign-setup")
    def campaign_setup():
        return render_page("campaign_setup.html", page_title="campaign setup", active_page="campaign_setup")

    @app.route("/owner-actions")
    def owner_actions():
        return render_page("owner_actions.html", page_title="owner actions", active_page="owner_actions")

    @app.route("/system-settings")
    def system_settings():
        return render_page("system_settings.html", page_title="system settings", active_page="system_settings")
