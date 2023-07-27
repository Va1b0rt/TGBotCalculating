import asyncio
import re
from typing import Union

import pandas as pd
import requests
from requests import Response

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
import undetected_chromedriver

SEARCH_URL = 'https://vkursi.pro/search?q='


# driver = webdriver.Chrome('chromedriver.exe')
# driver.get('https://auto.ria.com/uk/cabinet')
# driver.maximize_window()


def get_chromedriver():
    chrome_options = webdriver.ChromeOptions()
    # chrome_options.add_argument(f'{User_Agent}')
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument("--disable-cache")  # Отключение кэширования
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    # chrome_options.add_argument("--disable-cookies")  # Отключение использования куков
    chrome_options.add_argument("--headless")
    _driver = undetected_chromedriver.Chrome(options=chrome_options)
    return _driver


#driver = get_chromedriver()


async def if_in_person_info(egrpou: str) -> bool:
    driver.get(f'{SEARCH_URL}{egrpou}')
    organization_name = None
    try:
        organization_name = driver.find_element(By.CLASS_NAME, 'organization-name')
    except NoSuchElementException:
        pass

    try:
        organization_name = driver.find_element(By.CLASS_NAME, 'title')
    except NoSuchElementException:
        pass

    if organization_name:
        if organization_name:
            return True
        else:
            return False
    else:
        return False


async def get_info(persons_egrpou: list[str]) -> dict[str, bool]:
    result = {}

    for egrpou in persons_egrpou:
        if egrpou in result:
            continue
        else:
            result[egrpou] = await if_in_person_info(egrpou)

    return result


async def get_person_info(egrpou: str) -> Union[bool, Response]:
    """ Get personal info in youcontrol.com.ua """

    url = 'https://youcontrol.com.ua/ru/search/?q='
    headers = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "Accept-Language": 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7,uk;q=0.6',
        "Sec-Ch-Ua": '"Not.A/Brand";v="8", "Chromium";v="114", "Google Chrome";v="114"',
        "Sec-Ch-Ua-Mobile": "?0",
        "Sec-Ch-Ua-Platform": '"Windows"',
        "Sec-Fetch-Dest": 'document',
        "Sec-Fetch-Mode": 'navigate',
        "Sec-Fetch-Site": 'none',
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"}

    pattern = re.compile(r'<title>(.*)</title>')

    req = requests.get(f'{url}{egrpou}', headers=headers)

    if req.status_code > 300:
        await asyncio.sleep(0.5)
        return await get_person_info(egrpou)

    if pattern.search(req.text):
        return True

    return False


if __name__ == '__main__':
    data_frame = pd.read_excel('./test.xls')

    columns = data_frame.columns.values.tolist()

    egrpou_column = data_frame[columns[6]].values.tolist()
    name_column = data_frame[columns[7]].values.tolist()

    egrpous: list[str] = []

    for egrpou in egrpou_column:
        if type(egrpou) is str and len(egrpou) == 10:
            egrpous.append(egrpou)

    #result = asyncio.run(get_info(egrpous))

    #print(result)
    url = 'https://youcontrol.com.ua/ru/search/?q='
    headers = {"Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
               "Accept-Language": 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7,uk;q=0.6',
               "Sec-Ch-Ua": '"Not.A/Brand";v="8", "Chromium";v="114", "Google Chrome";v="114"',
               "Sec-Ch-Ua-Mobile": "?0",
               "Sec-Ch-Ua-Platform": '"Windows"',
               "Sec-Fetch-Dest": 'document',
               "Sec-Fetch-Mode": 'navigate',
               "Sec-Fetch-Site": 'none',
               "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"}

    for egrpou in egrpous:
        req = requests.get(f'{url}{egrpou}', headers=headers)

        pattern = re.compile(r'<title>(.*)</title>')
        print(pattern.search(req.text)[1])



