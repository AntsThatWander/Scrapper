from bs4 import BeautifulSoup
import requests
import pandas as pd
import json
import datetime as dt
import time
import random
from typing import List
from typing import Optional
from urllib.error import HTTPError, URLError
from urllib.request import ProxyHandler, build_opener, install_opener, Request, urlopen
from urllib.parse import quote
from random_user_agent.user_agent import UserAgent
from random_user_agent.params import SoftwareName, OperatingSystem


class NoDataException(Exception):
    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return self.msg
    
class Handler:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.0.7) Gecko/2009021910 Firefox/3.0.7'}

    def open_url(self, url : str):
        def _get_user_agent() :
            software_names = [SoftwareName.CHROME.value]
            operating_systems = [OperatingSystem.WINDOWS.value, OperatingSystem.LINUX.value]   
            user_agent_rotator = UserAgent(software_names=software_names, operating_systems=operating_systems, limit=100)
            # Get Random User Agent String.
            user_agent = user_agent_rotator.get_random_user_agent()
            self.headers['User-Agent'] = user_agent

        _get_user_agent()
        request = Request(url, None, self.headers)
        return urlopen(request).read().decode('utf-8')
    
    def get_new_ip(self, wait_time):
        pass

    
    @staticmethod
    def renew_connection():
        with Controller.from_port(port=9051) as controller:
            controller.authenticate(password='btt')
            controller.signal(Signal.NEWNYM)
            controller.close()

class link_getter :
    # selectors per site to get links. Choose one where you want to get links.
    site = {
        'naver' : {
            'url' : "https://search.naver.com/search.naver?where=news&query=",
            'selector' : "#main_pack > section > div > div.group_news > ul > li > div > div > div.news_info > div.info_group > a.info"
        }
    }

    def __init__(self, excel_name = "word_list.csv"):
        self.data_src = pd.read_csv(excel_name)['word'].tolist()
        self.output_data = []
        self.total_cnt = 0
        self.tor_handler = Handler()

    #If you meet an error while crawling, you can get json.
    def get_json(self) :
        return self.output_data
    
    def init_json(self, output_data : List[str], total_cnt : int) -> List[dict]:
        self.output_data = output_data
        self.total_cnt = total_cnt

    def link_to_json(self, file_name : str, 
                        data_prsv_flag : bool,
                        input_data : Optional[List[str]] = None, 
                        base_url : Optional[str] = None,
                        selector : Optional[str] = None,
                        start_date : Optional[dt.date] = None,
                        end_date : Optional[dt.date] = None,
                        total_page  : Optional[int] = None):
        
        #init data for the function.
        self._data_from_json(file_name, data_prsv_flag)
        _total_page = 400 if total_page is None else total_page if total_page <= 400 else 400
        _input_data = self.data_src if input_data is None else input_data
        _start_date = start_date if start_date is not None else dt.date.today()
        _end_date = dt.date(_start_date.year, _start_date.month-1, _start_date.day-1) if end_date is None else dt.date(end_date.year, end_date.month, end_date.day-1)
        
        _base_url = base_url if base_url is not None else link_getter.site.get('naver').get('url')
        _selector = selector if selector is not None else link_getter.site.get('naver').get('selector')

        for key in _input_data:
            print(f"{key} started") #print log. Erase it if you don't want any log
            self._trip_per_date(key, _base_url, _start_date, _end_date, _total_page, _selector, file_name)
            print(f"{key} ended") #print log. Erase it if you don't want any log
         
        return self.output_data
    

    def _trip_per_date(self, key, _base_url, _start_date, _end_date, _total_page, _selector, file_name) :
        cur_date = _start_date
        while(cur_date != _end_date) :
                prev_date = cur_date - dt.timedelta(days = 1)
                for page in range(_total_page):
                    try : 
                        time.sleep(random.randrange(35, 55) / 100)
                        cur_url =  self._create_url(_base_url, key, page, '&sort=1', '&pd=3', f'&ds={cur_date.strftime("%Y.%m.%d")}', f'&de={cur_date.strftime("%Y.%m.%d")}') 
                        html = self.tor_handler.open_url(cur_url)
                        soup = BeautifulSoup(html, 'html.parser')
                        print(cur_url) #print log. Erase it if you don't want any log
                        self._put_link_from_page_to_list(soup, _selector)
                    except HTTPError as hp:
                        print(hp)
                        if hp.__str__() == 'HTTP Error 403: Forbidden' :
                            print("You're currently blocked")
                            raise hp
                        return None
                    except URLError as ue:
                        print('wrong url')
                        print(ue)
                        return None
                    except NoDataException as nd:
                        print(nd)
                        break
                    except Exception as ex:
                        print('error during html request & parsing')
                        print(ex)
                        return None
                    
                self._data_to_json(file_name)
                cur_date = prev_date
    
    def _put_link_from_page_to_list(self, soup, selector) :
        selected = soup.select(selector)
        if len(selected) == 0 :
            raise NoDataException('No more data found in this day')
        for elem in selected:
            # to get rid of class = 'info press'
            if len(elem['class']) > 1 :
                continue
            self.total_cnt += 1
            link = elem['href']
            dictionary = {f'{self.total_cnt}' : link}
            self.output_data.append(dictionary)
        
    def _create_url(self, url : str, key : str, page_num : int, *args : str) :
        params = ''
        for idx, arg in enumerate(args):
            params += arg
        return url + quote(key) + "&start=" + str(page_num * 10 + 1) + params
    

    def _data_to_json(self, file_name : str) :
        try:
            with open(file_name, 'w') as f:
                json.dump(self.output_data, f, ensure_ascii=False, indent=4)
        except IOError as IOex:
            print('error with opening', + str(file_name))
            print(IOex)
    
    def _data_from_json(self, file_name : str, data_prsv_flag : bool) :
        if data_prsv_flag :
            try : 
                with open(file_name, "r") as fd :
                    _json = json.load(fd)
                    if(len(_json) == 0) :
                        raise NoDataException('This json file is empty.')
                    total_cnt = int(list(_json[len(_json) - 1].keys())[0])
                    self.init_json(_json, total_cnt)
            except IOError as fn :
                print(fn)
                print('No file found. Use Default Dataset.')
            except NoDataException as fn :
                print(fn)
                print('No data found in the file. Use Default Dataset.')
            finally :
                self.init_json([], 0)
        else :
            self.init_json([], 0)


lg = link_getter()
lg.link_to_json('to_Jinwoongdd.json', False)
