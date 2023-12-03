import time
import requests
import pandas as pd
import json
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import yaml
import ssl
import smtplib
from email.message import EmailMessage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from email.utils import make_msgid
from random import randint

def html_soup(driver, url):
    driver.get(url)
    time.sleep(5)
    html_content = driver.page_source
    soup = BeautifulSoup(html_content, 'html.parser')
    return soup

def first_link(soup, website):
    listings_ul = soup.find('ul', class_='hz-Listings hz-Listings--list-view')
    li = listings_ul.find_all('li')
    for i in range(len(li)):
        try:
            _link = f'https://{website}' + str(li[i].find('a')['href'])
            break
        except:
            continue
    return _link

def telegram_bot(requests,pic_url,http_api,chat_id,message):
    response = requests.get(pic_url)
    img = response.content

    # Prepare the file for sending
    file = {'photo': ('image.webp', img)}

    # Send the POST request
    to_url = f'https://api.telegram.org/bot{http_api}/sendPhoto?chat_id={chat_id}&caption={message}'
    requests.post(to_url, files=file)
    print(f'Telegram sent to-- {chat_id}')


def get_criteria(criteria, row):
    id_ = criteria.iloc[row, 0]
    website = criteria.iloc[row, 1]
    brand = criteria.iloc[row, 2]
    model = criteria.iloc[row, 3]
    price_from = criteria.iloc[row, 4]
    price_to = criteria.iloc[row, 5]
    year_from = criteria.iloc[row, 6]
    year_to = criteria.iloc[row, 7]
    return id_, website, brand, model, price_from, price_to, year_from, year_to

def check_link_in_json(link_to_open, json_file_path, driver):
    link_to_check = link_to_open.strip()
    
    with open(json_file_path, 'r') as file:
        data = json.load(file)

    if link_to_check in data["links"]:
        sta = 'yes'
        print("data alread sent -- ignoring")
        driver.quit()
    else:
        sta = 'no'
        print("new data found sending info")
        data["links"].append(link_to_check)

        with open(json_file_path, 'w') as file:
            json.dump(data, file, indent=2)
    return sta

criteria = pd.read_csv('criteria.csv')
users = pd.read_csv('users.csv')
with open('config.yml', 'r') as file:
    data = yaml.safe_load(file)

json_file_path = 'history.json'

chrome_options = Options()
chrome_options.add_argument('--headless')
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')
chrome_options.add_argument('--disable-gpu')
chrome_options.add_argument('--disable-software-rasterizer')
chrome_options.add_argument('--disable-extensions')

while True:
    print('Starting new Session')
    time.sleep(data['wait'])
    print('script started')
    for row in range(criteria.shape[0]):
        id_, website, brand, model, price_from, price_to, year_from, year_to = get_criteria(criteria, row)
        main_url = f'https://{website}/l/auto-s/{brand}/{model}#PriceCentsFrom:{price_from}00|PriceCentsTo:{price_to}00|constructionYearFrom:{year_from}|constructionYearTo:{year_to}|sortBy:SORT_INDEX|sortOrder:DECREASING'
        
        driver = webdriver.Chrome(options=chrome_options)
        # driver = webdriver.Remote("http://localhost:4444", options=webdriver.ChromeOptions())
        main_page_soup = html_soup(driver, main_url)
        link_to_open = first_link(main_page_soup, website)
        print('first scrap done')

        sta = check_link_in_json(link_to_open, json_file_path, driver)
        if sta == 'yes':
            continue

        car_page_soup = html_soup(driver, link_to_open)
        try:
            show_number_button = driver.find_element(By.XPATH, '/html[1]/body[1]/div[1]/main[1]/div[3]/div[2]/aside[1]/div[1]/div[2]/button[2]/span[2]')
            show_number_button.click()
            
            wait = WebDriverWait(driver, 5)
            element = wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'PhoneDialog-phone')))
            phone = driver.find_element(By.CLASS_NAME, 'PhoneDialog-phone').text

        except:
            phone = '0'+str(randint(653113242,850665636))

        title = car_page_soup.find('h1', class_='Listing-title').text
        meta_tag = car_page_soup.find('meta', property='og:image')
        img_link = meta_tag.get('content')
        price = car_page_soup.find('div', class_='Listing-price').text.replace('\xa0', ' ')
        name = car_page_soup.find('span', class_='SellerInfo-name').text
        address = car_page_soup.find('div', class_='SellerInfo-rowWithIcon').text
        descrip = car_page_soup.find('div', class_='Description-description').text.replace('\xa0', ' ')[:150] + ' ...'
        
        driver.quit()

        for row in range(users.shape[0]):
            criteria_id = users.iloc[row, 0]
            if criteria_id == id_:
                pass
            else:
                continue
            email_r = str(users.iloc[row, 1])
            chat_id = str(users.iloc[row, 2])
            print('running')
            email_sender = data['email']
            email_password = data['pas']
            email_receiver = email_r
            http_api = data['http_api']
            subject = f'{title}--{price}'

            body = f'<h2><strong>{title}</strong></h2><br/> <strong>Price:</strong> {price}<br/> <strong>Name:</strong> {name}<br/> <strong>Phone:</strong> {phone}<br/> <strong>Address:</strong> {address}<br/> <strong>Description:</strong> {descrip}<br/> <strong>Link to post:</strong> {link_to_open}'

            em = MIMEMultipart('related')
            em['From'] = email_sender
            em['To'] = email_receiver
            em['Subject'] = subject

            msgText = MIMEText('<div style="font-weight: bold;">%s</div><br/><img src="cid:%s"/><br/>' % (body, make_msgid()), 'html')
            em.attach(msgText)

            image_url = img_link
            image_data = requests.get(image_url).content
            image = MIMEImage(image_data, _subtype='webp', name='image.webp')
            image.add_header('Content-ID', make_msgid())
            em.attach(image)

            context = ssl.create_default_context()

            with smtplib.SMTP_SSL('smtp.gmail.com', 465, context=context) as smtp:
                smtp.login(email_sender, email_password)
                smtp.sendmail(email_sender, email_receiver, em.as_string())

            print(f'Email sent to -- {email_receiver}')

            message = f'{title}\nPrice: {price}\nName: {name}\nPhone: {phone}\nAddress: {address}\nDescription: {descrip}\nLink to post: {link_to_open}'

            telegram_bot(requests, img_link, http_api, chat_id, message)
            
