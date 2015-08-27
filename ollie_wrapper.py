# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
"""
import subprocess
import pandas
import StringIO
import tempfile
import json

def get_extraction(input_text, input_type):
    """ Will take an input and use ollie to perform verb extration. Returns a json containing all the extraction information.
    input_text - The file name, or text to perform extraction on. 
    input_type - File if the input_text is a file name. Text if the input_text is text. Unicorn_json if the input_text is a json from unicorn.
    """
    
    to_extract = ''
    if input_type == 'unicorn_json':
        json_body = ''
        #Load the json to a dictionary 
        json_dict = json.loads(input_text.replace('\n', '\\n'))
        for index in json_dict:
            json_body += '\n' + index['_source']['body']
        # Here we are creating a temp file to give to ollie
        f = tempfile.NamedTemporaryFile(mode = 'w')
        f.write(json_body)
        f.seek(0)
        to_extract = f.name
    elif input_type == 'file':
        to_extract = input_text
    elif input_type == 'text':
        f = tempfile.NamedTemporaryFile(mode = 'w')
        f.write(input_text)
        f.seek(0)
        to_extract = f.name
    else:
        # If an incorrect input type was given raise an error
        raise ValueError('Incorrent input type')
        
    sp = subprocess.Popen(['java', 
                           '-Xmx512m', 
                           '-jar', 
                           'ollie-app-latest.jar', 
                           '--output-format', 
                           'tabbed', 
                           to_extract], 
                           stdout=subprocess.PIPE)
    out = sp.stdout.read()
    
    data_frame = pandas.read_csv(StringIO.StringIO(out), sep='\t')
    
    # Orient the data frame by records
    output = data_frame.to_json(orient = 'records')
        
    return output
    
def match_extraction(unicorn_json, extraction_output):
    """
    Given a unicorn_json and extraction json from ollie, this method will attempt to marry the ollie output to the proper unicorn_json input
    unicorn_json - A json file from unicorn
    extracton_output - Ollie extraction derived from the get_extraction function
    """
    
    unicorn_dict = json.loads(unicorn_json.replace('\n', '\\n'))
    extraction_dict = json.loads(extraction_output.replace('\n', '\\n'))
    
    i = 0
    current_list = []
    # The logic here is we will go through each extraction from ollie and if it's text is found in a specific unicorn json, we will add it. 
    for index in extraction_dict:
        if index['text'] in unicorn_dict[i]['_source']['body']:
            current_list.append(index)
        else:
            unicorn_dict[i]['ollie_extraction'] = current_list
            current_list = []
            i += 1
            # Because it's possible that there were no extractions for a specifit text, we keep adding 1 to the unicorn index so long as we don't find the text
            while index['text'] not in unicorn_dict[i]['_source']['body']:
                i += 1
            # At this point we are sure we are at the unicorn index containing the text so add it to the current list
            current_list.append(index)
                
    # The for loop will exit befor loading in the rest of the data, so if there is something in the current_list, add it now. 
    if current_list:
        unicorn_dict[i]['ollie_extraction'] = current_list

    return unicorn_dict
 
