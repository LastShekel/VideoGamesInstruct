import requests
from bs4 import BeautifulSoup as BS
from bs4.element import Tag, NavigableString
import re
import time
from typing import Union


class Review_collector:

    def __init__(self, headers=None, host=None):
        self.games = None
        if not headers:
            self.headers = {
                'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
                'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/97.0.4692.99 Safari/537.36'
            }

        if not host:
            self.host = 'https://stopgame.ru'

    def add_text(self, main: str, text: Union[str, NavigableString]):
        separators = [' ', '\n']
        if len(main) == 0:
            return text
        if len(text) == 0:
            return main

        if main[-1] in separators and text[0] in separators:
            return self.add_text(main[:-1], text[1:])
        if main[-1] in separators and not (text[0] in separators):
            return self.add_text(main[:-1], text)
        if not (main[-1] in separators) and text[0] in separators:
            return self.add_text(main, text[1:])
        if not (main[-1] in separators) and not (text[0] in separators):
            return main + ' ' + text

    def filter_text(self, text: Union[Tag, NavigableString, str]):
        result = ''
        if type(text) == NavigableString or type(text) == str:
            return text
        if text.attrs.get('class', None):
            if sum(map(lambda c: True if re.match(".*gallery.*", c) else False,
                       text.attrs['class'])):  ## skip pictures
                return result
        if type(text) == Tag and text.name == 'abbr':
            return text.attrs['title']
        for part in text:
            addition = ''
            if type(part) == NavigableString:
                addition = self.filter_text(part)
            if part.name == 'p':
                addition = self.filter_text(part.contents[0])
            if str(part) == '<br>' or str(part) == '<br/>':
                continue
            if part.name == 'b' or part.name == 'u':
                if len(part.contents) == 0:
                    continue
                addition = self.filter_text(part.contents[-1])
            if part.name == 'i' or part.name == 'em':
                addition = self.filter_text(part)
            if part.name == 'ol' or part.name == 'ul':
                list_counter = 1
                for li in part.contents:
                    addition = str(list_counter) + '. ' + self.filter_text(li)
                    list_counter += 1
            if part.name == 'blockquote':
                addition = '"' + str(part.contents[0]) + '"'
            if part.name == 'span':
                addition = self.filter_text(part.contents[0])
            if part.name == 'strong':
                addition = part.contents[0]
            if part.name == 'sg-spoiler':
                addition = '"' + self.filter_text(part) + '"'
            if part.name == 'abbr':
                if '█' in self.filter_text(part.contents[0]):
                    addition = part.attrs['title']
                elif type(part.contents[0]) == Tag:
                    addition = self.filter_text(part.contents[0])
                else:
                    addition = part.contents[0]
            if part.name == 'a':
                addition = self.filter_text(part.contents[-1])
            if part.name == 'lite-youtube':
                addition = '\n'+str(part.contents[1]['href'])+'\n'
            if part.name == 'div':
                if hasattr(part, 'attrs') and 'class' in part.attrs:
                    if 'caption' in part.attrs['class'][0]:
                        addition = self.filter_text(part.contents[0])
                    if 'content' in part.attrs['class'][0]:
                        for content in part.contents:
                            result = self.add_text(result,
                                                   self.filter_text(
                                                       content))
                    if 'stop-choice' in part.attrs['class'][0]:
                        addition = 'Наш выбор.'
                    elif 'review-rating' in part.attrs['class'][0]:
                        addition = part.text
                        if 'Оценка игры' in part.contents[0]:
                            addition += ':'
                        else:
                            review_rating = list(
                            filter(lambda x: 'active' in
                                             ' '.join(x['class']),
                                   part.contents))[0]
                            rus_rating = review_rating.contents[0]['href'][9:]
                            if rus_rating == 'musor':
                                rating = 'мусор'
                            if rus_rating == 'prohodnyak':
                                rating = 'проходняк'
                            if rus_rating == 'pohvalno':
                                rating = 'похвально'
                            if rus_rating == 'izum':
                                rating = 'изумительно'
                            addition = rating
                else:
                    result = self.add_text(result, self.filter_text(part))
            result = self.add_text(result, addition)

        return result+'\n'

    def link_to_review(self, link: str):
        soup = BS(self._get_html(self.host + link).text, 'html.parser')
        content = soup.find('div', class_=re.compile(".*_content_.*"))
        review = ''
        for text in content.contents:
            if type(text) == NavigableString:
                review += '\n'
                continue
            if type(text) != Tag:
                continue
            review += self.filter_text(text)
        review = review.replace(' ', ' ')
        review = review.replace('<br/>', '')
        review = review.rstrip()
        review = review.lstrip()
        return review

    def _get_html(self, url: str, params=''):
        while True:
            req = requests.get(url, headers=self.headers, params=params)
            if req.status_code == 200:
                break
            else:
                time.sleep(60)
        return req

    def get_review_page_content(self, html: str):
        soup = BS(html, 'html.parser')
        grid = soup.find('div', class_=re.compile(
            ".*default-grid.*"))  # "_default-grid_b9a3a_208" find all reviews on page
        items = []
        for i in grid.descendants:
            if type(i) != Tag:
                continue
            items.append(i)

        games = []
        for item in items:
            article = item.find('article')
            if article is None:
                continue
            href = [a['href'] for a in article.find_all('a')][0]
            review = self.link_to_review(href)
            games.append(
                {
                    'title': article.attrs['aria-label'][7:],
                    'review_link': self.host + href,
                    'review': review
                }
            )
        self.games = games
        return games
