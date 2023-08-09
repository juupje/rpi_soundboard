#!/home/pi/Documents/environments/flask-wsgi/bin/python3
import sys, os, subprocess, io
import werkzeug
werkzeug.cached_property = werkzeug.utils.cached_property
from flask import Flask, render_template, request
from flask_restplus import Api, Resource, fields
import importlib 
import webcontroller
from rpi_soundboard import Controller
app = Flask(__name__, template_folder='web/templates', static_folder='web/static')

api = Api(app, version="1.0", title="Soundboard", description="A RESTful API to control a soundboard",
          doc="/docs")

ns_rpi = api.namespace('rpi', description="Raspberry Pi related operations")

@app.route("/home", strict_slashes=False)
def webpage():
    importlib.reload(webcontroller)
    return webcontroller.render_webpage(animation=request.args.get("animation", default=None, type=str))

@ns_rpi.route("/")
class RPIInformation(Resource):
    def post(self):
        data = api.payload
        if("option" in data):
            cwd = os.getcwd()
            option = data["option"]
            if(option in ["kill", "reboot", "shutdown"]):
                cmd = ["bash", f"{cwd:s}/shutdown", option]
                with open("output.txt", "w+") as file:
                    subprocess.run(cmd, stdout=file)         
                    print("Executed command '" + " ".join(cmd));#
                    file.seek(io.SEEK_SET)
                    last_line = ""
                    output = ""
                    for line in file:
                        output += line
                        last_line = line.strip()
                    print("Got response '" + last_line +"'")
                    if(last_line == option):
                        return {"success": True}
                    else:
                        return {"success": False, "message": output}
        return {"success": False, "message": "Unknown option"}

if __name__=="__main__":
    import signal
    controller = Controller()
    signal.signal(signal.SIGINT, controller.cleanup)
    app.run()