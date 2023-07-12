import asyncio

import pandas as pd

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


driver = get_chromedriver()


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


if __name__ == '__main__':
    data_frame = pd.read_excel('./test.xls')

    columns = data_frame.columns.values.tolist()

    egrpou_column = data_frame[columns[6]].values.tolist()
    name_column = data_frame[columns[7]].values.tolist()

    egrpous: list[str] = []

    for egrpou in egrpou_column:
        if type(egrpou) is str and len(egrpou) == 10:
            egrpous.append(egrpou)

    result = asyncio.run(get_info(egrpous))

    print(result)



