"""
Pipeline for text processing implementation
"""

from pathlib import Path
from typing import List

from pymorphy2 import MorphAnalyzer
from pymystem3 import Mystem

from article import Article
from constants import ASSETS_PATH


class EmptyDirectoryError(Exception):
    """
    Custom error
    """


class InconsistentDatasetError(Exception):
    """
    Custom error
    """


class UnknownDatasetError(Exception):
    """
    Custom error
    """


class MorphologicalToken:
    """
    Stores language params for each processed token
    """

    def __init__(self, original_word, normalized_form):
        self.original_word = original_word
        self.normalized_form = normalized_form
        self.mystem_tags = ''
        self.pymorphy_tags = ''

    def __str__(self):
        return f"{self.normalized_form}<{self.mystem_tags}>({self.pymorphy_tags})"


class CorpusManager:
    """
    Works with articles and stores them
    """

    def __init__(self, path_to_raw_txt_data: str):
        self.path_to_raw_txt_date = path_to_raw_txt_data
        self._storage = {}
        self._scan_dataset()

    def _scan_dataset(self):
        """
        Register each dataset entry
        """
        path = Path(self.path_to_raw_txt_date)

        for one_file in path.glob('*_raw.txt'):
            idx = str(one_file).split('\\')[-1].split('_')[0]
            self._storage[idx] = Article(url=None, article_id=idx)

    def get_articles(self):
        """
        Returns storage params
        """
        return self._storage


class TextProcessingPipeline:
    """
    Process articles from corpus manager
    """

    def __init__(self, corpus_manager: CorpusManager):
        self.corpus_manager = corpus_manager
        self.text = ''

    def run(self):
        """
        Runs pipeline process scenario
        """
        articles = self.corpus_manager.get_articles()
        for article in articles.values():
            self.text = article.get_raw_text()
            morph_tokens = self._process()
            processed_text = []
            for token in morph_tokens:
                processed_text.append(str(token))
            article.save_processed(' '.join(processed_text))

    def _process(self) -> List[type(MorphologicalToken)]:
        """
        Performs processing of each text
        """
        pymorphy = MorphAnalyzer()
        result = Mystem().analyze(self.text)
        tokens = []

        for token in result:
            if token.get('analysis') and token.get('text'):
                if token['analysis'][0].get('lex') and token['analysis'][0].get('gr'):
                    morph_token = MorphologicalToken(token['text'], token['analysis'][0]['lex'])
                    morph_token.mystem_tags = token['analysis'][0]['gr']
                    morph_token.pymorphy_tags = pymorphy.parse(morph_token.original_word)[0].tag
                    tokens.append(morph_token)
        return tokens


def validate_dataset(path_to_validate):
    """
    Validates folder with assets
    """
    paths = Path(path_to_validate)
    if not paths.exists():
        raise FileNotFoundError

    if not paths.is_dir():
        raise NotADirectoryError

    if not list(paths.iterdir()):
        raise EmptyDirectoryError

    raw_files = list(paths.rglob('*.txt'))
    meta_files = list(paths.rglob('*.json'))
    raw_numbers = list(map(lambda file: int(file.name.split('_')[0]), raw_files))
    correct_indexes = list(range(min(raw_numbers), max(raw_numbers) + 1))
    if len(raw_files) != len(meta_files) or sorted(raw_numbers) != correct_indexes:
        raise InconsistentDatasetError


def main():
    validate_dataset(ASSETS_PATH)
    corpus_manager = CorpusManager(path_to_raw_txt_data=ASSETS_PATH)
    pipeline = TextProcessingPipeline(corpus_manager=corpus_manager)
    pipeline.run()


if __name__ == "__main__":
    main()
