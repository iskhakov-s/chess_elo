import os
import requests
import zipfile

MONTHS = ("jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec")
DOWNLOAD_DIR = "fide_historical_ratings_zip"
EXTRACT_DIR = "fide_historical_ratings"

def scrape():
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    
    session = requests.Session()

    for year in range(2000, 2013):
        yy = str(year)[-2:]
        
        for month in MONTHS:
            # url = f"https://ratings.fide.com/download/standard_{month}{yy}frl.zip"
            url= f"https://ratings.fide.com/download/{month}{yy}frl.zip"
            filename = url.split('/')[-1]
            local_path = os.path.join(DOWNLOAD_DIR, filename)
            
            # Skip if the file is already downloaded
            if os.path.exists(local_path):
                print(f"[SKIP] {filename} already exists locally.")
                continue
            
            print(f"Checking: {url} ...", end=" ")
            
            try:
                # We stream the request so we don't load the whole file into RAM at once
                with session.get(url, stream=True) as r:
                    if r.status_code == 200:
                        print("FOUND! Downloading...")
                        with open(local_path, 'wb') as f:
                            for chunk in r.iter_content(chunk_size=8192):
                                f.write(chunk)
                    elif r.status_code == 404:
                        print("Not Found (404) - Skipping.")
                    else:
                        print(f"Failed with status code: {r.status_code}")
                        
            except requests.exceptions.RequestException as e:
                print(f"Connection error: {e}")

def confirm_downloads():
    print("Verifying downloaded files...")
    for year in range(2000, 2026):
        print("\n", year)
        yy = str(year)[-2:]
        for month in MONTHS:
            filename1 = f"{month}{yy}frl.zip"
            filename2 = f"standard_{month}{yy}frl.zip"
            local_path1 = os.path.join(DOWNLOAD_DIR, filename1)
            local_path2 = os.path.join(DOWNLOAD_DIR, filename2)

            if os.path.exists(local_path1) or os.path.exists(local_path2):
                print(month, sep=" ")
                
def unzip_files():
    print("Unzipping downloaded files...")
    for filename in os.listdir(DOWNLOAD_DIR):
        if filename.endswith(".zip"):
            zip_path = os.path.join(DOWNLOAD_DIR, filename)
            
            print(f"Extracting {filename}...")
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(EXTRACT_DIR)
           
# misc functions to organize data  
FORMATTED_DIR = "fide_historical_ratings_formatted"
def move_formatted_files():
    print("Moving formatted files to the main directory...")
    for filename in os.listdir(EXTRACT_DIR):
        if filename.endswith(".csv"):
            src_path = os.path.join(EXTRACT_DIR, filename)
            dst_path = os.path.join(FORMATTED_DIR, filename)
            os.rename(src_path, dst_path)

def remove_prefix():
    for filename in os.listdir(FORMATTED_DIR):
        src_path = os.path.join(FORMATTED_DIR, filename)
        dst_path = os.path.join(FORMATTED_DIR, filename.lstrip(FORMATTED_DIR))
        os.rename(src_path, dst_path)

if __name__ == "__main__":
    # print("Starting streamlined FIDE downloads...")
    # main()
    remove_prefix()
    # print("Finished checking all combinations.")


