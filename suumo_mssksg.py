import lxml.html
import time
import requests
import math
import datetime
import re
import os
import sys
import csv
import pandas as pd
import urllib
from urllib.parse import urljoin
import urllib3
from bs4 import BeautifulSoup
import random
import logging 
urllib3.disable_warnings()

logging.basicConfig(filename='suumo_mssksg.log', level=logging.INFO)

# __name__はこのモジュールの名前
logger = logging.getLogger(__name__)

# logger.info('start program')

headers = {
    # 'Host': str(parse[1]),
    # 'DNT': '1',
    'Upgrade-Insecure-Requests': '1',
    'Accept-Language': 'ja,en-US;q=0.8,en;q=0.6',
    'Accept-Encoding': 'gzip, deflate, br',
    'Cache-Control': 'max-age=0',
    # 'If-None-Match': "38571fc0eaef091808382b438be97054",
    # 'If-Modified-Since': 'Thu, 08 Dec 2016 06:52:51 GMT',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
    'User-Agent': 'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx',
}


# logger.info('session start') # セッションの確認

s = requests.Session()
s.verify = False
s.headers.update(headers)
s.mount('http://', requests.adapters.HTTPAdapter(max_retries=10))
s.mount('https://', requests.adapters.HTTPAdapter(max_retries=10))

# logger.info('session mounted')

def get_urls(url):
    urls = []

    res = s.get(url, allow_redirects=True)
    res.raise_for_status()

    dom = lxml.html.fromstring(res.text)
    
    #<td class="ui-text--midium ui-text--bold">
    ##<a href="/chintai/jnc_000042098882/" target="_blank" 
    ##onclick="sendBeaconSiteCatalystClick(event,this,'click_casset_bkn_link',false);">詳細を見る</a>
    #</td>
    

    for a in dom.xpath('//td[@class="ui-text--midium ui-text--bold"]/a[contains(text(), "詳細を見る")]'):
        if urljoin(BASE_URL, a.get('href')) not in urls:
            urls.append(urljoin(BASE_URL, a.get('href')))
 
    return urls


def get_next_page(url):
    res = s.get(url, allow_redirects=True)
    res.raise_for_status()

    dom = lxml.html.fromstring(res.text)

    # <p class="pagination-parts">
    # # <a href="/jj/bukken/ichiran/JJ012FC001/?jj012fi20202Kbn=6&amp;initKbn=1&amp;displayClass=dn&amp;disabledClass=false&amp;ar=060&amp;bs=011&amp;ra=060027&amp;rn=2025&amp;rnTemp=2025&amp;ekTemp=202541150&amp;ekTjCd=&amp;ekTjNm=&amp;tj=0&amp;cnb=0&amp;cn=9999999&amp;rnek=202541150&amp;kb=1&amp;kt=9999999&amp;mb=0&amp;mt=9999999&amp;et=10&amp;et=10&amp;fw2=&amp;pn=2">次へ</a></p>
    #p_tag = soup.find('p', class_="pagination-parts")
    #import pdb; pdb.set_trace()
    for a in dom.xpath('//p[@class="pagination-parts"]/a[contains(text(), "次へ")]'):
        n_url = urljoin(BASE_URL, a.get('href'))

    return n_url


