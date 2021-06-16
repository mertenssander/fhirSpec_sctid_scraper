FROM python:3.9
 
RUN pip install pandas tqdm requests xlrd openpyxl xlsxwriter fhir.resources cached  python-decouple beautifulsoup4

RUN mkdir /scripts
COPY ./ /scripts

WORKDIR /scripts

# ENTRYPOINT python3 generate.py
ENTRYPOINT bash