import argparse
import asyncio
import logging

import requests
from tqdm import tqdm
import pandas as pd
import time

from ReviewCollector import ReviewCollector

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
HOST = 'https://stopgame.ru'
URL = 'https://stopgame.ru/review'
HEADERS = {
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/97.0.4692.99 Safari/537.36'}


def get_html(url: str) -> requests.Response:
    while True:
        req = requests.get(url, headers=HEADERS)
        if req.status_code == 200:
            break
        else:
            time.sleep(60)
    return req


async def get_html_for_reviews_page(url: str,
                                    pageNumber: int) -> requests.Response:
    correct_url = url + '/p' + str(pageNumber)
    req = get_html(correct_url)
    return req


def save_results_to_csv(items: list, path: str) -> None:
    df = pd.DataFrame(items)
    df.to_csv(path, index=False, sep=';', encoding='utf-8-sig')


async def parse(n_pages: int, result_file: str) -> None:
    games = []
    html = await get_html_for_reviews_page(URL, 1)
    if html.status_code == 200:  # check the connection and if successfully:
        logger.info('The parsing process has started successfully')
        htmls = await asyncio.gather(
            *[get_html_for_reviews_page(URL, pageNumber=page)
              for page in
              range(1, n_pages + 1)])
        games = await asyncio.gather(
            *[ReviewCollector().get_review_page_content(html.text) for html in
              tqdm(htmls, desc='Pages')])
        logger.info('Parsing has finished successfully!')
    else:
        logger.error('Error! -> ' + URL)
    save_results_to_csv([item for sublist in games for item in sublist], result_file)
    logger.info('Your results successfully saved in ' + result_file)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        prog='StopGame Review Collector',
        description='Collects review from StopGame.ru',
    )
    parser.add_argument(
        '-f',
        '--filename',
        action='store',
        help='filename where reviews will be stored. Default: Stopgame_review_links.csv')
    parser.add_argument('-p', '--pages', action='store',
                        help='number of pages to review in site', default=10)
    parser.add_argument('-v', '--verbose', action='store_true',
                        help='log verbosity. if true logger set to debug')
    args = parser.parse_args()
    if args.verbose:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)
    result_file = args.filename
    if args.pages is None:
        logger.info(
            'Pages not set, setting default %d number of pages' % args.pages)
    pages = int(args.pages)

    if result_file is None:
        result_file = 'Stopgame_review_links.csv'
        logger.info('Result file not set saving to %s' % result_file)
    asyncio.run(parse(pages, result_file))
