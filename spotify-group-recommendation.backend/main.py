

from flask import Flask, request
from flask_cors import CORS, cross_origin

import ml_main

app = Flask(__name__)
@app.route("/token", methods=["POST"])
@cross_origin()
def token():
    token = request.args.get("token")[9:][:-9].split("separator")
    return {"success": ml_main.mainly(token)}

if __name__ == "__main__":
    app.run()
