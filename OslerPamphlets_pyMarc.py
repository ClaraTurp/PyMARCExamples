# -*- coding: utf-8 -*-

import csv
import pymarc
from pymarc import MARCReader
from pymarc import MARCWriter
from pymarc import Record
from pymarc.field import Field
from pymarc import marc8
import os
import copy


###################
#    Functions
###################

def readCsvFile(fileName):
    myFile = open(fileName, "r", encoding = "utf-8", errors = "ignore")
    reader = csv.reader(myFile)

    return reader

def createPrintFiles(filename, x):
    myFile = open(filename, x, newline = "", encoding="utf-8", errors= "ignore")
    writer = csv.writer(myFile)

    return writer


def transferToArray(reader, myArray):
    for row in reader:
        myArray.append(row[0])

def cleanOclcNum(array):
    matchFound = False
    for currentField035a in array:
        currentField035a = currentField035a.strip()
        if currentField035a.startswith("(OCoLC)"):
            oclcNum = currentField035a[7:]
            matchFound = True
    if matchFound == False:
       oclcNum = "; ".join(str(x) for x in array)
    return oclcNum

def cleanSysNumber(SystemNumber):
    if SystemNumber.startswith("=001"):
        SystemNumber = SystemNumber[4:]
        SystemNumber = SystemNumber.strip()
    return SystemNumber

def assignOneField(record, field, subfield):
    try: 
        myField = record[field][subfield]
    except TypeError:
        myField = ""
    return myField

def assignMultipleFieldsSubfield(record, field, subfield):
    myArray = []
    for currentField in record.get_fields(field):
        for currentSubfield in currentField.get_subfields(subfield):
            myArray.append(currentSubfield)
    return myArray

def assignMultipleSubfields(record, field, subfield1, subfield2, subfield3):
    myArray = []
    for currentField in record.get_fields(field):
        myArray = []
        for currentSubfield in currentField.get_subfields(subfield1, subfield2, subfield3):
            myArray.append(currentSubfield)
    return myArray


###################
#    Main Code   
###################

writer = createPrintFiles("OslerPamphlet.csv", "w")
currentDir = os.getcwd()
filesDir = currentDir + "\\MarcFiles\\"


for filename in os.listdir(filesDir):
    print(filename)
    
    file = open(filesDir + filename, "rb")
    reader = MARCReader(file, to_unicode= True, force_utf8= True, utf8_handling="strict")

    for record in reader:
       
        SystemNum = str(record["001"])
        SysNum = cleanSysNumber(SystemNum)
        oclc = assignMultipleFieldsSubfield(record, "035", "a")
        OclcNum = cleanOclcNum(oclc)
        location = assignMultipleSubfields(record, "852", "b", "c", "h")

        if len(location) >= 3 and location != None:
            if location[0] == "OSLER" and (location[1] == "MAIN" or location[1] == "FELLW") and location[2] == "Pamphlet":
                writer.writerow([SysNum, OclcNum, location])
