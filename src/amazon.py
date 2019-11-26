import requests
import sys
import utils
import logging
import os
import time
from logging import handlers
from bs4 import BeautifulSoup
import scrapy
from multiprocessing import Queue, Manager
import threading
import pandas as pd
import re
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

project_directory = utils.get_project_root()
csv_directory = str(project_directory) + '/csv/'
script_name = os.path.basename(__file__)

# Logs directory setup
logs_directory = os.path.join(project_directory, 'logs')
if not os.path.exists(logs_directory):
    os.makedirs(logs_directory)

if not os.path.exists(csv_directory):
    os.makedirs(csv_directory)

# LOGGING
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
log_template = '%(asctime)s %(module)s %(levelname)s: %(message)s'
formatter = logging.Formatter(log_template)

# Logging - File Handler
log_file_size_in_mb = 10
count_of_backups = 5  # example.log example.log.1 example.log.2
log_file_size_in_bytes = log_file_size_in_mb * 1024 * 1024
log_filename = os.path.join(logs_directory, os.path.splitext(script_name)[0]) + '.log'
file_handler = handlers.RotatingFileHandler(log_filename, maxBytes=log_file_size_in_bytes,
                                            backupCount=count_of_backups)
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

# Logging - STDOUT Handler
stdout_handler = logging.StreamHandler(sys.stdout)
stdout_handler.setFormatter(formatter)
logger.addHandler(stdout_handler)

# This function will return all bestsellers product pages
def get_bestsellers_links(page):
    amazon_url = "https://www.amazon.com"
    
    try:
        headers = {"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:66.0) Gecko/20100101 Firefox/66.0", "Accept-Encoding":"gzip, deflate", "Accept":"text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8", "DNT":"1","Connection":"close", "Upgrade-Insecure-Requests":"1"}
        r = requests.get("https://www.amazon.com/Best-Sellers-Home-Kitchen-Furniture/zgbs/home-garden/1063306/ref=zg_bs_pg_2?_encoding=UTF8&pg="+str(page), headers=headers)
        content = r.content
        soup = BeautifulSoup(content, features="lxml")
        product_links = []

        for section in soup.findAll('div', attrs={'class':'a-fixed-left-grid-col a-col-right'}):
            for href in section.findAll('a', attrs={'class':'a-link-normal'}):
                if href is not None:
                    skip_element = False
                    link_filter = re.search('product-reviews', str(href))
                    skip_test1 = re.search('new-releases', str(href))
                    skip_test2 = re.search('most-wished-for', str(href))
                    skip_test3 = re.search('most-gifted', str(href))
                    if skip_test1 is not None or skip_test2 is not None or skip_test3 is not None:
                        skip_element = True
                    # if it is none, its a product url
                    if link_filter is None and skip_element != True:
                        product_link = amazon_url + href.get('href')
                        product_links.append(product_link)
                else:
                    logger.debug('----- MISSING DATA -----')
                    continue
    except Exception as exception:
        logger.error(exception)
    
    return product_links

def get_product_data(url, q):  
    headers = {"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:66.0) Gecko/20100101 Firefox/66.0", "Accept-Encoding":"gzip, deflate", "Accept":"text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8", "DNT":"1","Connection":"close", "Upgrade-Insecure-Requests":"1"}
    
    session = requests.Session()
    # retry time = {backoff factor} * (2 ^ ({number of total retries} - 1))
    retry = Retry(connect=5, backoff_factor=0.5)
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)

    r = session.get(url, headers=headers)

    #r = requests.get(url, headers=headers)
    content = r.content
    soup = BeautifulSoup(content, features="lxml")
	
    for main_section in soup.findAll('div', attrs={'class':'home en_US'}):
        #main_section.find('', attrs={'':''})
        product_info = []
        name = main_section.find('span', attrs={'id':'productTitle', 'class': 'a-size-large'})
        price = main_section.find('span', attrs={'id':'priceblock_ourprice'})
        review_qtd = main_section.find('span', attrs={'id':'acrCustomerReviewText'})
        rating_overall = main_section.find('span', attrs={'class':'a-icon-alt'})
        availability = main_section.find('span', attrs={'class': 'a-size-medium a-color-success'})

        if name is not None:
            product_info.append(name.text.strip())
        else:
            product_info.append("name-missing-data")
 
        if price is not None:
            product_info.append(price.text.strip())
        else:
            product_info.append('price-missing-data')
		
        if review_qtd is not None:
            product_info.append(review_qtd.text.strip())
        else:
            product_info.append('review-qtd-missing-data')

        if rating_overall is not None:
            product_info.append(rating_overall.text.strip())
        else:
            product_info.append('rating-missing-data')

        if availability is not None:
            product_info.append(availability.text.strip())
        else:
            product_info.append('availability-missing-data')

        q.put(product_info)


if __name__ == '__main__':
    n_pages = 2
    startTime = time.time()
    
    # Searching into the bestsellers, we will scrap all of the bestsellers links first
    p_links = []
    for i in range(1, (n_pages+1)):
        tmp_p_links = get_bestsellers_links(i)
        p_links += tmp_p_links

    utils.remove_duplicates(p_links)
    
    df_bestsellers_links = pd.DataFrame({'Product link page':p_links})
    df_bestsellers_links.to_csv(csv_directory+'amazon_bestseller_products_links.csv', index=True, encoding='utf-8')
    
    # Now we have a array(and a .csv file) with all bestsellers links and what we wanna do is
    # to get the product info. I'll be using threading for more speed
    m = Manager()
    q = m.Queue()
    p = {}
    for i in range(0, len(p_links)):
        logger.debug("starting thread {}".format(i))
        p[i] = threading.Thread(target=get_product_data, args=(p_links[i],q))
        p[i].start()

    # Join process
    for i in range(0, len(p_links)):
        p[i].join()
    
    p_name, p_price, p_rating_qtd, p_rating_overall, p_availability = [], [], [], [], []
    while q.empty() is not True:
        queue_top = q.get()
        p_name.append(queue_top[0])
        p_price.append(queue_top[1])
        p_rating_qtd.append(queue_top[2])
        p_rating_overall.append(queue_top[3])
        p_availability.append(queue_top[4])
    
    df_bestsellers_products = pd.DataFrame({'Product Name': p_name,
                                            'Price':p_price,
                                            'Review Nº':p_rating_qtd,
                                            'Overall Rating:':p_rating_overall,
                                            'Stock Availability':p_availability})
    
    df_bestsellers_products.to_csv(csv_directory+'amazon_bestseller_products_information.csv', index=True, encoding='utf-8')

    logger.debug("total time taken {} seconds".format(str(time.time()-startTime)))