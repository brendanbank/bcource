from bcource import create_app
from flask_babel import Babel
from flask import request

app = create_app()

if __name__ == '__main__':
    # Only for debugging while developing
    app.run(host='0.0.0.0', port=5001)
