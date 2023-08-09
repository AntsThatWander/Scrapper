from typing import List
from bs4 import BeautifulSoup
import requests

class WebCrawling:
    def __init__(self, urls: List[str], tags: List[str]):
        self._urls = urls
        self._tags = tags
        self._header = ({'User-Agent':
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 \
            (KHTML, like Gecko) Chrome/44.0.2403.157 Safari/537.36',\
            'Accept-Language': 'en-US, en;q=0.5'})
        self._data = list()

    def run(self):
        try:
            if len(self._tags) != 3:
                raise Exception('The number of tags must be 3')
            self._runEach()
            return self._data
        except Exception as e:
            print(e)
            return None

    def _runEach(self):
        data = list()
        for url in self._urls:
            data.append(self._getData(url))
        self._data = data

    def _getData(self, url):
        data = list()
        try:
            response = requests.get(url, headers=self._header)
            if response.status_code != 200:
                raise Exception('The status code is not 200')
            soup = BeautifulSoup(response.text, 'html.parser')
            title, content, date = self._tags
            data.append(self._extractData(soup, title))
            data.append(self._extractContent(soup, content))
            data.append(self._extractData(soup, date))
            return data
        except Exception as e:
            print('Error occured while getting data\n{0}'.format(e))
            return None

    def _extractData(self, soup, tag):
        return soup.select(tag)[0].text

    def _extractContent(self, soup, tag):
        content = list()
        data = soup.select(tag)
        for text in data:
            content.append(text.text)
        return content
