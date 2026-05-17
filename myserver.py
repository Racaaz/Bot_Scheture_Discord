from flask import Flask
from threading import Thread
import logging

app = Flask('')

@app.route('/')
def home():
    return 'Server is Running!'

def run():
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)
    app.run(host='0.0.0.0', port=8080, debug=False, use_reloader=False)

def server_on():
    t = Thread(target=run)
    t.demon = True
    t.start()
    
    