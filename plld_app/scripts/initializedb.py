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
        if pandas.isnull(language['ISO']):
            # The convention for file-names of varieties without iso
            # code is ad-hoc, skip those until we have established a
            # good convention.
            continue
        else:
            # Otherwise, the convention is that languages are
            # described by files starting with their iso code and an
            # underscore.
            files_concerning = [file for file in os.listdir(DBPATH)
                                if file.lower().startswith(
                                        language['ISO'].lower()+'_')]


        # For each such language, we might have typological, sociolinguistic and lexical (small vocabulary or big vocabulary or kinship terms) data. Deal with them in order.
        
        # Try to load the corresponding typology questionnaire
        typology_files = [file for file in files_concerning
                          if 'typolog' in file.lower()]
        if len(typology_files) == 1:
            try:
                add_typological_data(typology_files[0], parameters, lang)
            except UnexpectedTypologyFormatError:
                print("File", typology_files[0], "had an unexpected format for a typology questionnaire!")
        else:
            print("There were not one, but", len(typology_files), "possible questionnaires.")
                

            
def add_typological_data(questionnaire_file_name, parameters, language):
    """ Parse the typological questionnaire into the database """
    contribution_text, parameter_descriptions, answers = parse_questionnaire(
        os.path.join(DBPATH, questionnaire_file_name))

    # All ValueSets must be related to a contribution, so generate one from the metadata.
    contrib = common.Contribution(id='contrib'+newid(), name=contribution_text+newid())

    for p, parameter in parameter_descriptions.iterrows():
        question = parameter['q_text'].lower()
        try:
            param = parameters[question]
        except KeyError:
            param = common.Parameter(
                id='param{:s}'.format(newid()),
                name=parameter['q_text'])
            parameters[question] = param

        answer = str(answers["a_text"][question])
        # ValueSets group Values related to the same Language, Contribution and 
        # Parameter
        vs = common.ValueSet(id='vs'+newid(),
                             language=language,
                             parameter=param,
                             contribution=contrib)

        # Values store the actual "measurements":
        DBSession.add(common.Value(id='v'+newid(), name=answer, valueset=vs))
        DBSession.flush()

def prime_cache(args):
    """If data needs to be denormalized for lookup, do that here.
    This procedure should be separate from the db initialization, because
    it will have to be run periodiucally whenever data has been updated.
    """


if __name__ == '__main__':
    initializedb(create=main, prime_cache=prime_cache)
    sys.exit(0)
