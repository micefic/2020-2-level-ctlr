"""
Crawler implementation
"""

import json
import os
import datetime

from time import sleep
import requests
from bs4 import BeautifulSoup
from article import Article

from constants import CRAWLER_CONFIG_PATH
from constants import ASSETS_PATH

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                         'Chrome/88.0.4324.111 YaBrowser/21.2.1.107 Yowser/2.5 Safari/537.36'}


class IncorrectURLError(Exception):
    """
    Custom error
    """


class NumberOfArticlesOutOfRangeError(Exception):
    """
    Custom error
    """


class IncorrectNumberOfArticlesError(Exception):
    """
    Custom error
    """


class UnknownConfigError(Exception):
    """
    Most general error
    """


class Crawler:
    """
    Crawler implementation
    """

    def __init__(self, seed_urls: list, max_article: int, max_articles_per_seed: int):
        self.seed_urls = seed_urls
        self.max_article = max_article
        self.max_articles_per_seed = max_articles_per_seed
        self.urls = []

    @staticmethod
    def _extract_url(article_bs):
        return article_bs.find('a').attrs['href']

    def find_articles(self):
        """
        Finds articles
        """
        for url in self.seed_urls:
            response = requests.get(url, headers=headers)
            sleep(5)
            if not response:
                raise IncorrectURLError
            page_soup = BeautifulSoup(response.content, features='lxml')
            article_soup = page_soup.find_all('h1', class_='entry-title')
            for article_bs in article_soup[:self.max_articles_per_seed]:
                if len(self.urls) <= self.max_article and article_bs not in self.urls:
                    seed_url = self._extract_url(article_bs)
                    self.urls.append(seed_url)
            return self.urls

    def get_search_urls(self):
        """
        Returns seed_urls param
        """
        return self.seed_urls


class ArticleParser:
    """
    ArticleParser implementation
    """

    def __init__(self, full_url: str, article_id: int):
        self.full_url = full_url
        self.article_id = article_id
        self.article = Article(full_url, article_id)

    def _fill_article_with_text(self, article_soup):
        par_soup = article_soup.find('div', class_="entry-content").find_all('p')
        for par in par_soup:
            self.article.text += par.text.strip() + '\n'

    def _fill_article_with_meta_information(self, article_soup):
        self.article.title = article_soup.find('h1', class_='entry-title').text.strip()
        self.article.author = 'NOT FOUND'
        for topic in article_soup.find_all('a', rel="tag"):
            self.article.topics.append(topic.text)
        self.article.date = self.unify_date_format(article_soup.find('time', class_='entry-date').text)

    @staticmethod
    def unify_date_format(date_str):
        """
        Unifies date format
        """
        return datetime.datetime.strptime(date_str, "%d.%m.%Y")

    def parse(self):
        """
        Parses each article
        """
        request = requests.get(self.full_url, headers=headers).content
        article_bs = BeautifulSoup(request, features='lxml')
        self._fill_article_with_text(article_bs)
        self._fill_article_with_meta_information(article_bs)
        self.article.save_raw()
        return self.article


def prepare_environment(base_path):
    """
    Creates ASSETS_PATH folder if not created and removes existing folder
    """
    if not os.path.exists(base_path):
        os.makedirs(base_path)


def validate_config(crawler_path):
    """
    Validates given config
    """
    with open(crawler_path, 'r', encoding='utf-8') as file:
        crawler_config = json.load(file)

    if ('base_urls' not in crawler_config
            or not isinstance(crawler_config['base_urls'], list)
            or not all([isinstance(url, str) for url in crawler_config['base_urls']])):
        raise IncorrectURLError

    if ('total_articles_to_find_and_parse' in crawler_config and
            isinstance(crawler_config['total_articles_to_find_and_parse'], int)
            and crawler_config['total_articles_to_find_and_parse'] > 101):
        raise NumberOfArticlesOutOfRangeError

    if (not isinstance(crawler_config['total_articles_to_find_and_parse'], int)
            or 'total_articles_to_find_and_parse' not in crawler_config
            or 'max_number_articles_to_get_from_one_seed' not in crawler_config):
        raise IncorrectNumberOfArticlesError

    return (crawler_config['base_urls'],
            crawler_config['total_articles_to_find_and_parse'],
            crawler_config['max_number_articles_to_get_from_one_seed'])


if __name__ == '__main__':
    # YOUR CODE HERE
    urls, maximum_articles, maximum_articles_per_seed = validate_config(CRAWLER_CONFIG_PATH)
    crawler = Crawler(urls, maximum_articles, maximum_articles_per_seed)
    articles = crawler.find_articles()
    prepare_environment(ASSETS_PATH)

    for ind, article_url in enumerate(crawler.urls):
        parser = ArticleParser(full_url=article_url, article_id=ind+1)
        sleep(5)
        article = parser.parse()
        article.save_raw()
