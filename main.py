import requests
from tqdm import tqdm
import pandas as pd
import time

from Review_collector import Review_collector

CSV = 'Stopgame_review_links.csv'
HOST = 'https://stopgame.ru'
URL = 'https://stopgame.ru/review'
HEADERS = {
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/97.0.4692.99 Safari/537.36'
}


def get_html(url: str, params=''):
    while True:
        req = requests.get(url, headers=HEADERS, params=params)
        if req.status_code == 200:
            break
        else:
            time.sleep(60)
    return req


def get_html_for_reviews_page(url: str, pageNumber: int):
    correct_url = url + '/p' + str(pageNumber)
    req = get_html(correct_url)
    return req


def save_results_to_csv(items: list, path: str):
    df = pd.DataFrame(items)
    df.to_csv(path, index=False, sep=';', encoding='utf-8-sig')


def parse():
    games = []
    PAGENATION = input('Specify the quantity of pages to parse: ')
    PAGENATION = int(PAGENATION.strip())
    html = get_html_for_reviews_page(URL, 1)
    if html.status_code == 200:  # check the connection and if successfully:
        print('The parsing process has started successfully...')
        for page in tqdm(range(1, PAGENATION + 1), desc='Pages'):
            html = get_html_for_reviews_page(URL, pageNumber=page)
            games.extend(Review_collector().get_review_page_content(html.text))
        print('Parsing has finished successfully!')
        # print(games)
    else:  # or:
        print('Error! -> ' + URL)
    save_results_to_csv(games,
                        CSV)  # saving results in .csv in the path of your project
    print('Your results successfully saved in ' + CSV)


parse()
