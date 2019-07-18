import scrapy
import pandas as pd
import os
import requests
from bs4 import BeautifulSoup


class TournamentSpider(scrapy.Spider):
    name = 'tournaments'
    url = "https://maps.googleapis.com/maps/api/geocode/json?address={}&key={}"

    # All found tournaments
    start_urls = pd.read_csv("angler_data.csv")["tournament_link"].dropna().unique().tolist()

    def __init__(self):
        self.apikey = os.environ['apikey']

    def parse(self, response):

        soup = BeautifulSoup(response.body, 'lxml')
        tourney = soup.find("h1").string
        datestring = soup.find(
            "div",
            class_="date-display-range") \
                .text.replace(",", "").split(" ")

        if len(datestring) == 5:
            startmonth, startday, _, finishday, year = datestring
            finishmonth = startmonth
        # One day tournaments
        elif len(datestring) == 3:
            startmonth, startday, year = datestring
            finishday = startday
            finishmonth = startmonth
        # Tournaments that stradle a month
        elif len(datestring) == 6:
            startmonth, startday, _, finishmonth, finishday, year = datestring

        location = soup.find(
            "div",
            class_="field field-name-field-body-of-water field-type-text field-label-hidden") \
                .text.split(",")[0].lower()

        city = soup.find(
            "div",
            class_="field field-name-field-city field-type-text field-label-hidden") \
                .text.split(",")[0].lower()

        state = soup.find(
            "div",
            class_="field field-name-field-state field-type-list-text field-label-hidden") \
                .text.lower()

        # request to geocode
        r = requests.get(
            self.url.format(",".join([city, state]), self.apikey)
            )


        # check response status
        if not r.status_code == 200:
            lat = "None"
            lon = "None"

        else:
            latlon = r.json()["results"][0]['geometry']['location']
            lat = latlon['lat']
            lon = latlon['lng']


        ret = {
               "location": location,
               "city": city,
               "state": state,
               "startmonth": startmonth,
               "finishmonth": finishmonth,
               "startdate": startday,
               "finishdate": finishday,
               "year": year,
               "lat": lat,
               "lon": lon,
               "tournament_link": response.url
               }

        yield ret
