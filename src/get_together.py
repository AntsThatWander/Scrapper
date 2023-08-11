from parse import WebCrawling
import json

tags = ['#title_area > span', 
        '#dic_area', 
        '#ct > div.media_end_head.go_trans > div.media_end_head_info.nv_notrans > div.media_end_head_info_datestamp > div:nth-child(1) > span']

with open('./naver_news.json', 'r') as f:
    _urls = json.load(f)

urls = []


for url in _urls:
    urls.append(list(url.values())[0])

wc = WebCrawling(urls, tags)

with open('./result.txt', 'w') as f:
    for item in wc.run():
        f.write("%s\n" % item[1])