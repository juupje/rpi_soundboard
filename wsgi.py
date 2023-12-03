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
ns_play = api.namespace('play', description="Play sounds!")

@app.route("/home", strict_slashes=False)
def webpage_home():
    importlib.reload(webcontroller)
    return webcontroller.render_webpage(controller, page='home')
@app.route("/upload", strict_slashes=False)
def webpage_upload():
    importlib.reload(webcontroller)
    return webcontroller.render_webpage(controller, page='upload')

@ns_play.route("/<string:page>/<int:track>")
@ns_play.response(404, 'LED not found')
@ns_play.param('led_id', 'The LED identifier')
class PlaySound(Resource):
    def post(self, page:str, track:int):
        try:
            if(controller.soundboard.play_sound(page, track)):
                return {"success": True}
            return {"success": False, "message": "Sound effect doesn't exist."}
        except Exception as e:
            return {"success": False, "message": e.message()}
        
    def get(self, page:str, track:int):
        desc = controller.soundboard.get_description(page, track)
        return {"success": True, "description": desc} if desc else {"success": False}

@ns_rpi.route("/")
class RPIInformation(Resource):
    def post(self):
        data = api.payload
        if("option" in data):
            cwd = os.getcwd()
            option = data["option"]
            if(option in ["reboot", "shutdown"]):
                print("Stopping...")
                controller.cleanup()
                command = f"sudo /sbin/{option} -h now"
                import subprocess
                process = subprocess.Popen(command.split(), stdout=subprocess.PIPE)
                output = process.communicate()[0]
                print(output)
                return {"success": True, "message": output}
            else:
                return {"success": False, "message": "Unknown option"}
        return {"success": False, "message": "Invalid command"}


import signal
controller = Controller()
signal.signal(signal.SIGINT, controller.cleanup)
if __name__ =="__main__":
    app.run()