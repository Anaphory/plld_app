#!/usr/bin/python3

""" Load cultural features questionnaires and parse them into a working format """

import pandas
from xlrd.biffh import XLRDError
from clldutils.misc import slug

class UnexpectedCultureFormatError (ValueError):
    """Exception to be thrown when a questionnaire is misformatted"""
    pass

def parse_culture_questionnaire(filename):
    questionnaire = pandas.ExcelFile(filename)

    metadata_sheet_name = 'Metadata'
    if metadata_sheet_name in questionnaire.sheet_names:
        metadata_sheet = questionnaire.parse(metadata_sheet_name, header=None)
        try:
            metadata_blob = "; ".join(map(str, metadata_sheet.values))
        except KeyError:
            metadata_blob = ""
    else:
        metadata_blob = ""
    metadata = metadata_blob

    weird_rows = set()
    answers = pandas.DataFrame(columns = ["Answer", "Original Answer", "Notes"])
    features = pandas.DataFrame(columns = ["Domain", "Question_text_English", "Question_text_Indonesian", "Question_notes"])
    try:
        data_sheet = questionnaire.parse(
            0,
            skiprows=[0, 1, 2, 3, 4]).dropna('columns', 'all')
    except XLRDError:
        raise UnexpectedCultureFormatError(
            "Culture sheet did not have a 'Questionnaire' sheet")
    if "answer" in data_sheet.columns[5].lower():
        cols = list(data_sheet.columns)
        cols[5]="Original Answer"
        data_sheet.columns = cols
    else:
        raise UnexpectedCultureFormatError(
            "Expected Excel column F to have 'answer' in its header.")
        
    for i, row in data_sheet.iterrows():
        if pandas.isnull(row["Q_ID"]):
            # print(row)
            continue
        id = str(row["Q_ID"]).lower()
        if pandas.isnull(row[5]):
            # print(row)
            continue
        else:
            question = row[features.columns]
            question.name = id
            features = features.append(question)

            answer = row[answers.columns]
            if pandas.isnull(answer['Original Answer']):
                answer['Answer'] = None
            elif type(answer['Original Answer']) == int:
                answer['Answer'] = answer['Original Answer']
            elif slug(answer['Original Answer']) == 'yes':
                answer['Answer'] = True
            elif slug(answer['Original Answer']) == 'no':
                answer['Answer'] = False
            elif slug(answer['Original Answer']) == 'na':
                answer['Answer'] = None
            else:
                answer['Answer'] = answer['Original Answer']

            answer.name = id
            answers = answers.append(answer)

            assert(len(features) == len(answers))
    return metadata, features, answers

if __name__=='__main__':
    import sys
    metadata, features, answers = parse_questionnaire(sys.argv[1])
    print(metadata)
    print(features)
    print(answers.to_string())
