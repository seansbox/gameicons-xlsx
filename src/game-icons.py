import csv
import json
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
        return "paw-print"
    if code == "rapidshare-arrow":
        return "rapid sharing arrow"
    if code == "bal-leth":
        return "bat-leth"


def css_to_csv(css_text, csv_writer):
    # Define a regular expression pattern to match CSS rules
    chars = css_text.split(".game-icon-")
    chars.pop(0)
    print(len(chars), "symbols found")

    # Iterate through the matches and extract the data
    i = 0
    for char in chars:
        pattern = r'(.*):before\s*{\s*content:\s*"\\(.*?)"'
        match = re.findall(pattern, char)
        if not match:
            continue

        name = match[0][0].strip()
        code = match[0][1].strip()
        symbol = chr(int(f"{code}", 16))
        formula = f'=UNICHAR(HEX2DEC("{code}"))'
        i += 1
        desc = store.get(name)
        if desc:
            desc = desc[0]
        # is_two = False
        # if name.endswith("-2"):
        #    is_two = True
        #    name = name[:-2]
        if not desc:
            found = False
            for subname in [name, name.split("-")[0], name.split("-")[-1], fix(name)]:
                if not subname:
                    continue
                if found:
                    break
                json_data = search_gameicons(subname)
                hits = json_data.get("results", [])[0].get("hits", [])
                # if is_two and len(hits) > 1:
                #    hits.pop(0)
                for hit in hits:
                    id = hit.get("id", "").split("/")[-1]
                    if id != name and id != fix(name):
                        continue
                    friendly = hit.get("name", "")
                    content = hit.get("content", "")
                    tags = hit.get("tags", "")
                    desc = f"{friendly}: {content} ({tags})".replace("  ", " ").replace("  ", " ")
                    if is_two:
                        name += "-2"
                    found = True
                    print(i, name, desc)
                    break
            if not found:
                # if is_two:
                #    name += "-2"
                print(str(len(hits)) + " matches but no exact matches for " + name)
                desc = name + " (missing)"
            store.set(name, desc)
        csv_row = [name, symbol, formula, code, desc]
        csv_writer.writerow(csv_row)


# Read CSS from "game-icons.css" file
with open("game-icons.css", "r") as css_file:
    css_input = css_file.read()

# Convert CSS to CSV

# Write CSV data to "game-icons-build.csv" file
with open("game-icons-build.csv", "w", newline="", encoding="utf-8") as csv_file:
    csv_writer = csv.writer(csv_file)
    csv_writer.writerow(["Name", "Symbol", "Formula", "Code", "Description"])
    css_to_csv(css_input, csv_writer)

print("Conversion completed. CSV data saved to 'game-icons-build.csv'.")
