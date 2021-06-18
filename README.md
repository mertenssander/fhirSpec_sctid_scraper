# Description
Python script that checks the HL7 FHIR TOC and gathers all the urls on pages in that TOC. If the url points to the SNOMED International browser, it extracts the SCTID and adds it to a list. At the end, the list of concepts gets checked against CSIRO's public ontoserver endpoint. The 'inactive' property gets printed to an excel file, along with the sctid, display text and any pages where the concept appeared.

# Execution
> docker-compose run runner

or

Install dependencies from Dockerfile and run
> python main.py