from __future__ import unicode_literals
import sys

from clld.scripts.util import initializedb, Data
from clld.db.meta import DBSession
from clld.db.models import common
from path import path

from clld.db.models.parameter import DomainElement
from clldutils.misc import slug

from sqlalchemy.orm import joinedload, joinedload_all
from pylab import figure, axes, pie
import plld_app
from plld_app import models

import os
import os.path
import pandas

from parse_typology_questionnaire import parse_typology_questionnaire, UnexpectedTypologyFormatError
from parse_cultural_questionnaire import parse_culture_questionnaire, UnexpectedCultureFormatError

counter=0
def newid():
    global counter
    counter += 1
    return str(counter)

icons_dir = path(plld_app.__file__).dirname().joinpath('static', 'icons')
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
        lang = models.Lect(
            id=((language['Language name (-dialect)'].lower()[:4] + "x" + newid())
                if pandas.isnull(language['Glottolog'])
                else language['Glottolog'].strip()),
            region=language['Region'],
            family=language['Family'],
            name=language['Language name (-dialect)'].strip(),
            latitude=language['Lat'],
            longitude=language['Lon'])

        # Check what data files we have that say they are about that language.
        if pandas.isnull(language['ISO_code']):
            # The convention for file-names of varieties without iso
            # code is ad-hoc, skip those until we have established a
            # good convention.
            files_concerning = [file for file in os.listdir(DBPATH)
                                if file.lower().startswith(
                                        language['Internal'].lower()+'_')]
        else:
            # Otherwise, the convention is that languages are
            # described by files starting with their iso code and an
            # underscore.
            files_concerning = [file for file in os.listdir(DBPATH)
                                if file.lower().startswith(
                                        language['ISO_code'].lower()+'_')]


        # For each such language, we might have typological, sociolinguistic and lexical (small vocabulary or big vocabulary or kinship terms) data. Deal with them in order.
        
        # Try to load the corresponding typology questionnaire
        typology_files = [file for file in files_concerning
                          if 'typolog' in file.lower()]
        if len(typology_files) == 1:
            try:
                add_typological_data(typology_files[0], parameters, lang)
                print("Typological data read.")
            except UnexpectedTypologyFormatError:
                print("File", typology_files[0], "had an unexpected format for a typology questionnaire!")
        else:
            print("There were not one, but", len(typology_files), "possible questionnaires.")

        # Try to load the corresponding cultural features questionnaire
        culture_files = [file for file in files_concerning
                          if 'cult' in file.lower()]
        if len(culture_files) == 1:
            try:
                add_cultural_data(culture_files[0], parameters, lang)
                print("Cultural data read.")
            except UnexpectedCultureFormatError:
                print("File", culture_files[0], "had an unexpected format for a culture questionnaire!")
        else:
            print("There were not one, but", len(culture_files), "possible questionnaires.")

def color(number):
    """ Define a color for integer numbers """
    if number is None or pandas.isnull(number):
        return "ff3300"
    colors = [
        "000000",
        "ffffff",
        "ff0000",
        "00ff00",
        "0000ff",
        "ffff00",
        "ff00ff",
        "00ffff",
        "ff3300",
        ]
    return colors[number % len(colors)]
    
            
def add_typological_data(questionnaire_file_name, parameters, language):
    """ Parse the typological questionnaire into the database """
    contribution_text, parameter_descriptions, answers = parse_typology_questionnaire(
        os.path.join(DBPATH, questionnaire_file_name))

    # All ValueSets must be related to a contribution, so generate one from the metadata.
    contrib = common.Contribution(id='contrib'+newid(), name=contribution_text+newid())

    for p, parameter in parameter_descriptions.iterrows():
        # First, make sure that this parameter exists – either look it up or create it.
        question = parameter['q_text'].lower()
        try:
            param, domain = parameters[question]
        except KeyError:
            param = common.Parameter(
                id='param{:s}'.format(newid()),
                name=parameter['q_text'])
            domain = {}
            parameters[question] = (param, domain)

        # Secondly, check whether we are aware that this answer is
        # valid already – otherwise we add its value to the domain,
        # and use that.
        # Note: Once we have a database, we can do better filtering
        # and constraining, and don't need to rely on reasonable data.
        answer = str(answers["a_text"][question])
        try:
            domain_element = domain[answer]
        except KeyError:
            try:
                numerical_value = int(answer)
            except ValueError:
                numerical_value = (1 if answer == "Y" else
                                   0 if answer == "N" else
                                   None)
            domain_element = common.DomainElement(
                id=param.id+answer,
                description=question+" – "+answer,
                number=numerical_value,
                name=answer,
                parameter=param,
                abbr=answer,
                jsondata={'color': color(numerical_value)})
            domain[answer] = domain_element

        # Now create the ValueSet, representing all values the
        # language has for this parameter
        vs = common.ValueSet(id='vs'+newid(),
                             language=language,
                             parameter=param,
                             jsondata=domain_element.jsondata,
                             contribution=contrib)

        # and fill in the actual values, which in this case is only
        # one. This object, and all objects it depends on, are then
        # scheduled for writing into the database.
        DBSession.add(common.Value(
            id='v'+newid(),
            valueset=vs,
            frequency=float(100),
            jsondata=domain_element.jsondata,
            domainelement=domain_element))
        # Execute all scheduled database updates.
        DBSession.flush()

