import requests
import time
import random
import pandas as pd
import json
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from seleniumwire import webdriver
import yaml
import smtplib
import ssl
from email.message import EmailMessage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from email.utils import make_msgid



def html_soup(driver,url):
    #here we will add proxies
    
    
#     driver = webdriver.Edge()
    driver.get(url)
    # Allow time for the page to load (you may need to adjust the sleep duration)
    time.sleep(5)

    # Get the updated HTML content after JavaScript has executed
    html_content = driver.page_source

    # Close the WebDriver
#     driver.quit()

    # Now you can use BeautifulSoup to parse the HTML as before
    soup = BeautifulSoup(html_content, 'html.parser')
    
    
    
    return soup


def first_link(soup,website):
    listings_ul = soup.find('ul', class_='hz-Listings hz-Listings--list-view')
    li = listings_ul.find_all('li')
    for i in range(len(li)):
        try:
            _link = f'https://{website}'+str(li[i].find('a')['href'])
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
    print('Telegram sent')
    
def get_criteria(criteria,row):
    id_ = criteria.iloc[row, 0]
    website = criteria.iloc[row, 1]
    brand = criteria.iloc[row, 2]
    model = criteria.iloc[row, 3]
    price_from = criteria.iloc[row, 4]
    price_to = criteria.iloc[row, 5]
    year_from = criteria.iloc[row, 6]
    year_to = criteria.iloc[row, 7]
    return id_,website,brand,model,price_from,price_to,year_from,year_to

def random_proxy(proxies_df):
    #selecting random proxies
    random_proxy = proxies_df.sample()
    proxy = random_proxy['proxy'].values[0]
    port = random_proxy['port'].values[0]
    user = random_proxy['user'].values[0]
    password = random_proxy['pass'].values[0]

    options = {
       'proxy': {
           'https': f'http://{user}:{password}@{proxy}:{port}'
#            'http': f'https://{user}:{password}@{proxy}:{port}',
#            'no_proxy': 'localhost,127.0.0.1' # excludes
       }
    }
    return options



def check_link_in_json(link_to_open, json_file_path,driver):
    link_to_check = link_to_open.strip()
    
    with open(json_file_path, 'r') as file:
        data = json.load(file)

    if link_to_check in data["links"]:
        sta = 'yes'
        print("Yes")
        driver.quit()
    
    else:
        sta = 'no'
        print("No")
        # If the link is not present, append it to the list
        data["links"].append(link_to_check)

        # Save the updated data back to the JSON file
        with open(json_file_path, 'w') as file:
            json.dump(data, file, indent=2)
    return sta
    
criteria = pd.read_csv('criteria.csv')
proxies_df = pd.read_csv('proxy.csv')

users = pd.read_csv('users.csv')
with open('config.yml', 'r') as file:
    data = yaml.safe_load(file)
    
json_file_path = 'history.json'

