import asyncio
import os
import typing as T  # noqa
import pandas as pd
from lexicalrichness import LexicalRichness

from src.neural_network.base import NeuralNetworkBase
from src.neural_network.nn_models.utils.timeit import timeit
from src.repos.factories.user_question_metric import TgUserQuestionMetricRepo
from src.settings import NNModelsSettings
from src.settings.static import OTHER_DATA_DIR


class LRVariedVocabulary(NeuralNetworkBase):
    def __init__(self, settings: NNModelsSettings, uq_metric_repo: TgUserQuestionMetricRepo):
        super().__init__(settings, uq_metric_repo)
        self.ielts_academic_vocabulary: T.Optional[T.List[str]] = None

    def load(self):
        if not self.ielts_academic_vocabulary:
            self.ielts_academic_vocabulary = self.load_ielts_academic_words(
                os.path.join(OTHER_DATA_DIR, 'ielts_academic_vocabulary.csv'))
        super().load()

    @timeit
    def lr_varied_vocabulary(self, text, **kwargs) -> float:
        lex = LexicalRichness(text)
        cttr = lex.cttr
        terms = lex.terms
        ielts_count = sum(1 for word in self.ielts_academic_vocabulary if word in set(text.lower().split()))
        thresholds = {
            'cttr': [(7.385, 9), (7.058, 8), (6.790, 7), (6.535, 6), (6.014, 5),
                     (5.690, 4), (4.251, 3), (3.251, 2), (2.251, 1)],
            'terms': [(250, 9), (200, 8), (150, 7), (100, 6), (75, 5), (50, 4), (25, 3)],
            'ielts_count': [(15, 9), (12, 8), (9, 7), (6, 6), (4, 5), (3, 4), (2, 3), (1, 2)]
        }
        scores = [
            LRVariedVocabulary.calculate_metric_score(cttr, thresholds['cttr']),
            LRVariedVocabulary.calculate_metric_score(terms, thresholds['terms']),
            LRVariedVocabulary.calculate_metric_score(ielts_count, thresholds['ielts_count'])
        ]
        final_score = float(round(sum(scores) / 3))

        uq_id: T.Optional[int] = kwargs.get('uq_id', None)
        if uq_id is not None:
            asyncio.create_task(self.save_metric_data(uq_id, 'lr_vowu', final_score))

        return final_score

    @staticmethod
    def calculate_metric_score(value, thresholds):
        return next((score for threshold, score in thresholds if value >= threshold), 1)

    @staticmethod
    def load_ielts_academic_words(file_path):
        df = pd.read_csv(file_path, header=None, names=["words"])
        return df['words'].tolist()