def scrape(url, scrape_number):
    """
    title
    address
    structure
    stroy
    layout
    price/tsubo
    total_price/10000
    floor
    tsubo
    x_min
    year
    
    property_price/10000
    mng_fee/10000
    
    x-n1
    x-n2
    x-n3
    
    year_memo
    access_x
    access_n1
    n1_min
    access_n2
    n2_min
    access_n3
    n3_min

    date
    datetime
    url

    """

    res = s.get(url, allow_redirects=True)
    # import pdb; pdb.set_trace()
    # logger.info(res)
    res.raise_for_status()

    dom = lxml.html.fromstring(res.text)
    # import pdb; pdb.set_trace()
    # logger.info(dom)

    response = s.get(url, allow_redirects=True)
    content = response.content
    # BeautifulSoup に content を渡して解析の準備をする
    soup = BeautifulSoup(content, 'html.parser')
    # logger.info(soup.prettify())

    data = {}
    notFound = []

    # 初期化
    for r in [

        'No.','title', 'address', 'structure', 'story', 'layout', 'price/tsubo', 'total_price/JPY', 'floor', 'tsubo', 'x_min', 'year', \
        'property_price/JPY', 'mng_fee/JPY', 'x_n1', 'x_n2', 'x_n3', 'floor_memo', 'year_memo', 'access_x', \
        'access_n1', 'n1_min', 'access_n2', 'n2_min', 'access_n3', 'n3_min', 'date', 'datetime', 'url'
        ]:
        
        data[r] = None
    # No.
    data['No.'] = scrape_number
    # date
    data['date'] = datetime.datetime.now().strftime('%Y-%m-%d')
    if len(notFound)!=0:
        pass

    # datetime
    data['datetime'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    if len(notFound)!=0:
        pass

    # url
    data['url'] = url 


    # title
    try:
        # //*[@id="wrapper"]/div[3]/div[1]/h1
        tmp = dom.xpath('//h1')[0].text
        data['title'] = tmp.strip('\r\n\t\t\t\t\t\t\t')
    except Exception:
        notFound.append('title')
    print('【title】', data['title'])
    
    # property_price/JPY
    #import pdb; pdb.set_trace()
    try:
        m = re.search(r'([0-9].*万円)', str(soup))[0]
        # 8.23万円
        if m:
            tmp = m.rstrip('万円')
            data['property_price/JPY'] = float(tmp) * 10000
        else:
            data['property_price/JPY'] = tm
    except Exception:
        notFound.append('property_price/JPY')
    print('【property_price/JPY】', data['property_price/JPY'])

    # mng_fee/JPY
    #'<span>管理費・共益費:\xa011000円</span>'
    #import pdb; pdb.set_trace()
    try:
        m = re.search(r'(.*管理費.*)', str(soup))[0]
        if m:
            m_n1 = re.search(r'([1-9][0-9]*円)', m)[0]
            m_n2 = m_n1.rstrip('円')
            data['mng_fee/JPY'] = int(m_n2)
        else:
            data['mng_fee/JPY'] = 0
    except Exception:
        data['mng_fee/JPY'] = 0
    print('【mng_fee/JPY】', data['mng_fee/JPY'])

    # total_price/JPY
    try:
        data['total_price/JPY'] = data['property_price/JPY'] + data['mng_fee/JPY'] 
    except:
        try:
            data['total_price/JPY'] = data['property_price/JPY']
        except:
            notFound.append('total_price/JPY')
    print('【total_price/JPY】', data['total_price/JPY'])


    # layout
    #import pdb; pdb.set_trace()
    time.sleep(random.randint(3,8))
    while True:
        try:
            #<div class="property_data-title">間取り</div>
            #<div class="property_data-body">1DK</div>
            tmp = dom.xpath('//div[contains(text(), "間取り")]/following-sibling::div[@class="property_data-body"]')[0].text
            try:
                data['layout'] = tmp.lstrip('\r\n\t\t\t\t\t\t\t\t\t\t\t')
            except:
                continue
            else:
                break
                data['layout'] = tmp
        except Exception:
            notFound.append('layout')
    print('【layout】', data['layout'])


    # tsubo 
    # price/tsubo
    try:
        tmp = dom.xpath('//div[contains(text(), "専有面積")]/following-sibling::div[@class="property_data-body"]')[0].text
        #
        try:
            _tmp = tmp.lstrip('\r\n\t\t\t\t\t\t\t\t\t\t\t').rstrip('m')
            # 31.5m
            tsubo = float(_tmp) * 0.3025
            data['tsubo'] = round(tsubo, 2)
            try:
                unit_price = round(data['total_price/JPY'] / data['tsubo'], 2)
                data['price/tsubo'] = float(unit_price)
            except Exception:
                notFound.append('price/tsubo')
        except:
            data['tsubo'] = tmp
        
    except Exception:
        notFound.append('tsubo')
    print('【tsubo】', data['tsubo'])
    print('【price/tsubo】', data['price/tsubo'])


    # year
    # https://qiita.com/wonder_zone/items/a15ee2760a1d9e796b67
    #import datetime
    try:
        # 2006年1月
        # <th class="data_02" scope="cols">築年月</th>
        # <td>2017年1月</td>
        #import pdb; pdb.set_trace()
        tmp = dom.xpath('//th[contains(text(), "築年月")]/following-sibling::td')[0].text
        data['year_memo'] = tmp
        try:
            y_tmp = re.search('\d*年', tmp)[0]
            if y_tmp:
                _y_tmp = y_tmp.rstrip('年')
                y = int(_y_tmp)
                m_tmp = re.search('\d*月', tmp)[0]
                if m_tmp:
                    _m_tmp = m_tmp.rstrip('月')
                    m = int(_m_tmp)
                    start_time = datetime.date(y, m, 1)
                    end_time = datetime.date(2018, 8, 1)
                    term = (end_time-start_time).days
                    _term = float(term) / 365
                    data['year'] = round(_term, 2)
                else:
                    start_time = datetime.date(y, 1, 1)
                    end_time = datetime.date(2018, 7, 1)
                    term = (end_time-start_time).days
                    _term = float(term) / 365
                    data['year'] = round(_term, 2)
        except:
            data['year'] = _tmp
    except Exception:
        notFound.append('year_memo')
    print('【year_memo】', data['year_memo'])
    print('【year】', data['year'])
   

    # access_n1
    # n1_min
    try:
        tmp = dom.xpath('//*[@id="js-view_gallery"]/div[1]/div[2]/div[3]/div[2]/div[1]/div/div[2]/div[1]')[0].text
        data['access_n1'] = tmp
        m = re.search('\d*分', tmp)[0]
        if m:
            n1_time = m.rstrip('分')
            data['n1_min'] = int(n1_time)
        else:
            notFound.append('n1_min')
    except Exception:
        notFound.append('access_n1')
    print('【access_n1】', data['access_n1'])
    print('【n1_min】', data['n1_min'])

    # access_n2
    # n2_min
    try:
        tmp = dom.xpath('//*[@id="js-view_gallery"]/div[1]/div[2]/div[3]/div[2]/div[1]/div/div[2]/div[2]')[0].text
        data['access_n2'] = tmp
        m = re.search('\d*分', tmp)[0]
        if m:
            n2_time = m.rstrip('分')
            data['n2_min'] = int(n2_time)
        else:
            notFound.append('n2_min')
    except Exception:
        notFound.append('access_n2')
        notFound.append('n2_min')
    print('【access_n2】', data['access_n2'])
    print('【n2_min】', data['n2_min'])
    
    # access_n3
    # n3_min
    try:
        tmp = dom.xpath('//*[@id="js-view_gallery"]/div[1]/div[2]/div[3]/div[2]/div[1]/div/div[2]/div[3]')[0].text
        data['access_n3'] = tmp
        m = re.search('\d*分', tmp)[0]
        if m:
            n3_time = m.rstrip('分')
            data['n3_min'] = int(n3_time)
        else:
            notFound.append('n3_min')
    except Exception:
        notFound.append('access_n3')
    print('【access_n3】', data['access_n3'])
    print('【n3_min】', data['n3_min'])

    # access_x
    try:
        tmp = dom.xpath('//div[@class="property_view_detail property_view_detail--train"]\
        //div[contains(@class,"property_view_detail-text") and contains(text(), "東急東横線/武蔵小杉駅")]')[0].text
        data['access_x'] = tmp
        print('【access_x】', data['access_x'])
        m = re.search('\d*分', tmp)[0]
        if m:
            x_time = m.rstrip('分')
            data['x_min'] = int(x_time)
            print('【x_min】', data['x_min'])
        else:
            notFound.append('x_min')
    except Exception:
        notFound.append('x_min')
    
    # x_n1
    try:
        #import pdb; pdb.set_trace()
        gap_n1 = data['x_min'] - data['n1_min'] 
        if gap_n1 <= 0:
            data['x_n1'] = '✔'
            print('【x_n1】', data['x_n1'])
        else:
            data['x_n1'] = 'n1 is closer than x'
            print('【x_n1】', data['x_n1'])
    except:
        notFound.append('x_n1')
    # x_n2
    try:
        gap_n2 = data['x_min'] - data['n2_min'] 
        if gap_n2 <= 0:
            data['x_n2'] = '✔'
            print('【x_n2】', data['x_n2'])
        else:
            data['x_n2'] = 'n2 is closer than x'
            print('【x_n2】', data['x_n2'])
    except:
        notFound.append('x_n2')
    # x_n3
    try:
        gap_n3 = data['x_min'] - data['n3_min'] 
        if gap_n3 <= 0:
            data['x_n3'] = '✔'
            print('【x_n3】', data['x_n3'])
        else:
            data['x_n3'] = 'n3 is closer than x'
            print('【x_n3】', data['x_n3'])
    except:
        notFound.append('x_n3')
    

    # address
    try:
        #import pdb; pdb.set_trace()
        tmp = dom.xpath('//*[@id="js-view_gallery"]/div[1]/div[2]/div[3]/div[2]/div[2]/div/div[2]/div')[0].text
        data['address'] = tmp.lstrip('\r\n\t\t\t\t\t\t\t\t\t')
    except Exception:
        notFound.append('address')
    print('【address】', data['address'])

    
    # stroy
    # floor
    try:
        #<th class="data_01" scope="cols">階建</th>
        #<td>3階/15階建</td>
        tmp = dom.xpath('//th[contains(text(), "階建")]/following-sibling::td')[0].text
        data['floor_memo'] = tmp
        # floor
        try:
            m_f = re.search('\d*階/', tmp)[0]
            data['floor'] = int(m_f.rstrip('階/'))
        except:
            data['floor'] = tmp
        
        # stroy
        try:
            #import pdb; pdb.set_trace()
            m_s = re.search('\d*階建', tmp)[0]
            data['story'] = int(m_s.rstrip('階建'))
        except:
            data['story'] = tmp
    except Exception:
        notFound.append('floor')
        notFound.append('story')
    print('【floor】', data['floor'])
    print('【story】', data['story'])
    print('【floor_memo】', data['floor_memo'])


    # structure
    ## <th class="data_02" scope="cols">構造</th>
    # <td>鉄筋コン</td>
    try:
        tmp = dom.xpath('//th[contains(text(), "構造")]/following-sibling::td')[0].text
        #import pdb; pdb.set_trace()
        data['structure'] = tmp.lstrip('\r\n\t\t\t\t\t\t')
    except Exception:
        notFound.append('structure')
    print('【structure】', data['structure'])

    return data



BASE_URL = 'https://suumo.jp'
parse = urllib.parse.urlparse(BASE_URL)
surf_url = 'https://suumo.jp/jj/chintai/ichiran/FR301FC001/?ar=030&bs=040&ra=014&cb=0.0&ct=9999999&et=9999999&cn=9999999&mb=0&mt=9999999&shkr1=03&shkr2=03&shkr3=03&shkr4=03&fw2=&ek=022038720&rn=0220'

# setting up when to run single.py
#item_data_url = 'https://suumo.jp/chintai/jnc_000019274646/'

if __name__ == '__main__':
    start = time.time()

    datas = []
    urls = []
    current_url = surf_url
    print(current_url)
    time.sleep(random.randint(3,8))

        
    #If you would like to get data from all pages after 2nd  and more pages...

    while True:
        time.sleep(random.randint(3,8))
        urls.extend(get_urls(current_url))
        print(urls)
        try:
            time.sleep(random.randint(8,12))
            current_url = get_next_page(current_url)
            print('■', current_url)
        except:
            break
    """
            
    # test
    ######### only 1st page ################
    urls.extend(get_urls(current_url))
    ########################################
    """

    time.sleep(random.randint(3,8))
    crawl_number = 1
    print('■■', urls)
    urls_conts = len(urls)
    print('・・・', str(urls_conts) + 'th pages!')

    for item_data_url in urls:
        print('■■■', item_data_url)
        try:
            time.sleep(random.randint(8,12))
            datas.append(scrape(item_data_url, crawl_number))
            print('【No.'+ str(crawl_number) + '】' + item_data_url)
            crawl_number = crawl_number + 1
        except:
            pass
        time.sleep(random.randint(3,8))
    
    column_order = [

        'No.', 'title', 'address', 'structure', 'story', 'layout', 'price/tsubo', 'total_price/JPY', 'floor', 'tsubo', 'x_min', 'year', \
        'property_price/JPY', 'mng_fee/JPY', 'x_n1', 'x_n2', 'x_n3', 'floor_memo','year_memo', 'access_x', \
        'access_n1', 'n1_min', 'access_n2', 'n2_min', 'access_n3', 'n3_min', 'date', 'datetime', 'url'

    ]
    
    if len(datas)!=0:
        df = pd.DataFrame(datas)
   
        #df.to_csv('/xxx/suumo_survey/csv/suumo_mssksg_'+datetime.datetime.now().strftime('%Y%m%d_%H%M%S')+'.csv', sep=',',encoding='UTF-8',index=False, quoting=csv.QUOTE_ALL, columns=column_order)
        #df.to_csv('/xxx/suumo_survey/csv/suumo_mssksg_'+datetime.datetime.now().strftime('%Y%m%d_%H%M%S')+'.tsv', sep='\t',encoding='UTF-8',index=False, quoting=csv.QUOTE_ALL, columns=column_order)
        #df.to_json('/xxx/suumo_survey/csv/suumo_mssksg_'+datetime.datetime.now().strftime('%Y%m%d_%H%M%S')+'.json', force_ascii=False)

        df.to_csv('/xxxxxxxx/suumo/csv/suumo_mssksg_'+datetime.datetime.now().strftime('%Y%m%d_%H%M%S')+'.csv', sep=',',encoding='UTF-8',index=False, quoting=csv.QUOTE_ALL, columns=column_order)
        df.to_csv('/xxxxxxxx/suumo/csv/suumo_mssksg_'+datetime.datetime.now().strftime('%Y%m%d_%H%M%S')+'.tsv', sep='\t',encoding='UTF-8',index=False, quoting=csv.QUOTE_ALL, columns=column_order)
        df.to_json('/xxxxxxxx/suumo/csv/suumo_mssksg_'+datetime.datetime.now().strftime('%Y%m%d_%H%M%S')+'.json', force_ascii=False)

    end = time.time()
    print("process {0} ms".format((end - start) * 1000))
    sys.exit()