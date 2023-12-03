from selenium import webdriver
from time import sleep
from selenium import webdriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from time import sleep

sleep(5)

browser = webdriver.Remote("http://localhost:4444", options=webdriver.ChromeOptions())
# browser = webdriver.Remote("http://selenium:4444/wd/hub", DesiredCapabilities.CHROME)

try:
    browser.get("https://medium.com")
    sleep(5)
finally:
    browser.quit()
