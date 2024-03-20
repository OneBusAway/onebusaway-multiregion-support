import urllib.request, urllib.error, urllib.parse
import csv
import io

# In both reading cases, we need to read all data into memory
# because there's no way of seeking back in a CSV reader.

def get_csv_from_file(path):
    with open(path) as f:
        reader = csv.DictReader(open(path))
        return list(reader)


def get_csv_from_url(url):
    "Returns a list of regions from the specified spreadsheet URL."
    opener = urllib.request.build_opener(
        urllib.request.HTTPCookieProcessor(),
        urllib.request.HTTPRedirectHandler()
    )
    urllib.request.install_opener(opener)
    response = urllib.request.urlopen(url)
    reader = csv.DictReader(io.TextIOWrapper(response, encoding='utf-8'))
    return list(reader)