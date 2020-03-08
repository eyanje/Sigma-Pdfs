#!bin/python3

from argparse import ArgumentParser
from io import BytesIO
from itertools import chain
import os
from pathlib import Path
import re
from urllib import request
from tkinter import Tk

from bs4 import BeautifulSoup
from dotenv import load_dotenv
from PyPDF2 import PdfFileReader, PdfFileMerger

default_link_whitelist = '[0-9]+|/(final|extra|opening|tiebreaker)/i|' # Traverse all links with numbers in them
default_url_whitelist = '(historybowl\.com)|(.pdf)'
progress_bar_len = 20

load_dotenv()

################ Utility #######################

def progress_bar(progress):
    displayed = int(progress * progress_bar_len)
    prog = '#' * displayed
    unprog = '.' * (progress_bar_len - displayed)
    return f'[{prog}{unprog}]'

def urlopen(url):
    """
    Opens the url with a special User-Agent
    """
    user_agent = 'Mozilla/5.0 Gecko/20100101 Firefox/68.0' 
    headers = {
        'User-Agent': user_agent
    }
    req = request.Request(url, headers=headers)
    return request.urlopen(req)

def get_download_path(name):
    if not name.endswith('.pdf'):
        name += '.pdf'
    return str(Path('.') / os.getenv('DOWNLOAD_DIRECTORY') / name)

def get_min_page_title(url):
    """
    Reads the title of a page and trims out fluff
    """

    if (url.endswith('.pdf')):
        return url[url.rfind('/') + 1:]

    with urlopen(url) as data:
        soup = BeautifulSoup(data, 'html.parser')
    title = soup.find('title').text

    fluff = r' [\-–] National History Bee & Bowl [\-–] .+ Division'
    fluffRe = re.compile(fluff)
    fluffMatch = fluffRe.search(title)
    if fluffMatch != None:
        title = title[:fluffMatch.start()]
    return title

def get_pdf_urls_rec(url, link_whitelist=default_link_whitelist):
    """
    Reads a url and extracts lists pertaining to a whitelist
    """

    if url.endswith('.pdf'):
        return (url,)

    with urlopen(url) as data:
        soup = BeautifulSoup(data, 'html.parser')

    content = soup.find(id='content')
    post_contents = content.find_all(class_='post-content')

    # Find links
    links = (c.find_all('a', href=True) for c in post_contents)
    links = chain.from_iterable(links) # Flatten list
    
    # Filter links
    wl_re = re.compile(link_whitelist)
    filter_func = lambda l: wl_re.search(l.text) and re.compile(default_url_whitelist).search(l['href'])
    links = filter(filter_func, links)

    pdfs = list()
    for link in links:
        pdfs.extend(get_pdf_urls_rec(link['href'], link_whitelist))

    return pdfs

################ Clipboard ####################

def convert_hex(hex_codes):
    codes = hex_codes.strip().split(' ')
    text = ''.join(chr(int(c, 16)) for c in codes)
    return text

def read_clipboard_urls(sep=None):
    tk = Tk()
    tk.withdraw()
    
    clip = tk.clipboard_get()
    del tk
    urls = clip.split(sep=sep)
    urls = tuple(u.strip() for u in urls)

    return urls

def get_clipboard_html():
    """
    Converts the clipboard contents to HTML
    """
    tk = Tk()
    tk.withdraw()
    
    clip = tk.clipboard_get(ype='text/html')
    del tk
    html = convert_hex(clip)

    return html

def read_clipboard_links():
    """
    Reads HTML in the clipboard and extracts link urls
    """
    soup = BeautifulSoup(get_clipboard_html(), 'html.parser')
    
    links = soup.find_all('a', href=True)
    urls = tuple(l['href'] for l in links)
    
    return urls

################ Making the PDFs ###############

def fetch_pdf(url):
    with urlopen(url) as data:
        data = BytesIO(data.read())
    return PdfFileReader(data)

def download_merge_urls(urls, dest_path):
    """
    Downloads the specified files as pdfs
    This is the central code working with pdfs.
    """
    
    print(f'Downloading and merging {len(urls)} pdfs')

    merger = PdfFileMerger()

    for i,url in enumerate(urls):
        progress = (i + 1)/len(urls)
        print(f'\r{progress_bar(progress)} {(i+1)}/{len(urls)}', end='')
        pdf_reader = fetch_pdf(url)
        merger.append(pdf_reader)
    print()

    # Ensure containing directory
    containing_dir = Path(dest_path).parent
    if not os.path.isdir(containing_dir):
        print('Creating directory', containing_dir)
        os.makedirs(containing_dir)

    print(f'Writing pdfs to {dest_path}')
    merger.write(dest_path)
    print('Done')

def download_all_separate(urls, name=None):
    """
    A simple function that does all the default stuff
    """

    for url in urls:
        if name == None:
            name = get_min_page_title(url)
    
        print('Fetching list of urls...')
        suburls = get_pdf_urls_rec(url)

        dlPath = get_download_path(name)
        download_merge_urls(suburls, dlPath)

        name = None

def download_all_together(urls, name=None):
    """
    Merges all pdfs into one file
    """
    if not urls:
        return

    if not name:
        name = get_min_page_title(urls[0])

    dl_urls = list()

    print('Fetching list of urls...')
    for url in urls:
        pdf_urls = get_pdf_urls_rec(url)
        dl_urls.extend(pdf_urls)

    dlPath = get_download_path(name)
    download_merge_urls(pdf_urls, dlPath)

def download_all_conditional(urls, name=None, together=False):
    if together:
        return download_all_together(urls, name)
    else:
        return download_all_separate(urls, name)

################ Testing ######################

def test(test_url='https://www.historybowl.com/2018-2019-regional-and-state-tournament-questions/'):
    print('Getting name')
    print(get_min_page_title(test_url))
    print('Getting urls')
    print(get_pdf_urls_rec(test_url))

# Argument Parsing

################ Running #######################

parser = ArgumentParser(description='Downloads and perges pdfs from the History Bowl website')
parser.add_argument('url', nargs='*')
# Allows all urls to be merged into one pdf
parser.add_argument('--cu', '--clipboard-urls', action='store', dest='sep',
        help=r'Include urls stored in the clipboard, delimited by sep. Use n to specify newlines.')
parser.add_argument('--cl', '--clipboard-links', action='store_true',
        help='Include urls stored in links in the clipboard')
parser.add_argument('-n', '--name', action='store', dest='name',
        help='Saves the PDF with a specified name')
parser.add_argument('-t', '--together', action='store_true', dest='together',
        help='Merges all urls into one pdf, even if multiple urls are passed')

args = parser.parse_args()

urls = args.url

# Read urls directly
if (args.sep):
    sep = '\n'.join(args.cu.split(r'\n'))    # Convert \n into linebreaks
    sep = '\n'.join(args.cu.split('n'))    # Convert \n into linebreaks

    cl_urls = read_clipboard_urls(sep)
    print('Clipboard contains urls:')
    for cu in cl_urls:
        print(cu)
    urls.extend(cl_urls)

# Read urls from links
if (args.cl):
    cl_urls = read_clipboard_links()
    print('Clipboard contains urls:')
    for cu in cl_urls:
        print(cu)
    urls.extend(cl_urls)

# Filter out empty urls
urls = tuple(filter(bool, urls))

if (urls):
    download_all_conditional(urls, args.name, args.together)
else:
    print('ERROR: No urls specified!')
    print()
    parser.print_help()
