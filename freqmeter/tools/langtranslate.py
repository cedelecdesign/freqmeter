# -*- coding: utf-8 -*-
"""
A simple replacement for Qt translation mechanism as it doesn't
work very well with pyQt !!!
Just create a plain text containing all the strigs and loadLanguage will
return a list of strings you can use in your code.
"""


def loadLanguage(filename):
    """ load a text file containing translation strings """
    langstr = []

    try:
        # open language file and read strings
        with open(filename, 'r') as reader:
            langstr = reader.readlines()
            # remove end of line character
            for x in range(len(langstr)):
                langstr[x] = langstr[x].replace('\n', '')
    except FileNotFoundError:
        langstr = None

    return langstr


def load_section(filename, section):
    langstr = []

    try:
        # open language file and read strings
        with open(filename, 'r') as reader:
            for line in reader:
                # line is a section
                if line[:8] == "[section":
                    data = line.split(":")
                    name = data[1].replace(']\n', '')
                    # is the good section
                    if name == section:
                        while 1:
                            line = reader.readline().replace('\n', '')
                            if line != '':
                                langstr.append(line)
                            else:
                                return langstr

    except FileNotFoundError:
        print("File not found")
        return None
