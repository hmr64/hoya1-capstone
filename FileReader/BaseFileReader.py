from abc import ABC, abstractclassmethod
import re

class BaseFileReader(ABC):
    """description of class"""

    # Optional list of sentences to search for within the pdf text
    regex_list = [
            r"\s+[^.]*\bstatistic(s)?\s+or\b[^.]*\.(?=\s)",  # Matches sentences with "statistic/statistics or"
            r"\s+[^.]*\bdata\s+and\b[^.]*\.(?=\s)",  # Matches sentences with "data and"
            r"\s+[^.]*\bEvaluation\b[^.]*\.(?=\s)",  # Matches sentences with "Evaluation"
            r"\s+[^.]*\bMetrics\b[^.]*\.(?=\s)",  # Matches sentences with "Metrics"
            r"\s+[^.]*\bevidence\s+of\b[^.]*\.(?=\s)",  # Matches sentences with "evidence of"
            r"\s+[^.]*\btarget\s+population\b[^.]*\.(?=\s)"  # Matches sentences with "target population"
    ]

    def __init__(self, url):
        self.url = url

    @abstractclassmethod
    def extract_text(self, use_regex):
        pass

    def get_regex_matches(self, text):
        """
        Input: url: Url to pdf of grant information
               regex_list: List of regex strings that we want matches for
        Output: Sentences from the pdf that match the regex strings
        """

        # Get regex matches from the pdf text
        matches = []
        for regex in self.regex_list:
            matches.extend(re.findall(regex, text))

        return " ".join(matches).strip()




