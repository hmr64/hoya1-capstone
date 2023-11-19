import requests
from bs4 import BeautifulSoup
import re

from FileReader.BaseHtmlReader import BaseHtmlReader

class NihGrantReader(BaseHtmlReader):

    def __init__(self, url):
        super().__init__(url)

    def extract_text(self, use_regex):
        try:
            response = requests.get(self.url)
   
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
       
                # Find the "Part 2. Full Text of Announcement" header
                part2_header = soup.find('h1', text="Part 2. Full Text of Announcement")

                if part2_header:
                    content_texts = []
           
                    # Navigate to the parent of the header
                    parent_div = part2_header.parent

                    # Extract text from the next div siblings
                    for div_sibling in parent_div.find_next_siblings('div', limit=5):
                        # Append the textual content of the div (without HTML tags) to the content_texts list
                        content_texts.append(div_sibling.get_text(strip=True))

        except Exception as e:
            raise e

        if use_regex:
            return self.get_regex_matches("\n\n".join(content_texts))

        return "\n\n".join(content_texts)




