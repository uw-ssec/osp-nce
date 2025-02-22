import json

import sys
import os

# Adjust the sys.path to include the directory containing path_utils
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'shared')))

import path_utils

PROJECT_ROOT = path_utils.get_project_root()
FORM_INPUTS = os.path.join(PROJECT_ROOT, "src", "shared", "form")
FIELDS_INPUT = os.path.join(FORM_INPUTS, "fields.json")
FIELDS_MAP_INPUT = os.path.join(FORM_INPUTS, "fields_map.json")
FIELDS_MAP_PDF_INPUT = os.path.join(FORM_INPUTS, "fields_map_pdf.json")

class Form:
    
    def __init__(self):
        
        with open(FIELDS_INPUT) as f:
            self.fields = json.load(f)
        
        with open(FIELDS_MAP_INPUT) as f:
            self.fields_map = json.load(f)
            
        with open(FIELDS_MAP_PDF_INPUT) as f:
            self.fields_map_pdf = json.load(f)
        
        # Check if Fields Map keys are a subset of Fields Map PDF keys    
        if not self.fields_map.keys() <= self.fields_map_pdf.keys():
            raise ValueError(
            "There was an error initializing the ERM form. \n"
            "Fields Map keys are not a subset of Fields Map PDF keys.\n"
            "To troubleshoot this, check the fields_map.json and fields_map_pdf.json files in the src/shared/form directory."
            )
            
    def get_fields(self):
        return self.fields
    
    def get_fields_map(self):
        return self.fields_map
    
    def get_fields_map_pdf(self):
        return self.fields_map_pdf
            
    def __main__(self):
        "Testing erm_form.py:"
        print("*" * 50)
        form = Form()
        print("Fields:")
        print(json.dumps(form.fields, indent=4))
        print("Fields Map:")
        print(json.dumps(form.fields_map, indent=4))
        print("Fields Map PDF:")
        print(json.dumps(form.fields_map_pdf, indent=4))

if __name__ == "__main__":
    form = Form()
    form.__main__()