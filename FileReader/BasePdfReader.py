import requests
import fitz

from FileReader.BaseFileReader import BaseFileReader

class BasePdfReader(BaseFileReader):

    def __init__(self, url):
        super().__init__(url)

    def get_start_end_pages(self, doc):
        start = 0
        end = doc.page_count
        return (start, end)

    def extract_text(self, use_regex):
        # Sentences we want to look for in the grant pdfs

        # Get pdf text
        try:
            request = requests.get(self.url)

            if request.status_code == 200:
                with fitz.open(stream=request.content, filetype="pdf") as doc:
                    (start, end) = self.get_start_end_pages(doc)
                    text = chr(12).join([page.get_text() for page in doc.pages(start, end, 1)])
            else:
                raise

        except Exception as e:
            raise e

        if use_regex:
            return self.get_regex_matches(text)

        return text




