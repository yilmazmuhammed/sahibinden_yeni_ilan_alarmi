import json
from datetime import datetime
from time import sleep

from bs4 import BeautifulSoup
from pygame import mixer
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service
from webdriver_manager.firefox import GeckoDriverManager

FILE_NAME = "search_result.html"
JSON_FILE = "ilanlar.json"
ALL_JSON_FILE = "all_" + JSON_FILE


def write_adverts_to_file(adverts, filename):
    with open(filename, "w") as json_file:
        json.dump(adverts, json_file, indent=4)


def read_adverts_from_file(filename):
    try:
        with open(filename) as json_file:
            data = json.load(json_file)
    except Exception as e:
        print(type(e), e)
        data = {}
    return data


def find_new_adverts(old_adverts, new_adverts):
    result = {}
    for advert_id, advert in new_adverts.items():
        if not old_adverts.get(advert_id):
            result[advert_id] = advert

    return result


def get_soup_from_url(driver, url):
    driver.get(url)
    html = driver.page_source
    soup = BeautifulSoup(html, 'html.parser')
    return soup


def get_new_adverts_from_url(url):
    options = Options()
    options.add_argument("--headless")
    driver = webdriver.Firefox(service=Service(GeckoDriverManager().install()), options=options)

    paging_offset = 0
    paging_size = 50
    adverts = {}
    old_advert_count = 0
    while True:
        modified_url = url
        if paging_offset:
            modified_url = modified_url + "&pagingOffset=" + str(paging_offset)
        modified_url = modified_url + "&pagingSize=" + str(paging_size)
        print("Searched url:", modified_url)

        soup = get_soup_from_url(driver, modified_url)

        result = soup.find_all(attrs={"class": "searchResultsItem"})

        for i, element in enumerate(result):
            try:
                date_field = element.find_all(attrs={"class": "searchResultsDateValue"})[0].text
                for i in ["<span>", "</span>", "<br/>"]:
                    date_field = date_field.replace(i, "")
                date_field = date_field.replace("\n\n", " ")
                date_field = date_field.replace("\n", "")
                advert = {
                    "date": date_field.strip(),
                    "price": element.find_all(attrs={"class": "searchResultsPriceValue"})[0].find_all("span")[
                        0].text.strip(),
                    "title": element.find_all(attrs={"class": "classifiedTitle"})[0].text.strip(),
                    "url": "https://www.sahibinden.com" + element.find_all(attrs={"class": "classifiedTitle"})[0]["href"],
                    "time": datetime.now().strftime("%Y-%m-%d %H:%M")
                }
                advert_id = element["data-id"]
                adverts[advert_id] = advert
                # print(advert_id, advert)
            except:
                pass
        paging_offset += paging_size
        if len(adverts) % paging_size not in [0, 1] or len(adverts) == old_advert_count:
            break
        old_advert_count = len(adverts)

    print("Toplam ilan sayısı:", len(adverts))

    print("-" * 150)

    driver.close()
    old_adverts = read_adverts_from_file(ALL_JSON_FILE)

    new_adverts = find_new_adverts(old_adverts=old_adverts, new_adverts=adverts)

    if len(new_adverts) > 0:
        old_adverts.update(new_adverts)
        write_adverts_to_file(old_adverts, ALL_JSON_FILE)

    return new_adverts


def play_beep():
    mixer.init()
    beep = mixer.Sound("bell.wav")
    beep.play()


def open_adverts_with_new_tabs(adverts, driver=None):
    if driver is None:
        driver = webdriver.Firefox(service=Service(GeckoDriverManager().install()))

    driver.get('http://google.com')
    for advert_id, advert in adverts.items():
        driver.execute_script(f"window.open('about:blank', '{advert_id}');")
        driver.switch_to.window(f"{advert_id}")
        driver.get(advert["url"])


if __name__ == '__main__':
    URL = "https://www.sahibinden.com/kiralik-daire?a23=38517&a23=284406&a23=38511&a23=38512&a23=1133903&a23=38515&a23=38513&a23=38518&a23=1199428&a23=38516&a23=149999&a23=1199436&a23=1174010&a23=1182365&sorting=date_desc&viewType=List&address_quarter=26580&address_quarter=26551&address_quarter=26432&address_quarter=26552&address_quarter=26431&address_quarter=26434&address_quarter=26433&address_quarter=26557&address_quarter=26545&address_quarter=26435&address_quarter=26548&address_district=2489&address_town=513&address_town=514&address_town=515&a20=38470&a20=1227923&price_max=4000&address_city=38"
    while True:
        print(datetime.now().strftime("%Y-%m-%d_%H-%M") + ": Yeni ilanlar aranıyor")
        new_adverts = get_new_adverts_from_url(url=URL)
        if len(new_adverts):
            print("Yeni ilan sayısı:", len(new_adverts))
            print("Yeni ilanlar:")
            for advert_id, advert in new_adverts.items():
                print(advert_id, advert)

            write_adverts_to_file(new_adverts, datetime.now().strftime("%Y-%m-%d_%H-%M_") + JSON_FILE)
            play_beep()
            # open_adverts_with_new_tabs(new_adverts)
        else:
            print("Yeni ilan bulunamadı")

        print("+" * 150 + "\n\n")
        sleep(5 * 60)
