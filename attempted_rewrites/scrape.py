import os
import requests
from zipfile import ZipFile

MONTHS = [
    "jan01", "apr01", "jul01", "oct01",
    "jan02", "apr02", "jul02", "oct02",
    "jan03", "apr03", "jul03", "oct03",
    "jan04", "apr04", "jul04", "oct04",
    "jan05", "apr05", "jul05", "oct05",
    "jan06", "apr06", "jul06", "oct06",
    "jan07", "apr07", "jul07", "oct07",
    "jan08", "apr08", "jul08", "oct08",
    "jan09", "apr09", "jul09", "sep09", "nov09",
    "jan10", "mar10", "may10", "jul10", "sep10", "nov10",
    "jan11", "mar11", "may11", "jul11", "sep11", "nov11",
    "jan12", "mar12", "may12", "jul12", "aug12", "sep12", "oct12", "nov12", "dec12"
]
MONTHS = MONTHS + [
    f"{month}{yy}" 
    for yy in [str(y)[-2:] for y in range(2013, 2026)] 
    for month in ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"]
    ]
MONTHS = MONTHS + ["jan26", "feb26", "mar26", "apr26", "may26"]


DOWNLOAD_DIR = "fide_historical_ratings_zip"
EXTRACT_DIR = "fide_historical_ratings"

ARCHIVE_URL = "https://ratings.fide.com/download/{month}frl.zip"
MODERN_URL = "https://ratings.fide.com/download/standard_{month}frl.zip"

def scrape():
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    
    session = requests.Session()
    
    use_archive_url = True
        
    for month in MONTHS:
        if month ==  "oct12":
            use_archive_url = False
        
        if use_archive_url:
            url = ARCHIVE_URL.format(month=month)
        else:
            url = MODERN_URL.format(month=month)
        filename = f"{month}.zip"
        local_path = os.path.join(DOWNLOAD_DIR, filename)
        
        # skip if the file is already downloaded
        if os.path.exists(local_path):
            print(f"{filename} already exists locally.")
            continue
        
        print(f"Checking: {url} ...", end=" ")
        
        try:
            # stream the request so you don't load the whole file into memory at once
            with session.get(url, stream=True) as r:
                r.raise_for_status()
                print("Downloading...")
                with open(local_path, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=1024*1024):
                        f.write(chunk)
        except requests.exceptions.RequestException as e:
            print(f"Connection error: {e}")
                
def unzip_files():
    print("Unzipping downloaded files...")
    for filename in os.listdir(DOWNLOAD_DIR):
        if filename.endswith(".zip"):
            zip_path = os.path.join(DOWNLOAD_DIR, filename)
            
            print(f"Extracting {filename}...")
            with ZipFile(zip_path, 'r') as zfile:
                zfile.extractall(EXTRACT_DIR)
    print("Finished extracting all files.")

if __name__ == "__main__":
    scrape()
    unzip_files()


