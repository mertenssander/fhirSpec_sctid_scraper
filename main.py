import requests
from bs4 import BeautifulSoup
import urllib.parse
import re
import tqdm
import json
import time
import pandas as pd

def gatherTocUrls(url, base):
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    
    links = soup.findAll('a')

    output = []
    for link in links:
        try:
            output.append(urllib.parse.urljoin(base, link['href']))
        except Exception as e:
            print(f"Error adding {link} - {e}")
            continue

    return list(set(output))

def findSCTIDsOnPage(page):
    response = requests.get(page)
    soup = BeautifulSoup(response.content, 'html.parser')

    # Identify urls that start with http://browser.ihtsdotools.org/
    urls = soup.findAll('a', href = re.compile(r'http://browser.ihtsdotools.org/.*'))

    output = []
    for url in urls:
        try:
            output.append({'source' : page, 'sctid' : url['href'].split("=")[-1]})
        except:
            continue

    return output

if __name__ == "__main__":
    # Fetch TOC
    print("Fetching TOC")
    pages = gatherTocUrls(url = "https://hl7.org/fhir/toc.html", base = "https://hl7.org/fhir/")

    # testing
    # pages = ["https://hl7.org/fhir/valueset-procedure-outcome.html"]

    print(f"Found {len(pages)} pages on TOC")
    
    print("Iterating over pages")
    concepts = []
    for page in tqdm.tqdm(pages):
        concepts.extend(findSCTIDsOnPage(page))

    print("Checking if these concepts are active")
    sctids = [{"code": x['sctid']} for x in concepts]
    data = {
        "resourceType": "Parameters",
        "parameter": [
            {
                "name":"property",
                "valueString":"inactive"
            },
            {
                "name": "valueSet",
                "resource": {
                    "resourceType": "ValueSet",
                    "compose": {
                        "include": [{
                            "system": "http://snomed.info/sct",
                            "concept" : sctids
                        }]
                    }
                }
            }
        ]
    }
    headers = {
        "Content-Type" : "application/json"
    }
    response = requests.post("https://r4.ontoserver.csiro.au/fhir/ValueSet/$expand", data=json.dumps(data), headers=headers)

    # Retrieve verison used in returned valueset
    version = None
    for parameter in response.json()['expansion']['parameter']:
        if parameter['name'] == "version":
            version = parameter['valueUri']

    # Handle results for each concept
    checked_concepts = []
    for result in response.json()['expansion']['contains']:
        inactive = False
        props = {}
        for extension in result.get('extension',[]):
            code = None
            value = None
            for _extension in extension['extension']:
                if (_extension.get('url',False) == 'code') and(_extension.get('valueCode') == 'inactive'):
                    code = _extension['valueCode']
                if _extension.get('url',False) == 'value_x_':
                    value = _extension['valueBoolean']
            props[code] = value
                    
        # Collect all the pages this concept was used in
        used_in = [x['source'] for x in concepts if x['sctid'] == result['code']]

        # Send to dictionary for dataframe creation
        checked_concepts.append({
            'sctid' : result['code'],
            'display' : result['display'],
            'inactive' : props['inactive'],
            'used_in' : used_in,
        })
    
    print(f"Version used: {version}")

    # Create df from all concepts, columns=[sctid, display, active, pages]
    df = pd.DataFrame(checked_concepts)
    print(df.head())

    # Check if all codes from sctids = [{"code": x['sctid']} for x in concepts] are present in df
    df_concepts = len(set(df['sctid'].values))
    concepts_to_check = len(set([x['sctid'] for x in concepts]))
    print(f"Supposed to check {df_concepts} and checked {concepts_to_check}")

    # Print to excel
    df.to_excel(f"results {time.time()}.xlsx")