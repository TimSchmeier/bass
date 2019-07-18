import scrapy
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import re
import json
from bs4 import BeautifulSoup
import time


class AnglerSpider(scrapy.Spider):
    name = 'anglers'

    # All anglers
    start_urls = [
        'https://www.bassmaster.com/anglers-page?section=latest&page={}'.format(x)
            for x in range(540, 699)
        ]

    def __init__(self):
        self.driver = webdriver.Firefox()
        # wait for slow website loads
        self.driver.implicitly_wait(120)

    def get_table(self, page):
        self.driver.get(page)
        # wait for js table to load on each page
        table = WebDriverWait(self.driver, 120).until(
                EC.visibility_of_all_elements_located((By.CSS_SELECTOR, "td")))
        # bs is faster than selenium
        soup = BeautifulSoup(self.driver.page_source, 'lxml')
        return soup.find('tbody')

    def parse_angler(self, response):
        name = response.url.rsplit('/', 1)[1]
        page = response.url
        table = self.get_table(page)

        for row in table.find_all('tr'):
            tourney = row.find('td', class_='tournament')
            tournament_name = tourney.get_text()
            tournament_link = tourney.find('a').get('href')
            place = row.find('td', class_='place').get_text()
            weight = row.find('td', class_='total_weight').get_text()
            money = row.find('td', class_='total_money').get_text()

            # Handle getting skunked
            if weight == '0':
                weight = ['0lb', '0oz']
            else:
                weight = weight.split(" - ")

            cash = re.sub("[\$,]", "", money)

            retval = {
            "angler": name,
            "tournament": tournament_name,
            "tournament_link": tournament_link,
            "place": place,
            "oz": (int(weight[0].strip("lb")) * 16) + int(weight[1].strip("oz")),
            "winnings": float(cash),
            }
            yield retval

    def parse(self, response):
        anglers = response.css('span.field-content a')
        for angler in anglers:
            name = angler.xpath('text()').get()
            path = 'stats' + angler.xpath('@href').get()
            yield response.follow(path, callback=self.parse_angler)
