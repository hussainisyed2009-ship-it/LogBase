#!/usr/bin/env python
"""WSGI entry point for Gunicorn."""
from website import create_app

app = create_app()

if __name__ == '__main__':
    app.run(debug=False)