while True:
    time.sleep(data['wait'])
    for row in range(criteria.shape[0]):
        id_,website,brand,model,price_from,price_to,year_from,year_to = get_criteria(criteria,row)[0],get_criteria(criteria,row)[1],get_criteria(criteria,row)[2],get_criteria(criteria,row)[3],get_criteria(criteria,row)[4],get_criteria(criteria,row)[5],get_criteria(criteria,row)[6],get_criteria(criteria,row)[7]

        main_url = f'https://{website}/l/auto-s/{brand}/{model}#PriceCentsFrom:{price_from}00|PriceCentsTo:{price_to}00|constructionYearFrom:{year_from}|constructionYearTo:{year_to}|sortBy:SORT_INDEX|sortOrder:DECREASING'
        # print(main_url)

        # options  = random_proxy(proxies_df)
        # print(options)

        # driver = webdriver.Edge(seleniumwire_options=options)
        options = Options()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        # driver = webdriver.Chrome(options=options)
        driver = webdriver.Edge(options=options)
        
        main_page_soup = html_soup(driver,main_url)
        
        link_to_open = first_link(main_page_soup,website)
        
        # print(link_to_open)
        
        sta = check_link_in_json(link_to_open, json_file_path,driver)
        if sta == 'yes':
            continue
        else:
            pass
        
        car_page_soup = html_soup(driver,link_to_open)
        
        show_number_button = driver.find_element(By.XPATH, '//*[@id="seller-sidebar-root"]/div[2]/button[2]')
        show_number_button.click()
        # html_content2 = driver.page_source
            # Wait for the element to be present
        wait = WebDriverWait(driver, 5)
        element = wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'PhoneDialog-phone')))
        
        
        phone = driver.find_element(By.CLASS_NAME, 'PhoneDialog-phone').text
        
        
        
        title = car_page_soup.find('h1', class_='Listing-title').text

            # Find the meta tag with the property attribute 'og:image'
        meta_tag = car_page_soup.find('meta', property='og:image')

        # Extract the content attribute, which contains the hyperlink
        img_link = meta_tag.get('content')
        
        price = car_page_soup.find('div', class_='Listing-price').text.replace('\xa0',' ')
        
        name = car_page_soup.find('span', class_='SellerInfo-name').text
        
        address = car_page_soup.find('div', class_='SellerInfo-rowWithIcon').text
        
        descrip = car_page_soup.find('div', class_='Description-description').text.replace('\xa0',' ')[:150]+' ...'
        
        driver.quit()
        
        for row in range(users.shape[0]):
            criteria_id = users.iloc[row, 0]
            if criteria_id == id_:
                pass
            else:
                continue
            email_r = str(users.iloc[row, 1])
            chat_id = str(users.iloc[row, 2])

            email_sender = data['email']
            email_password = data['pas']
            email_receiver = email_r
            
            http_api = data['http_api']
            
            subject = f'{title}--{price}'
            
            
            body = f'<h2><strong>{title}</strong></h2><br/> <strong>Price:</strong> {price}<br/> <strong>Name:</strong> {name}<br/> <strong>Phone:</strong> {phone}<br/> <strong>Address:</strong> {address}<br/> <strong>Description:</strong> {descrip}<br/> <strong>Link to post:</strong> {link_to_open}'

    #         body = f'{title}<br/> Price -- {price}<br/> Name -- {name}<br/> Address -- {address}<br/> description -- {descrip}<br/> link to post: {link_to_open}'

            # Create a MIMEMultipart object with subtype 'related'
            em = MIMEMultipart('related')
            em['From'] = email_sender
            em['To'] = email_receiver
            em['Subject'] = subject

            # Create a MIMEText object with the HTML content of the email
    #         msgText = MIMEText('<b>%s</b><br/><img src="cid:%s"/><br/>' % (body, make_msgid()), 'html')
            msgText = MIMEText('<div style="font-weight: bold;">%s</div><br/><img src="cid:%s"/><br/>' % (body, make_msgid()), 'html')
            em.attach(msgText)

            # Add image from URL
            image_url = img_link # Replace with your image URL
            image_data = requests.get(image_url).content

            # Create a MIMEImage object with the image data
            image = MIMEImage(image_data, _subtype='webp', name='image.webp')
            image.add_header('Content-ID', make_msgid())
            em.attach(image)

            # Add SSL (layer of security)
            context = ssl.create_default_context()

            # Log in and send the email
            with smtplib.SMTP_SSL('smtp.gmail.com', 465, context=context) as smtp:
                smtp.login(email_sender, email_password)
                smtp.sendmail(email_sender, email_receiver, em.as_string())

            print('Email sent')
            


            # print('phone','--',phone)
            # print('title','--',title)
            # print('price','--',price)
            # print('name','--',name)
            # print('address','--',address)
            # print('descrip','--',descrip)
            # print('img_link','--',img_link)
            # print(http_api,'---',chat_id)
            
            message = f'{title}\nPrice: {price}\nName: {name}\nPhone: {phone}\nAddress: {address}\nDescription: {descrip}\nLink to post: {link_to_open}'
            
            telegram_bot(requests,img_link,http_api,chat_id,message)
            

        
        

