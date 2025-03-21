import re
import pygsheets
import pandas as pd

SHEET_IDs = [
    ('19qASykV8jpktq6CAyPNl2aytaJoiFM_n3MelmBelh7I', ['HELP: FAQs']),
]
CREDENTIAL = 'creds.json'



OVERALL_TEMPLATE = """
---
title: FAQ for {role}
---

{toc}

<!-- table of contents created by Adrian Bonnet, see https://Relex12.github.io/Markdown-Table-of-Contents for more -->


{content}

"""

CONTENT_TEMPLATE = """

### {section}

{content}


"""

SEPARATOR = "____________________________________________________________________________\n"

def load_faq(df):
    md_dict = {
        'student': {
            'role': 'Learners',
            'toc': {},
            'content': {},
        },
        'teacher': {
            'role': 'Teachers',
            'toc': {},
            'content': {},
        },
    }
    for row in df.sort_values(by=['#']).to_dict(orient='records'):
        if not row['Question']:
            continue
        # print(row)
        data = md_dict[row['USER type'].lower()]
        if row['Section'] not in data['toc']:
            data['toc'][row['Section']] = []
        data['toc'][row['Section']].append(row['Question'])
        data['content'][row['Question']] = CONTENT_TEMPLATE.format(section=row['Question'], content=row['Answer'])

    return md_dict

# use regex to remove special characters and punctuations
clean = lambda x: re.sub(r'[^\w\s]', '', x).lower().replace(' ', '-')


def format_md(md_dict):
    for _, data in md_dict.items():
        md_file = 'faq-{}-TOC.md'.format(data['role'].upper())
        print('Writing:', md_file)
        toc = ''
        content = ''
        for s, (section, questions) in enumerate(data['toc'].items()):
            toc += f'- [{section}](#{clean(section)})\n'
            content += f'{SEPARATOR}{SEPARATOR}## {section}\n\n'
            for q, question in enumerate(questions):
                toc += f'  - [{question}](#{clean(question)})\n'
                if q:
                    content += f'{SEPARATOR}'
                content += data['content'][question]
        with open(md_file, 'w') as f:
            f.write(OVERALL_TEMPLATE.format(role=data['role'], toc=toc, content=content))
        
        


if __name__ == '__main__':
    gc = pygsheets.authorize(service_file=CREDENTIAL)
    df = None
    for sheet_id, tabs in SHEET_IDs:
        for tab in tabs:
            print('Fetching:', sheet_id, tab)
            if df is None:
                df = gc.open_by_key(sheet_id).worksheet_by_title(tab).get_as_df()
            else:
                sheet_df = gc.open_by_key(sheet_id).worksheet_by_title(tab).get_as_df()
                try:
                    df = pd.concat([df, sheet_df], ignore_index=True)
                except Exception as e:
                    print(df)
                    print(sheet_df)
                    df = pd.concat([df, sheet_df], ignore_index=True)
        df = df.reset_index(drop=True)
    # print(df)
    md_dict = load_faq(df)
    format_md(md_dict)
    print('Done')
