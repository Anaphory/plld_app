#!/usr/bin/python3

""" Load typology questionnaires and parse them into a working format """

import pandas
from xlrd.biffh import XLRDError

class UnexpectedTypologyFormatError (ValueError):
    """Exception to be thrown when a questionnaire is misformatted"""
    pass

def parse_typology_questionnaire(filename):
    questionnaire = pandas.ExcelFile(filename)

    metadata_sheet_name = 'Metadata'
    if metadata_sheet_name in questionnaire.sheet_names:
        metadata_sheet = questionnaire.parse(metadata_sheet_name, header=None)
        try:
            metadata_blob = "; ".join(metadata_sheet[0])
        except KeyError:
            metadata_blob = ""
    else:
        metadata_blob = ""
    metadata = metadata_blob

    weird_rows = set()
    answers = pandas.DataFrame(columns = ["a_text", "a_notes" ,"a_reference"])
    features = pandas.DataFrame(columns = ["q_id: Reesink", "q_text", "q_note: Nijmegen Typological Survey"])
    data_sheet_name = 'Questionnaire'
    try:
        data_sheet = questionnaire.parse(
            data_sheet_name,
            skiprows=[0, 1, 2, 3, 4, 5, 7]).dropna('columns', 'all')
    except XLRDError:
        raise UnexpectedTypologyFormatError("Typology sheet did not have a 'Questionnaire' sheet")
    for i, row in data_sheet.iterrows():
        if pandas.isnull(row["q_text"]):
            weird_rows.add(i)
        if pandas.isnull(row["a_text"]):
            weird_rows.add(i)
        else:
            features = features.append(row[["q_id: Reesink", "q_text", "q_note: Nijmegen Topological Survey"]])
            answer = row[["a_text", "a_notes", "a_reference"]]
            answer.name = row["q_text"].lower()
            answers = answers.append(answer)
            assert(len(features) == len(answers))
    return metadata, features, answers

if __name__=='__main__':
    import sys
    metadata, features, answers = parse_questionnaire(sys.argv[1])
    print(metadata)
    print(features)
    print(answers.to_string())
