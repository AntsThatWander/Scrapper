from bs4 import BeautifulSoup
import requests
import pandas as pd
import time
import json

class link_getter :
    def __init__(self):
        self.data = pd.read_excel("risk_dictionary.xlsx", sheet_name="1. 반도체 공급망 RISK 키워드 POOL")
        self.base_url = "https://search.naver.com/search.naver?where=news&query="
        self.sort = "&sort=1"
        # self.column_list = ['주요 업체', '주요 원자재', '파운드리 기업', '반도체 기업', '기타 관련 기업', '반도체 소재 업체', '반도체 웨이퍼 업체', '반도체 장비 업체', '기구 및 협회', '반도체 공통용어', '반도체 기술 용어', '반도체 생태계 용어', '반도체 공정 용어', '반도체 소재']
        self.data_col_list = ['반도체 공통용어']

    def get_link_by_naver(self):
        _json = []
        for data_column in self.data_col_list:
            data_rows = self.data[data_column].dropna(axis = 0).tolist()
            for key in data_rows:
                url = self.base_url + key + self.sort + self.get_start(0)
                html = requests.get(url)
                soup = BeautifulSoup(html.text, 'html.parser')
                
                print(f"keyword : {key}\n")
                #print(url)
                for elem in soup.select('#main_pack > section > div > div.group_news > ul > li > div > div > a'):
                    link = elem['href']
                    dictionary = {'col_nm' : data_column, 'key_nm' : key, 'link' : link}
                    _json.append(dictionary)
                print(f"{key} end\n")
                time.sleep(0.5)

        with open('./test.json','w') as f:
            json.dump(_json, f, ensure_ascii=False, indent=4)


    def get_link_by_naver_news(self):
        _json = []
        total_cnt = 0
        for data_column in self.data_col_list:
            data_rows = self.data[data_column].dropna(axis = 0).tolist()
            for key in data_rows:

                for i in range(7):
                    url = self.base_url + key + self.sort + self.get_start(i)
                    html = requests.get(url)
                    soup = BeautifulSoup(html.text, 'html.parser')
                    print(url)
                
                    for elem in soup.select('#main_pack > section > div > div.group_news > ul > li > div > div > div.news_info > div.info_group > a.info'):
                        if(len(elem['class']) > 1) :
                            continue
                        total_cnt += 1
                        link = elem['href']
                        dictionary = {f"{total_cnt}" :  link}
                        _json.append(dictionary)
                    
                    time.sleep(0.5)
            
        with open('./naver_news.json','w') as f:
            json.dump(_json, f, ensure_ascii=False, indent=4)

    
    def get_link_for_test(self):
        column = self.data_col_list[0]
        rows = self.data[column].dropna(axis = 0).tolist()

        key = rows[0]
        print(key)
        url = self.base_url + key + self.sort + self.get_start(0)
        html = requests.get(url)
        soup = BeautifulSoup(html.text, 'html.parser')

        cnt = 0
        for elem in soup.select('#main_pack > section > div > div.group_news > ul > li > div > div'):
            print(f"{cnt+1} : {elem.select('a.news_tit')}\n")
            print(f"{cnt+1}-1 : {elem.select('div > div.info_group > a')}\n")
            cnt += 1
    

        
    
    def get_start(self, cnt) :
        return "&start=" + str(cnt * 10 + 1)
            
            

    
    # def search(self, key):
    #     pass

lg = link_getter()
lg.get_link_by_naver_news()