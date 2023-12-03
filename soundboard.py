import json
import os
import subprocess

JSON_FILE = "audio/files.json"

class Soundboard:
    def __init__(self):
        if(os.path.exists(JSON_FILE)):
            with open(JSON_FILE, 'r') as file:
                self.doc = json.load(file)
        else:
            self.doc = {}
            with open(JSON_FILE, 'w') as file:
                json.dump(self.doc, file)
    
    def page_exists(self, page:str):
        return page in self.doc

    def reload(self):
        with open(JSON_FILE, 'r') as file:
            self.doc = json.load(file)
    
    def get_ntracks(self, page:str):
        try:
            return len(self.doc[page])
        except KeyError:
            return 0

    def get_description(self, page:str, track:int):
        try:
            print(f"{page}/{track}")
            desc = self.doc[page][track]["name"]
        except KeyError:
            return False
        return desc

    def play_sound(self, page, track):
        # see if it exists
        try:
            file = self.doc[page][track]["file"]
        except KeyError:
            print(f"Unknown page and track combination {page}/{track}")
            return False
        path = f"audio/"+file
        if(os.path.exists(path)):
            subprocess.Popen(["mpg123", os.path.abspath(path)], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            return True
        else:
            raise ValueError(f"File '{path}' does not exist")
        return False