#!/usr/bin/env python3

from bcource import create_app

app = create_app()

if __name__ == '__main__':
    # Only for debugging while developing
    if app.config.get('ENVIRONMENT') == "TESTING":
        app.run(host='0.0.0.0', port=5002, ssl_context=('cert.pem', 'key.pem'))
    else:
        app.run(host='0.0.0.0', port=5001)

