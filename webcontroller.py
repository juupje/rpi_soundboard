from flask import render_template
import subprocess
from rpi_soundboard import Controller

result = subprocess.run(['hostname', '-I'], stdout=subprocess.PIPE)
IP = result.stdout.decode("utf-8").split(" ")[0]
MAIN_TEMPLATE = "index.html"
UPLOAD_TEMPLATE = "upload.html"

def create_upload_page():
    return {}

def create_main_page(controller:Controller):
    tables = {"script": ""}
    for s in "ABCD":
        table = "<table class='track_table'><thead><tr><th>Track</th><th>Description</th></tr></thead>"
        tracks = controller.soundboard.get_ntracks(s)
        table += "<tbody>"
        for track in range(tracks):
            table += f"<tr><td>{track+1}</td><td>{controller.soundboard.get_description(s,track):s}</td><td><a onclick='play(\"{s:s}\", {track:d});' class='gg-play-button'></a></td></tr>"
        table += "</tbody></table>"
        tables[f"table_page_{s}"] = table
    return tables

def render_webpage(controller, page:str='home'):
    if page == 'upload':
        d = create_upload_page(controller)
        return render_template(UPLOAD_TEMPLATE, **d)
    else:
        d = create_main_page(controller)
        return render_template(MAIN_TEMPLATE, **d)
    