from datetime import datetime

import requests
from bs4 import BeautifulSoup as bs
from seleniumrequests import PhantomJS
from selenium.webdriver import DesiredCapabilities as dc
from selenium import webdriver
from selenium.webdriver.support.wait import WebDriverWait

from googletrans import Translator
import shelve

def write_article(date, body):
    url = 'http://gall.dcinside.com/mgallery/board/write/?id=nendoroid'
    xpaths = {
        'nick':"//input[@name='name']",
        'pw':"//input[@name='password']",
        'title':"//input[@name='subject']",
        'body':"//div[@id='tx_canvas_source_holder']",
    }
    dcap = dict(dc.PHANTOMJS)
    dcap["phantomjs.page.settings.userAgent"] = (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/53 "
        "(KHTML, like Gecko) Chrome/16.0.82"
    )

    title_format = '[알림] 굿스마샵 {} 넨도 예약 마감 D-{}'
    date = date.replace(hour=12)
    today = datetime.now()#.replace(hour=0, minute=0, second=0, microsecond=0)
    dday = date - today

    if dday.days > 3 or dday.days < 0:
        return

    title = title_format.format(date.strftime('%m월%d일'), dday.days)
    print(title)

    driver = PhantomJS(desired_capabilities=dcap)

    driver.get(url)
    driver.find_element_by_xpath(xpaths['nick']).send_keys('넨갤봇')
    driver.find_element_by_xpath(xpaths['pw']).send_keys('2648')
    driver.find_element_by_xpath(xpaths['title']).send_keys(title)
    WebDriverWait(driver, 2)

    html = driver.find_element_by_xpath("//div[@id='tx_switchertoggle']")
    bd = driver.find_element_by_xpath(xpaths['body'])

    def make_body(date, body):
        b = '<p>{} 정오에 예약이 마감됩니다.</p><br/><p>클릭하면 제품 페이지로 이동합니다.</p><br/><ul>'.format(date.strftime('%m월 %d일'))
        for name, link in body:
            b += ('<li><a href="{}" target="_blank">{}</a></li>'.format(link, name))
        b += '</ul>'
        return b

    full_body = make_body(date, body)
    print(full_body)

    actions = webdriver.ActionChains(driver)
    actions.move_to_element(html)
    actions.click()
    actions.move_to_element(bd)
    actions.click()
    actions.pause(1)
    actions.send_keys(full_body)
    actions.pause(1)
    actions.perform()

    submit = driver.find_element_by_xpath("//p[@class='btn_box_right']//input")
    submit.click()
    WebDriverWait(driver, 1)
    #print(driver.get_log('browser'))
    #print(driver.get_log('har'))
    driver.save_screenshot('a.png')
    driver.close()
    print('done!')


def get_info():
    url = 'https://goodsmileshop.com/en/order-close'
    r = requests.get(url)
    soup = bs(r.content)

    data = soup.find('div', class_='order-close-body')
    rows = data.find_all('p')
    idx = 0
    def get_last(rows, _idx):
        date = ''
        items = []
        for row in rows:
            _idx += 1
            text = row.text.strip()
            if row.get('class')[0] == 'order-close-row-last':
                date = text
                break
            #elif text.startswith('ねんどろいど '):
            elif text.startswith('Nendoroid '):
                link = row.find('a')
                name = link.text.strip()
                link = 'https://goodsmileshop.com' + link.get('href')
                items.append([name, link])

        dates = date.split()
        day = ''.join([c for c in dates[0] if c.isdigit()])
        day = '0'+day if len(day) == 1 else day
        month = dates[1]
        year = int(dates[2][:4])
        full_date = datetime.strptime('{}-{}-{}'.format(year, month, day), '%Y-%B-%d')

        return full_date, items, _idx

    date, items, idx = get_last(rows, idx)
    if len(items) == 0:
        date, items, idx = get_last(rows[idx:], idx)

    trans_dict = shelve.open('nendo_en.dict')
    translator = Translator()
    final = []
    for name, link in items:
        try:
            char_name = name.split(' ', 1)[1]
            if char_name in trans_dict:
                trans_name = trans_dict[char_name]
            else:
                trans_name = translator.translate(char_name, src='en', dest='ko').text
                trans_dict[char_name] = trans_name

            name = '넨도로이드 ' + trans_name
        except:
            print('err', name)
        finally:
            final.append((name, link))

    print(date, final)
    trans_dict.close()

    return date, final

def main():
    date, pr = get_info()
    if pr:
        write_article(date, pr)

if __name__ == '__main__':
    main()

