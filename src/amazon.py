import requests
import sys
import utils

'''
NOTES
Bestseller furniture pg

https://www.amazon.com/Best-Sellers-Home-Kitchen-Furniture/zgbs/home-garden/1063306/ref=zg_bs_pg_X
Where X= nmr of pages.(use 1 or 2)

'''

user_agent = 'Mozilla/5.0 (X11; Linux x86_64; rv:68.0) Gecko/20100101 Firefox/68.0'

url_list = []
url_list.append('https://www.amazon.com/Best-Sellers-Home-Kitchen-Furniture/zgbs/home-garden/1063306/ref=zg_bs_pg_1')
url_list.append('https://www.amazon.com/Best-Sellers-Home-Kitchen-Furniture/zgbs/home-garden/1063306/ref=zg_bs_pg_2')

for url in url_list:
    response = requests.get(url)