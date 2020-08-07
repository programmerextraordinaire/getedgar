"""

main.py

Main program to download and parse EDGAR data from the SEC website.

--tkp

2020-08-07  Init commit

"""


import click        # https://click.palletsprojects.com/en/7.x/
import requests     # https://2.python-requests.org/en/master/

url = "https://www.sec.gov/Archives/edgar/daily-index/"

@click.command()
def main(filter='D'):
    """Simple program that downloads and parses SEC EDGAR data."""
    click.echo("Downloaded EDGAR Form %s" % filter)

if __name__ == "__main__":
    main()
