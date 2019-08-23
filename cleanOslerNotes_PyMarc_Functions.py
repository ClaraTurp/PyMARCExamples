import csv
import pymarc
from pymarc import MARCReader
from pymarc import MARCWriter
from pymarc import Record
from pymarc.field import Field
import datetime
import os

###################
#    Functions
###################

def createPrintFiles(filename, x):
    myFile = open(filename, x, newline = "", encoding="utf-8", errors= "ignore")
    writer = csv.writer(myFile)

    return writer


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


def assignMultipleFieldsSubfields(record, field, subfield):
    myArray = []
    for currentField in record.get_fields(field):
        for currentSubfield in currentField.get_subfields(subfield):
            if currentSubfield is None:
                myArray.append("no Subfield")
            else:
                myArray.append(currentSubfield)
    return myArray
