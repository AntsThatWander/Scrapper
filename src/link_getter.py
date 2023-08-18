from bs4 import BeautifulSoup
import requests
import pandas as pd
import json
import datetime as dt
import time
from typing import List
from typing import Optional
from urllib.error import HTTPError
from urllib.error import URLError
import random
from random_user_agent.user_agent import UserAgent
from random_user_agent.params import SoftwareName, OperatingSystem

class NoDataException(Exception):
    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return self.msg

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
        self._json = []
        self.total_cnt = 0

    #If you meet an error while crawling, you can get json.
    def get_json(self) :
        return self._json
    
    def init_json(self, json : List[str], total_cnt : int):
        self._json = json
        self.total_cnt = total_cnt

    def get_link(self, file_name : str, 
                        data_prsv_flag : bool,
                        data : Optional[List[str]] = None, 
                        url : Optional[str] = None,
                        selector : Optional[str] = None,
                        start_date : Optional[dt.date] = None,
                        end_date : Optional[dt.date] = None,
                        repeat  : Optional[int] = None):
        _repeat = 400 if repeat is None else repeat if repeat <= 400 else 400
        _data = self.data_src if data is None else data
        _cur_date = start_date if start_date is not None else dt.date.today()
        _end_date = dt.date(_cur_date.year, _cur_date.month-1, _cur_date.day-1) if end_date is None else dt.date(end_date.year, end_date.month, end_date.day)
        base_url = url if url is not None else link_getter.site.get('naver').get('url')
        _selector = selector if selector is not None else link_getter.site.get('naver').get('selector')
        self._from_json(file_name, data_prsv_flag)
        
        for key in _data:
            print(f"{key} started") #print log. Erase it if you don't want any log
            self._get_dict(base_url, key, _cur_date, _end_date, _repeat, _selector, file_name)
            print(f"{key} ended") #print log. Erase it if you don't want any log
                
        self._to_json(file_name = file_name, json_file = self._json)
    

    def _get_dict(self, base_url, key, _cur_date, _end_date, _repeat, _selector, file_name) :
        while(_cur_date != _end_date) :
                prev_date = _cur_date - dt.timedelta(days = 1)
                for page_num in range(_repeat):
                    cur_url =  self._get_url(base_url, key, page_num, '&sort=1', '&pd=3', f'&ds={_cur_date.strftime("%Y.%m.%d")}', f'&de={_cur_date.strftime("%Y.%m.%d")}')
                    try : # Need exception handling improvement. 
                        software_names = [SoftwareName.CHROME.value]
                        operating_systems = [OperatingSystem.WINDOWS.value, OperatingSystem.LINUX.value]   

                        user_agent_rotator = UserAgent(software_names=software_names, operating_systems=operating_systems, limit=100)

                        # Get Random User Agent String.
                        user_agent = user_agent_rotator.get_random_user_agent()
                        
                        html = requests.get(cur_url, headers = {'User-Agent' : user_agent})
                        soup = BeautifulSoup(html.text, 'html.parser')
                        print(cur_url) #print log. Erase it if you don't want any log
                        self._get_page_data(soup, _selector)
                    except HTTPError as hp:
                        print('wrong http file')
                        print(hp)
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
                    time.sleep(0.5)
                self._to_json(file_name, self._json)
                _cur_date = prev_date
    
    def _get_page_data(self, soup, selector) :
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
            self._json.append(dictionary)
        
    def _get_url(self, url : str, key : str, page_num : int, *args : str) :
        params = ''
        for idx, arg in enumerate(args):
            params += arg
        return url + key + "&start=" + str(page_num * 10 + 1) + params
    

    def _to_json(self, file_name : str, json_file : List[str]) :
        try:
            with open(file_name, 'w') as f:
                json.dump(json_file, f, ensure_ascii=False, indent=4)
        except IOError as IOex:
            print('error with opening', + str(file_name))
            print(IOex)
    
    def _from_json(self, file_name : str, data_prsv_flag : bool) :
        if data_prsv_flag :
            try : 
                with open(file_name, "r") as fd :
                    _json = json.load(fd)
                    total_cnt = int(list(_json[len(_json) - 1].keys())[0])
                    self.init_json(_json, total_cnt)
            except IOError as fn :
                print('No file found. Default Value Set.')
                self.init_json([], 0)
        else :
            self.init_json([], 0)


lg = link_getter()
#lg.get_link('hmm.json', data = ['하나머트리얼즈', '하니웰스페셜티머터리얼스코리아(주)'])
lg._from_json('hmm.json', True)