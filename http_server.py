import socket
import time
import datetime

from flask import Flask, jsonify

VERSION = '0.01'

app = Flask(__name__)

@app.route('/api/time')
def get_host_time():
    return jsonify({'time': str(datetime.datetime.utcnow())})

@app.route('/api/host_info')
def get_host_info():
    info = {'hostname': socket.gethostname(),
            'ip_address': socket.gethostbyname(socket.gethostname()),
            }
    return jsonify(info)

@app.route('/api/')
def get_api_info():
    return jsonify({'version': VERSION})

if __name__ == '__main__':
    app.run()



