from __future__ import unicode_literals
import sys

from clld.scripts.util import initializedb, Data
from clld.db.meta import DBSession
from clld.db.models import common

import plld_app
from plld_app import models

import os
import os.path
import pandas

from parse_typology_questionnaire import parse_questionnaire, UnexpectedTypologyFormatError

counter=0
def newid():
    global counter
    counter += 1
    return str(counter)

DBPATH = "J:/ResearchData/HUM/LUCL-KlamerVICI/Lesser Sunda Database version 3 June 2016/"

def main(args):
    data = Data()

    dataset = common.Dataset(
        id=plld_app.__name__,
        name=plld_app.__name__,
        domain='plld.clld.org',
        description="Database of Papuan Language and Culture",
        )
    DBSession.add(dataset)

    # All ValueSets must be related to a contribution:
    contrib = common.Contribution(id='contrib', name='the contribution')

    # Load the list of languages
    languages = pandas.ExcelFile(os.path.join(DBPATH, "Languages and Coordinates.xlsx")).parse(0)
    
    parameters = {}
    for i, language in languages.iterrows():
        # Generate the database object for each language
        print("\nCreating language", language['Language name (-dialect)'])
        lang = common.Language(
            id=((language['Language name (-dialect)'].lower()[:4] + "x" + newid())
                if pandas.isnull(language['Glottolog'])
                else language['Glottolog'].strip()),
            name=language['Language name (-dialect)'].strip(),
            latitude=language['Lat'],
            longitude=language['Lon'])

        # Check what data files we have that say they are about that language.
        try:
            files_concerning = [file for file in os.listdir(DBPATH)
                                if file.lower().startswith(language['ISO'].lower())]
        except AttributeError:
            continue

        typology_files = [file for file in files_concerning
                          if 'typolog' in file.lower()]

        # Try to load the corresponding typology questionnaire
        if len(typology_files) != 1:
            continue
        questionnaire = typology_files[0]
        try:
            contribution_text, parameter_descriptions, answers = parse_questionnaire(
                os.path.join(DBPATH, questionnaire))
            for p, parameter in parameter_descriptions.iterrows():
                question = parameter['q_text']
                answer = str(answers["a_text"][question])
                #print('•', question, "=", answer.encode('ascii', 'ignore').decode('ascii'))
                try:
                    param = parameters[question.lower()]
                except KeyError:
                    param = common.Parameter(
                        id='param{:s}'.format(newid()),
                        name=question)
                    parameters[question.lower()] = param

                # ValueSets group Values related to the same Language, Contribution and 
                # Parameter
                vs = common.ValueSet(id='vs'+newid(),
                                     language=lang,
                                     parameter=param,
                                     contribution=contrib)

                # Values store the actual "measurements":
                DBSession.add(common.Value(id='v'+newid(), name=answer, valueset=vs))
                DBSession.flush()
                
            
            print("Typology database for", language.name, "successfully loaded.")
        except UnexpectedTypologyFormatError:
            print("File", questionnaire, "had an unexpected format for a typology questionnaire!")

def prime_cache(args):
    """If data needs to be denormalized for lookup, do that here.
    This procedure should be separate from the db initialization, because
    it will have to be run periodiucally whenever data has been updated.
    """


if __name__ == '__main__':
    initializedb(create=main, prime_cache=prime_cache)
    sys.exit(0)
