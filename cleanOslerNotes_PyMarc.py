import csv
import pymarc
from pymarc import MARCReader
from pymarc import MARCWriter
from pymarc import Record
from pymarc.field import Field
import datetime
import os

from cleanOslerNotes_PyMarc_Functions import createPrintFiles, cleanOclcNum, assignMultipleFieldsSubfields

###################
#    Main Code   
###################


OslerNotes = createPrintFiles("oslerNotesStr_Final.csv", "w")

currentDir = os.getcwd()
filesDir = currentDir + "\\MarcFiles\\"


for filename in os.listdir(filesDir):
    print(filename)
    
    file = open(filesDir + filename, "rb")
    reader = MARCReader(file, to_unicode= True, force_utf8= True, utf8_handling='ignore')

    for record in reader:
    
        oclc = assignMultipleFieldsSubfields(record, "035", "a")
        oclcNum = cleanOclcNum(oclc)
        notes = assignMultipleFieldsSubfields(record, "876", "z")
        notes = "/".join(notes)
        barcode = assignMultipleFieldsSubfields(record, "930", "5")
        barcode = "/".join(barcode)
        branch = assignMultipleFieldsSubfields(record, "930", "1")
        branch = "/".join(branch)
        shelvingLocation = assignMultipleFieldsSubfields(record, "930", "2")
        shelvingLocation = "/".join(shelvingLocation)

        if len(notes) > 0:
            if "ROBE" in shelvingLocation:
                myRecord = [oclcNum, barcode, branch, shelvingLocation, notes]
                OslerNotes.writerow(myRecord)
