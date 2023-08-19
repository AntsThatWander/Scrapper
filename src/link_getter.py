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
from stem import Signal
from stem.control import Controller

class NoDataException(Exception):
    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return self.msg
    
class TorHandler:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.0.7) Gecko/2009021910 Firefox/3.0.7'}

    def open_url(self, url : str):
        def _set_url_proxy():
            proxy_support = ProxyHandler({'http': '127.0.0.1:8118'})
            opener = build_opener(proxy_support)
            install_opener(opener)

        def _get_user_agent() :
            software_names = [SoftwareName.CHROME.value]
            operating_systems = [OperatingSystem.WINDOWS.value, OperatingSystem.LINUX.value, OperatingSystem.MAC_OS_X.value, OperatingSystem.MAC.value, OperatingSystem.UNIX.value]   
            user_agent_rotator = UserAgent(software_names=software_names, operating_systems=operating_systems, limit=100)
            # Get Random User Agent String.
            user_agent = user_agent_rotator.get_random_user_agent()
            self.headers['User-Agent'] = user_agent

        _set_url_proxy()
        _get_user_agent()
        request = Request(url, None, self.headers)
        return urlopen(request).read().decode('utf-8')
    
    def get_cur_ip(self) :
        return self.open_url('http://icanhazip.com/')
    
    def get_new_ip(self, wait_time : int) -> str:
        ip = self.get_cur_ip()
        old_ip = ip
        self.renew_connection()
        while ip == old_ip:
            time.sleep(wait_time)
            ip = self.get_cur_ip() 
        return ip.strip()
    
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
        self.internal_data = []
        self.output_data = []
        self.output_data_content = []
        self.total_cnt = 0
        self.tor_handler = TorHandler()

    #If you meet an error while crawling, you can get json.
    def get_json(self) :
        return self.output_data
    
    def init_json(self, output_data : List[str], total_cnt : int) -> List[dict]:
        self.output_data = output_data
        self.total_cnt = total_cnt
    
    def link_to_json(self, file_name : str, 
                        data_prsv_flag : bool,
                        input_data : Optional[List[str]] = None,
                        start_keyword : Optional[str] = None,
                        base_url : Optional[str] = None,
                        selector : Optional[str] = None,
                        start_date : Optional[dt.date] = None,
                        end_date : Optional[dt.date] = None,
                        toal_page_num  : Optional[int] = None):
        
        #init data for the function.
        self._data_from_json(file_name, data_prsv_flag)
        self._get_data_content()
        _toal_page_num = 400 if toal_page_num is None else toal_page_num if toal_page_num <= 400 else 400
        _input_data = self.data_src if input_data is None else input_data
        if start_keyword is not None :
            _input_data = self._slice_data_from_keyword(_input_data, start_keyword)

        _start_date = start_date if start_date is not None else dt.date.today()
        _end_date = dt.date(_start_date.year, _start_date.month-1, _start_date.day-1) if end_date is None else dt.date(end_date.year, end_date.month, end_date.day-1)
        
        _base_url = base_url if base_url is not None else link_getter.site.get('naver').get('url')
        _selector = selector if selector is not None else link_getter.site.get('naver').get('selector')

        for key in _input_data:
            print(f"{key} started") #print log. Erase it if you don't want any log
            self.tor_handler.get_new_ip(2)
            self._trip_per_date(key, _base_url, _start_date, _end_date, _toal_page_num, _selector, file_name)
            print(f"{key} ended") #print log. Erase it if you don't want any log
         
        return self.output_data
    

    def _trip_per_date(self, key, _base_url, _start_date, _end_date, _toal_page_num, _selector, file_name) :
        cur_date = _start_date
        date_cnt = 0
        page_cnt = 0
        while(cur_date != _end_date) :
                prev_date = cur_date - dt.timedelta(days = 1)
                date_cnt += 1
                for page in range(_toal_page_num):
                    page_cnt += 1
                    try : 
                        time.sleep(random.randrange(200,601) / 1000 * 0.47 + random.randrange(200,601) / 1000 * 0.53)
                        url =  self._create_url(_base_url, key, page, 
                                                    '&sort=1', '&pd=3', 
                                                    f'&ds={cur_date.strftime("%Y.%m.%d")}', 
                                                    f'&de={cur_date.strftime("%Y.%m.%d")}') 
                        html = self.tor_handler.open_url(url)
                        soup = BeautifulSoup(html, 'html.parser')
                        print(f'Your current ip : {self.tor_handler.get_cur_ip().strip()}')
                        print(url) #print log. Erase it if you don't want any log

                        if date_cnt >= random.randrange(5, 8) or page_cnt >= random.randrange(10, 16) :
                            print("Random IP change")
                            print(f'Your new ip : {self.tor_handler.get_new_ip(2)}')
                            
                            date_cnt = 0
                            page_cnt = 0
                
                        self._put_link_from_page_to_list(soup.select(_selector))
                        
                    except HTTPError as hp:
                        print(hp)
                        if hp.__str__() == 'HTTP Error 403: Forbidden' :
                            while True :
                                try : 
                                    print("You're currently blocked")
                                    print(f'Your new ip : {self.tor_handler.get_new_ip(2)}')
                                    print(f'In error, your url : {url}')
                                    time.sleep(random.randrange(250,551) / 98 * 0.45 + random.randrange(280,521) / 102 * 0.55)
                                    html = self.tor_handler.open_url(url)
                                    soup = BeautifulSoup(html, 'html.parser')
                                    self._put_link_from_page_to_list(soup.select(_selector))
                                    break
                                except Exception as e:
                                    print(f'error during blocked status : {e}')
                                    if e.__str__() == 'HTTP Error 403: Forbidden' :
                                        print('Still blocked')
                                        continue
                                    else :
                                        break
                            break
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

    
    def _put_link_from_page_to_list(self, selected) :
        if len(selected) == 0 :
            raise NoDataException('No more data found in this day')
        for elem in selected:
            # to get rid of class = 'info press'
            if len(elem['class']) > 1 :
                continue
            link = elem['href']
            if link in self.output_data_content :
                continue
            self.output_data_content.append(link)
            self.total_cnt += 1
            dictionary = {f'{self.total_cnt}' : link}
            self.output_data.append(dictionary)
            
        
    def _create_url(self, url : str, key : str, page_num : int, *args : str) :
        params = ''
        for idx, arg in enumerate(args):
            params += arg
        return url + quote(key) + "&start=" + str(page_num * 10 + 1) + params
    
    def _slice_data_from_keyword(self, data, keyword) :
        cnt = 0
        _data = []
        for _keyword in data :
            if _keyword == keyword :
                _data = data[cnt:]
                return _data
            cnt += 1
        print("The keyword you set doesn't exist")

    def _get_data_content(self) :
        if(len(self.output_data) == 0) :
            return None
        for _dict in self.output_data :
            self.output_data_content.append(list(_dict.values())[0])
    

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
                self.init_json([], 0)
            except NoDataException as fn :
                print(fn)
                print('No data found in the file. Use Default Dataset.')
                self.init_json([], 0)
        else :
            self.init_json([], 0)


lg = link_getter()
lg.link_to_json('data_crawling.json', True, start_keyword = '버슘머트리얼즈에스피씨코리아(유한)')
