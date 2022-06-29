import json
import pandas as pd
from requests_html import HTMLSession
import time
import regex
from datetime import timedelta

class amazonScraper:
    def __init__(self, csv_path):
        self.csv_path = csv_path
        self.output_list = []

    def csv_extractor(self):
        # Function to extract and return list of ASIN and Country-code from CSV file.
        dataset = pd.read_csv(self.csv_path)
        df = pd.DataFrame(dataset)
        country = list(df['country'])
        asin = list(df['Asin'])
        return country, asin

    def scraper(self, country, asin):
        s = HTMLSession()
        url = f'https://www.amazon.{country}/dp/{asin}'

        # initialising output dictionary with null values.
        output = {'Product Title': 'NA', 'Product Image URL': 'NA', 'Price of the Product': 'NA', 'Product Details': 'NA', 'URL' : url}
        resp = s.get(url)
        if resp.status_code == 200:
            try:
                product_details_ = resp.html.xpath("//ul[contains(@class, 'detail')] | //table[@role='presentation']", first=True)
                product_details = {}
                try:
                    df = [i.split(':') for i in product_details_.text.split('\n')]
                    for ls in df:
                        product_details[''.join(str(i) for i in str(ls[0]) if ord(i) < 128).strip()] = ''.join(i for i in str(ls[1]) if ord(i) < 128).strip()
                except:
                    df_ = product_details_.text.split('\n')
                    index = 0
                    while index in range(len(df_)):
                        product_details[(''.join(str(i) for i in (df_[index]) if ord(i) < 128)).strip()] = (''.join(str(i) for i in (df_[index+1]) if ord(i) < 128)).strip()
                        index += 2
                # Single product output file.        
                output = {
                    'Product Title': resp.html.xpath("//span[@id='productTitle']", first=True).text,
                    'Product Image URL': (resp.html.xpath("//img[contains(@class,'stretch-horizontal')] | //img[contains(@class,'stretch-vertical')]", first=True)).attrs['src'],
                    'Price of the Product': ''.join(i for i in str(regex.findall(r"\d+[.|,]\d+[^\p{Sc}|$\p{Sc}]", resp.html.xpath("//span[contains(text(),'€')]", first=True).text)[0]).replace(',','.') if i.isnumeric() or i == '.'),
                    'Product Details': product_details,
                    'URL' : url
                }
                # Appending dictionary to main list.
                self.output_list.append(output)
            except Exception as e:
                print('*'*50)
                print(e)
                print(resp.html)
                print('*'*50)
        elif resp.status_code == 404:
            print('*'*50)
            print(f'{url} : 404 Not found.')
            print('*'*50)
        else:
            print('*'*50)
            print(f'{url} : {resp.status_code} Error code.')
            print('*'*50)

    def main(self):
        countries, asins = self.csv_extractor()
        for country, asin in zip(countries, asins):
            if len(self.output_list) < 101:
                self.scraper(country, asin)
                # Implicitly sleeping for 30 seconds to avoid IP blocking / Reducing requests per second (load) to avoid detection.
                # To avoid this step you can use proxies and then multithreading.
                time.sleep(30)
            else:
                break
        # Converting list of dictionaries to JSON.
        data = json.dumps(self.output_list, indent=2)
        with open("output.json", "w") as final:
            final.write(data)
        
        return self.output_list # Returning list of dictionaries.

PATH = 'CSV FILE PATH'
obj = amazonScraper(PATH)

start_time = time.time()
obj.main()
print(f" {timedelta(seconds = (time.time() - start_time))} (Hours : Minutes: Seconds)")