def add_cultural_data(questionnaire_file_name, parameters, language):
    """ Parse the typological questionnaire into the database """
    contribution_text, parameter_descriptions, answers = parse_culture_questionnaire(
        os.path.join(DBPATH, questionnaire_file_name))

    # All ValueSets must be related to a contribution, so generate one from the metadata.
    contrib = common.Contribution(id='contrib'+newid(), name=contribution_text+newid())

    for p, parameter in parameter_descriptions.iterrows():
        # First, make sure that this parameter exists – either look it up or create it.
        pid = p.replace(".", "-")
        try:
            param, domain = parameters[pid]
        except KeyError:
            param = common.Parameter(
                id='culture'+pid,
                name=p,
                description=parameter['Question_text_English'],
                markup_description=parameter['Question_text_English'])
            domain = {}
            parameters[pid] = (param, domain)

        # Secondly, check whether we are aware that this answer is
        # valid already – otherwise we add its value to the domain,
        # and use that.
        # Note: Once we have a database, we can do better filtering
        # and constraining, and don't need to rely on reasonable data.
        answer = str(answers["Answer"][p])
        try:
            domain_element = domain[slug(answer)]
        except KeyError:
            try:
                numerical_value = int(answer)
            except ValueError:
                numerical_value = (1 if answer == "Y" or answer == 'True' else
                                   0 if answer == "N" or answer == 'False' else
                                   None)
            domain_element = common.DomainElement(
                id=param.id+slug(answer),
                description=answer,
                number=numerical_value,
                name=answer,
                parameter=param,
                abbr=answer,
                jsondata={'color': color(numerical_value)})
            DBSession.add(domain_element)
            try:
                DBSession.flush()
            except:
                print(domain, domain_element, language.name, pid, param.name)
            domain[slug(answer)] = domain_element

        # Now create the ValueSet, representing all values the
        # language has for this parameter
        vs = common.ValueSet(id='vs'+newid(),
                             language=language,
                             parameter=param,
                             jsondata=domain_element.jsondata,
                             contribution=contrib)

        # and fill in the actual values, which in this case is only
        # one. This object, and all objects it depends on, are then
        # scheduled for writing into the database.
        DBSession.add(common.Value(
            id='v'+newid(),
            valueset=vs,
            frequency=float(100),
            jsondata=domain_element.jsondata,
            domainelement=domain_element))
        # Execute all scheduled database updates.
        DBSession.flush()

def prime_cache(args):
    """If data needs to be denormalized for lookup, do that here.
    This procedure should be separate from the db initialization, because
    it will have to be run periodiucally whenever data has been updated.
    """
    icons = set()
    frequencies = set()

    for language in DBSession.query(models.Lect):
        color = {
            'Timor-Alor-Pantar': '00ff00',
            'Austronesian': 'ff0000'}[language.family]
        icon = "pie-100-{:s}.png".format(color)
        if icons_dir.joinpath(icon).exists():
            pass
        else:
            icon = figure(figsize=(0.4, 0.4))
            axes([0.1, 0.1, 0.8, 0.8])
            coll = pie((100,), colors=['#'+color])
            for wedge in coll[0]:
                wedge.set_linewidth(0.5)
            icon.savefig(
                icons_dir.joinpath(basename+'.png'),
                transparent=True)
        language.jsondata = {'color': color,
                             'icon': 'pie-100-{:s}.png'.format(color)}

    for valueset in DBSession.query(common.ValueSet).options(
            joinedload(common.ValueSet.parameter),
            joinedload_all(common.ValueSet.values, common.Value.domainelement)):
        values = sorted(list(valueset.values), key=lambda v: v.domainelement.number)
        assert abs(sum(v.frequency for v in values) - 100) < 1
        fracs = []
        colors = []

        for v in values:
            color = v.domainelement.jsondata['color']
            frequency = round(v.frequency)
            assert frequency

            if frequency not in frequencies:
                icon = figure(figsize=(0.4, 0.4))
                axes([0.1, 0.1, 0.8, 0.8])
                coll = pie((int(100 - frequency), frequency), colors=('w', 'k'))
                coll[0][0].set_linewidth(0.5)
                icon.savefig(
                    icons_dir.joinpath('freq-%s.png' % frequency),
                    transparent=True)
                frequencies.add(frequency)

            v.jsondata = {'frequency_icon': 'freq-%s.png' % frequency}
            fracs.append(frequency)
            colors.append(color)
            v.domainelement.jsondata = {
                'color': color, 'icon': 'pie-100-%s.png' % color}

        assert len(colors) == len(set(colors))
        fracs, colors = tuple(fracs), tuple(colors)

        basename = 'pie-'
        basename += '-'.join('%s-%s' % (f, c) for f, c in zip(fracs, colors))
        valueset.update_jsondata(icon=basename + '.png')
        if (fracs, colors) not in icons:
            icon = figure(figsize=(0.4, 0.4))
            axes([0.1, 0.1, 0.8, 0.8])
            coll = pie(
                tuple(reversed(fracs)),
                colors=['#' + _color for _color in reversed(colors)])
            for wedge in coll[0]:
                wedge.set_linewidth(0.5)
            icon.savefig(
                icons_dir.joinpath(basename+'.png'),
                transparent=True)
            icon.savefig(
                icons_dir.joinpath(basename+'.svg'),
                transparent=True)
            icons.add((fracs, colors))


if __name__ == '__main__':
    initializedb(create=main, prime_cache=prime_cache)
    sys.exit(0)
