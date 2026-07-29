import os
from dotenv import load_dotenv
from . import create_app

load_dotenv('.env.production', override=True)

app = create_app()

if __name__ == '__main__':
    debug_mode = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    app.run(host='0.0.0.0', port=8000, debug=debug_mode)

