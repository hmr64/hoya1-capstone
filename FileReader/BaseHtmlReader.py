import requests
from bs4 import BeautifulSoup
import re

from FileReader.BaseFileReader import BaseFileReader

class BaseHtmlReader(BaseFileReader):
    
    def __init__(self, url):
        super().__init__(url)

    def extract_text(self, use_regex):
        try:
            response = requests.get(self.url)
   
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
       
                text = soup.text

        except Exception as e:
            raise e

        if use_regex:
            return self.get_regex_matches(text.strip())

        return text.strip()




