import csv
import json
import os
import re
import urllib.request

import CSVKeyValueStore

store = CSVKeyValueStore.CSVKeyValueStore("game-icons-cache.csv")


# Queries Algolia search API for https://game-icons.net/
# Extracted from game-icons.net, so please use with caution.
def search_gameicons(query, page=0):
    query = re.sub(r"-", " ", query)  # actually better results to search approximate name rather than literal
    url = f"https://9hq1yxukvc-dsn.algolia.net/1/indexes/*/queries?x-algolia-agent=Algolia%20for%20vanilla%20JavaScript%20(lite)%203.24.5%3Binstantsearch.js%202.4.1%3BJS%20Helper%202.23.0&x-algolia-application-id=9HQ1YXUKVC&x-algolia-api-key=fa437c6f1fcba0f93608721397cd515d"

    headers = {
        "Accept-Language": "en-US,en;q=0.9,ceb;q=0.8",
        "Connection": "keep-alive",
        "DNT": "1",
        "Origin": "https://game-icons.net",
        "Referer": "https://game-icons.net/",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "cross-site",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
        "accept": "application/json",
        "content-type": "application/x-www-form-urlencoded",
        "sec-ch-ua": '"Chromium";v="118", "Google Chrome";v="118", "Not=A?Brand";v="99"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": "macOS",
    }

    data = {
        "requests": [
            {
                "indexName": "icons",
                "params": f"query={query}&page={page}&highlightPreTag=__ais-highlight__&highlightPostTag=__%2Fais-highlight__&facets=%5B%5D&tagFilters=",
            }
        ]
    }

    try:
        # Encode the data
        data_encoded = json.dumps(data).encode("utf-8")

        # Create a request
        req = urllib.request.Request(url, data=data_encoded, headers=headers)

        # Send a POST request
        response = urllib.request.urlopen(req)

        if response.status != 200:
            print(f"Failed to fetch page {page}.")
            return None

        # Read and decode the JSON content
        json_data = json.loads(response.read().decode("utf-8"))
        return json_data

    except Exception as e:
        print(f"Error while fetching page {page}: {str(e)}")
        return None


# A few search fix-ups where the CSS name doesn't align with the search name
def fix(code):
    if code == "d4":
        return "dice 4"
    if code == "d10":
        return "dice 10"
    if code == "d12":
        return "dice 12"
    if code == "pawprint":
        return "paw print"
    if code == "rapidshare-arrow":
        return "rapid sharing arrow"


def css_to_csv(css_text, csv_writer):
    # Define a regular expression pattern to match CSS rules
    pattern = r'\.game-icon-(.*):before\s*{\s*content:\s*"\\f(.*?)"\s*;\s*}'

    # Find all matches in the CSS text
    matches = re.findall(pattern, css_text)

    # Iterate through the matches and extract the data
    i = 0
    for match in matches:
        code = match[0].strip()
        hex_value = match[1].strip()
        unicode_char = f'=UNICHAR(HEX2DEC("{hex_value}"))'
        i += 1
        csv_row = store.get(code)
        is_two = False
        if code.endswith("-2"):
            is_two = True
            code = code[:-2]
        if not csv_row:
            found = False
            for subcode in [code, code.split("-")[0], code.split("-")[-1], fix(code)]:
                if not subcode:
                    continue
                if found:
                    break
                json_data = search_gameicons(subcode)
                hits = json_data.get("results", [])[0].get("hits", [])
                if is_two and len(hits) > 1:
                    hits.pop(0)
                for hit in hits:
                    id = hit.get("id", "").split("/")[-1]
                    if id != code:
                        continue
                    name = hit.get("name", "")
                    content = hit.get("content", "")
                    tags = hit.get("tags", "")
                    description = f"{name}: {content} ({tags})".replace("  ", " ").replace("  ", " ")
                    if is_two:
                        code += "-2"
                    csv_row = [code, unicode_char, description]
                    store.set(code, *csv_row)
                    found = True
                    print(i, csv_row)
                    break
            if not found:
                if is_two:
                    code += "-2"
                print(str(len(hits)) + " matches but no exact matches for " + code)
                print(hits)
                csv_row = [code, unicode_char, code + " (missing)"]
                store.set(code, *csv_row)
                print(i, csv_row)
        csv_writer.writerow(csv_row)


def download_if_not_exists(url, local_filename):
    """
    Download the specified file from the given URL if it doesn't exist locally.
    """
    if not os.path.exists(local_filename):
        try:
            with urllib.request.urlopen(url) as response, open(local_filename, "wb") as out_file:
                out_file.write(response.read())
            print(f"{local_filename} downloaded successfully!")
        except Exception as e:
            print(f"Error while downloading {local_filename}: {str(e)}")
    else:
        print(f"{local_filename} already exists!")


download_if_not_exists("https://github.com/seiyria/gameicons-font/raw/master/dist/game-icons.css", "game-icons.css")
download_if_not_exists("https://github.com/seiyria/gameicons-font/raw/master/dist/game-icons.ttf", "game-icons.ttf")


# Read CSS from "game-icons.css" file
with open("game-icons.css", "r") as css_file:
    css_input = css_file.read()

# Convert CSS to CSV

# Write CSV data to "game-icons-build.csv" file
with open("game-icons-build.csv", "w", newline="") as csv_file:
    csv_writer = csv.writer(csv_file)
    csv_writer.writerow(["Name", "Char", "Description"])
    css_to_csv(css_input, csv_writer)

print("Conversion completed. CSV data saved to 'game-icons-build.csv'.")
