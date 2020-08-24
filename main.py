"""

main.py

Main program to download and parse EDGAR data from the SEC website.

--tkp

History
=======
2020-08-07  Init commit - Q1 2018 had 7073 Form D filings
2020-08-24  Auto create folders and update downloads accordingly.

Results
=======
2018 Q1 7073/7073 Amt: $ 14,041,340  Total:$ 170,757,404,165
2018 Q3 6930/6930 Amt: $ 4,000,000  Total:$ 162,789,356,396
2018 Q4 6967/6967 Amt: $ 500,000  Total:$ 128,541,125,614

2019 Q1 6792/6792 Amt: $ 0  Total:$ 142,686,633,697
2019-Q4 6915/6915 Amt: $ 40,000  Total:$ 121,241,062,684

2020-Q1 7276/7276 Amt: $ 835,000  Total:$ 134,266,883,951
2020-Q2 6014/6014 Amt: $ 263,207  Total:$ 113,471,132,489
2020-Q3 3307/3307 Amt: $ 5,525,959  Total:$ 60,768,580,776
"""


import datetime
import os
from bs4 import BeautifulSoup   # https://www.crummy.com/software/BeautifulSoup/bs4/doc/
import click                    # https://click.palletsprojects.com/en/7.x/
import requests                 # https://2.python-requests.org/en/master/



class Filing:
    def __init__(self, ftype, url, amount):
        self.ftype = ftype
        self.url = url
        self.amount = amount    # Decimal? Int?


# Generate the list of index files archived in EDGAR since start_year (earliest: 1993) until the most recent quarter
# Return dictionary of d[filepath] = url
def get_urls(start_year = None):
    current_year = datetime.date.today().year
    current_quarter = (datetime.date.today().month - 1) // 3 + 1
    if start_year is None:
        start_year = 2017
    years = list(range(start_year, current_year))
    quarters = ['QTR1', 'QTR2', 'QTR3', 'QTR4']

    # Get the history, and append this year until the current quarter.
    history = [(y, q) for y in years for q in quarters]
    for i in range(1, current_quarter + 1):
        history.append((current_year, 'QTR%d' % i))
    
    # Get the urls - if Python 3.7 or later they should be in order.
    urls = {f'{y}-Q{q[-1]}': 'https://www.sec.gov/Archives/edgar/full-index/%d/%s/crawler.idx' % (y, q) for y,q in history}
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


def parse_filings(path, filings, verbose=False):
    # Make sure the path exists.
    if verbose: print(path)
    if not os.path.exists(path):
        os.makedirs(path)
        if verbose: print("Path did NOT exist - just made: " + path)
    
    total = 0
    num_filings = len(filings)
    i = 0
    for line in filings:
        i += 1
        url = line[98:].strip()
        # Create the file name
        xml = ''
        parts = url.split('/')
        filename = r"{0}/{1}_{2}.xml".format(path, i, parts[-1])
        if verbose: print("Filename = " + filename)
        if os.path.isfile(filename):
            with open(filename) as fr:
                xml = fr.read()
        else:
            xml = get_xml(url, verbose=False)
            # Save the XML file
            if xml is not None:
                with open(filename, "wt") as fh:
                    fh.write(xml)
        if verbose: print(xml)
        try:
            soup = BeautifulSoup(xml, 'lxml')
            if (soup.edgarsubmission.offeringdata.offeringsalesamounts.totalamountsold is not None):
                amt = int(soup.edgarsubmission.offeringdata.offeringsalesamounts.totalamountsold.string)
                total += amt
                #if verbose: print("{0}/{1} Amt: $ {2:,}  Total:$ {3:,}".format(i, num_filings, amt, total))
                print("{0}/{1} Amt: $ {2:,}  Total:$ {3:,}".format(i, num_filings, amt, total))
        except AttributeError:
            print("Error in line: " + line)
        except TypeError:
            print("Error in line: " + line)
            
    print("Total amount: $ {0}".format(total))


@click.command()
def main(filter='D'):
    """Simple program that downloads and parses SEC EDGAR data."""
    click.echo("Downloading EDGAR Form %s" % filter)
    urls = get_urls(2017)
    print("Downloaded {0} URLs".format(len(urls)))
    for path,url in urls.items():
        print(url)
        req = requests.get(url)
        print(req.status_code)
        lines = req.text.splitlines()[9:]   # Remove header
        #filing_types = get_types(lines)
        results = data_filter(filter, lines, False)
        print("Found {0} results".format(len(results)))
        #parse_filings(results[0:3], True)  # Process 1st 3
        path = os.path.join('data', path)
        parse_filings(path, results, False)        # Process all
        #print(req.text)


if __name__ == "__main__":
    main()
