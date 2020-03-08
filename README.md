# Sigma, a PDF dowloader for History Bowl

## Prerequisites

You will need [Python 3](//python.org) to run these.

Python packages

 - BeautifulSoup 4
 - PyPDF2
 - dotenv

You can install them with
```
python3 -m pip install bs4 PyPDF2 python-dotenv
```
or with
```
python3 -m pip install -r requirements.txt
```

## Usage

```
usage: sigma.py [-h] [--cu SEP] [--cl] [-n NAME] [-t] [url [url ...]]

Downloads and perges pdfs from the History Bowl website

positional arguments:
  url

optional arguments:
  -h, --help            show this help message and exit
  --cu SEP, --clipboard-urls SEP
                        Include urls stored in the clipboard, delimited by
                        sep. Use n to specify newlines.
  --cl, --clipboard-links
                        Include urls stored in links in the clipboard
  -n NAME, --name NAME  Saves the PDF with a specified name
  -t, --together        Merges all urls into one pdf, even if multiple urls
                        are passed
```
