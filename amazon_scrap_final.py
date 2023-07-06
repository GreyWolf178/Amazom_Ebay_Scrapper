from datetime import datetime
import os
import pandas as pd
import sys
from selenium.webdriver.common.by import By
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
import time


def resource_path(relative_path):
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


def get_driver():
    options = Options()
    # options.add_argument("--log-level=3")
    options.add_experimental_option('excludeSwitches', ['enable-logging'])
    options.add_experimental_option('excludeSwitches', ['enable-automation'])
    options.add_experimental_option('useAutomationExtension', False)
    # options.headless = True
    options.add_argument("--window-size=1280x720")
    options.add_argument("start-maximised")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument('--disable-features=VizDisplayCompositor')
    options.add_argument("--disable-notifications")

    ser = Service(resource_path('chromedriver.exe'))
    driver = webdriver.Chrome(options=options, service=ser)
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": """
            Object.defineProperty(navigator, 'webdriver', {
              get: () => undefined
            })
          """
    })
    driver.maximize_window()
    return driver


def accept_cookies(driver_):
    try:
        driver_.find_elements(By.XPATH, '//a[text()="Continue without accepting"]')[0].click()
        time.sleep(2)
    except:
        pass


def start_main(driver, req_file):
    df = pd.read_csv(req_file)
    image_ = ['Image URL 1', 'Image URL 2', 'Image URL 3', 'Image URL 4', 'Image URL 5', 'Image URL 6', 'Image URL 7']
    final_data = list()
    done_code = list()
    old_data_dic = dict()
    for index, code in df.iterrows():
        print(f'You are on {str(index + 1)} number')
        code_ = code[0]
        code = code[0].split(';')[0]
        if code in done_code:
            final_data.append({'ASIN;EAN;LPN': code_, **old_data_dic[code]})
            print(f'Duplicate Code {code}')
            continue
        done_code.append(code)
        url = f'https://www.amazon.de/s?k={code}'
        print(code)
        try:
            driver.get(url)
        except:
            pass
        time.sleep(4)
        accept_cookies(driver_=driver)
        boxes = driver.find_elements(By.CSS_SELECTOR, '.s-card-border')
        pro_links = list()
        while True:
            try:
                if boxes:
                    pro_links = [v.find_elements(By.TAG_NAME, 'a')[0].get_attribute('href') for v in boxes if
                                 not v.find_elements(By.CLASS_NAME, 'puis-label-popover-default')]
                print(f'{code} gets {len(pro_links)}  links!')
                break
            except:
                time.sleep(4)
                boxes = driver.find_elements(By.CSS_SELECTOR, '.s-card-border')
        if pro_links:
            for ind, p_link in enumerate(pro_links):
                print(f'{str(ind + 1)} sub number')
                try:
                    driver.get(p_link)
                except:
                    pass
                time.sleep(2)
                accept_cookies(driver_=driver)

                tittle = ''
                price = ''
                bullets = ''
                image_links = list()
                title_div = driver.find_elements(By.ID, 'productTitle')
                if title_div:
                    tittle = title_div[0].text
                price_div = driver.find_elements(By.CSS_SELECTOR, '.apexPriceToPay span')
                if price_div:
                    price_div = [v for v in price_div if v.get_attribute('class') != 'a-offscreen']
                    price = price_div[0].text
                bullets_div = driver.find_elements(By.ID, 'feature-bullets')
                if bullets_div:
                    bullets = bullets_div[0].text.replace('About this item', '')
                while True:
                    try:
                        to_click = driver.find_elements(By.CSS_SELECTOR, '.image .imgTagWrapper')
                        if to_click:
                            to_click[0].click()
                            break
                    except:
                        driver.refresh()
                        time.sleep(5)
                to_get = driver.find_elements(By.CSS_SELECTOR, ".a-popover-wrapper:not([class*=' '])")
                if to_get:
                    image_links_div = None
                    to_get = to_get[0]
                    for _ in range(3):
                        image_links_div = to_get.find_elements(By.CLASS_NAME, 'ivThumbImage')
                        if image_links_div:
                            break
                        else:

                            time.sleep(2)
                    if image_links_div:
                        for index, image_div in enumerate(image_links_div):
                            if len(image_links) == 7:
                                break
                            try:
                                image_div.click()
                            except:
                                continue
                            time.sleep(1.5)
                            temp_img = to_get.find_elements(By.CSS_SELECTOR, '#ivLargeImage img')
                            temp_img = [v.get_attribute('src') for v in temp_img if
                                        v.get_attribute('src') not in image_links]
                            if temp_img:
                                temp_img = temp_img[0]
                                image_links.append(temp_img)
                if image_links:
                    image_links = list(set(image_links))
                else:
                    try:
                        image_links.append(driver.find_element(By.CSS_SELECTOR, '.image .imgTagWrapper img').get_attribute('src'))
                    except:
                        pass

                result_dict = {image: '' if index >= len(image_links) else image_links[index] for index, image in
                               enumerate(image_)}
                pre_dict = {
                    'Tittle': tittle,
                    'Price': price,
                    'Bullets': bullets,
                    'Ref Link': p_link,
                    'Ref Code': code}
                sum_dict = pre_dict.copy()
                sum_dict.update(result_dict)
                old_data_dic[code] = sum_dict
                try:
                    final_data.append({'ASIN;EAN;LPN': code_, **old_data_dic[code]})
                except Exception as e:
                    print(e)
                    pass
        else:
            result_dict = {image: '' for image in image_}
            pre_dict = {
                'Tittle': '',
                'Price': '',
                'Bullets': '',
                'Ref Link': '',
                'Ref Code': code}

            sum_dict = pre_dict.copy()
            sum_dict.update(result_dict)
            old_data_dic[code] = sum_dict
            final_data.append({'ASIN;EAN;LPN': code_, **old_data_dic[code]})

    driver.quit()
    return final_data


def save_data(final_data, file_name):
    date_string = datetime.now().strftime("%Y-%m-%d %H:%M:%S").replace(':', '')
    df = pd.DataFrame(final_data)
    df.to_csv('{}_{}.csv'.format(file_name, date_string), index=False, encoding='utf-8-sig')
    df.to_excel('{}_{}.xlsx'.format(file_name, date_string), index=False)


if __name__ == '__main__':
    driver = get_driver()
    final_data = start_main(driver=driver, req_file='LKW Drogiere ASIN EAN1.csv')
    save_data(final_data=final_data, file_name='demo_german_amazon1')
