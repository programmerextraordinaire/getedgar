"""

main.py

Main program to download and parse EDGAR data from the SEC website.

--tkp

2020-08-07  Init commit - Q1 2018 had 7073 Form D filings

Amt: $ 0/tTotal:$ 20,578,438,852
https://www.sec.gov/Archives/edgar/data/1729436/000172943618000001/xslFormDX01/primary_doc.xml
https://www.sec.gov/Archives/edgar/data/1729436/000172943618000001/primary_doc.xml
Traceback (most recent call last):
  File "c:\Projects\Sandbox\EDGAR\getedgar\main.py", line 155, in <module>
    main()
  File "C:\Projects\Sandbox\EDGAR\getedgar\.venv\lib\site-packages\click\core.py", line 829, in __call__
    return self.main(*args, **kwargs)
  File "C:\Projects\Sandbox\EDGAR\getedgar\.venv\lib\site-packages\click\core.py", line 782, in main
    rv = self.invoke(ctx)
  File "C:\Projects\Sandbox\EDGAR\getedgar\.venv\lib\site-packages\click\core.py", line 1066, in invoke
    return ctx.invoke(self.callback, **ctx.params)
  File "C:\Projects\Sandbox\EDGAR\getedgar\.venv\lib\site-packages\click\core.py", line 610, in invoke
    return callback(*args, **kwargs)
  File "c:\Projects\Sandbox\EDGAR\getedgar\main.py", line 150, in main
    parse_filings(results, True)        # Process all
  File "c:\Projects\Sandbox\EDGAR\getedgar\main.py", line 127, in parse_filings
    if (soup.edgarsubmission.offeringdata.offeringsalesamounts.totalamountsold is not None):
AttributeError: 'NoneType' object has no attribute 'offeringdata'



"""


import datetime
from bs4 import BeautifulSoup   # https://www.crummy.com/software/BeautifulSoup/bs4/doc/
import click        # https://click.palletsprojects.com/en/7.x/
import requests     # https://2.python-requests.org/en/master/


class Filing:
    def __init__(self, ftype, url, amount):
        self.ftype = ftype
        self.url = url
        self.amount = amount    # Decimal? Int?



# Generate the list of index files archived in EDGAR since start_year (earliest: 1993) until the most recent quarter
def get_urls():
    current_year = datetime.date.today().year
    current_quarter = (datetime.date.today().month - 1) // 3 + 1
    start_year = 2018
    years = list(range(start_year, current_year))
    quarters = ['QTR1', 'QTR2', 'QTR3', 'QTR4']
    history = [(y, q) for y in years for q in quarters]
    for i in range(1, current_quarter + 1):
        history.append((current_year, 'QTR%d' % i))
    urls = ['https://www.sec.gov/Archives/edgar/full-index/%d/%s/crawler.idx' % (x[0], x[1]) for x in history]
    urls.sort()
    return urls


#ACRODYNE COMMUNICATIONS INC                                   10QSB/A     883296      1999-06-03  https://www.sec.gov/Archives/edgar/data/883296/0000889812-99-001744-index.htm         
def get_types(lines):
    filing_types = set()
    for line in lines:
        s = line[62:73].strip()
        if s == 'D':
            print(line)
        filing_types.add(s)
    t = list(filing_types)
    t.sort()
    return t


def data_filter(filing_type, lines, verbose=False):
    results = []
    for line in lines:
        s = line[62:73].strip()
        if s == filing_type:
            if verbose: print(line)
            results.append(line.strip())
    return results


def get_xml(url, verbose=False):
    xml = None
    if verbose: print(url)
    r = requests.get(url)
    if r.status_code == 200:
        soup = BeautifulSoup(r.text, 'lxml')
        links = soup.find_all('a')
        for tag in links:
            link = tag.get('href')
            if link[-4:] == ".xml":
                # Build full URL from relative link.
                # https://www.sec.gov/Archives/edgar/data/1566610/000149315218001873/primary_doc.xml
                xmlurl = "https://www.sec.gov" + link
                print(xmlurl)
                rx = requests.get(xmlurl)
                xml = rx.text
            if verbose: print(tag)
    else:
        print("ERROR Parsing URL: {0}".format(url))
    return xml


example_html = """
<table class="tableFile" summary="Document Format Files">
         <tbody><tr>
            <th scope="col" style="width: 5%;"><acronym title="Sequence Number">Seq</acronym></th>
            <th scope="col" style="width: 40%;">Description</th>
            <th scope="col" style="width: 20%;">Document</th>
            <th scope="col" style="width: 10%;">Type</th>
            <th scope="col">Size</th>
         </tr>
         <tr>
            <td scope="row">1</td>
            <td scope="row"></td>
            <td scope="row"><a href="/Archives/edgar/data/1566610/000149315218001873/xslFormDX01/primary_doc.xml">primary_doc.html</a></td>
            <td scope="row">D</td>
            <td scope="row">&nbsp;</td>
         </tr>
         <tr class="blueRow">
            <td scope="row">1</td>
            <td scope="row"></td>
            <td scope="row"><a href="/Archives/edgar/data/1566610/000149315218001873/primary_doc.xml">primary_doc.xml</a></td>
            <td scope="row">D</td>
            <td scope="row">4850</td>
         </tr>
         <tr>
            <td scope="row">&nbsp;</td>
            <td scope="row">Complete submission text file</td>
            <td scope="row"><a href="/Archives/edgar/data/1566610/000149315218001873/0001493152-18-001873.txt">0001493152-18-001873.txt</a></td>
            <td scope="row">&nbsp;</td>
            <td scope="row">6167</td>
         </tr>
      </tbody></table>
"""
def parse_filings(filings, verbose=False):
    total = 0
    for line in filings:
        url = line[98:].strip()
        xml = get_xml(url, verbose=False)
        #if verbose: print(xml)
        soup = BeautifulSoup(xml, 'lxml')
        if (soup.edgarsubmission.offeringdata.offeringsalesamounts.totalamountsold is not None):
            amt = int(soup.edgarsubmission.offeringdata.offeringsalesamounts.totalamountsold.string)
            total += amt
            if verbose: print("Amt: $ {0:,}/tTotal:$ {1:,}".format(amt, total))
    print("Total amount: $ {0}".format(total))


@click.command()
def main(filter='D'):
    """Simple program that downloads and parses SEC EDGAR data."""
    click.echo("Downloading EDGAR Form %s" % filter)
    urls = get_urls()
    print("Downloaded {0} URLs".format(len(urls)))
    url = urls[0]
    print(url)
    req = requests.get(url)
    print(req.status_code)
    lines = req.text.splitlines()[9:]   # Remove header
    #filing_types = get_types(lines)
    results = data_filter(filter, lines, False)
    print("Found {0} results".format(len(results)))
    #parse_filings(results[0:3], True)  # Process 1st 3
    parse_filings(results, True)        # Process all
    #print(req.text)


if __name__ == "__main__":
    main()
