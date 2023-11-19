import requests
from bs4 import BeautifulSoup
import re

from FileReader.BasePdfReader import BasePdfReader

class BjaGrantReader(BasePdfReader):

    def __init__(self, url):
        if "bja.ojp.gov/funding/opportunities" in url:
            pdf_ext = self.get_download_link(url, "Download")

            # Check if the extension is a relative URL or an absolute URL
            if pdf_ext.startswith("http"):
                pdf_link = pdf_ext
            else:
                base_url = url.rsplit('/funding/opportunities', 1)[0]
                pdf_link = base_url + pdf_ext
            
                self.url = pdf_link
        else:
            super().__init__(url)


    def get_start_end_pages(self, doc):
        """
        Find the start and end pages of a specific section of the PDF
        Returns: The pages of the Review Criteria section or the page range of the entire document if it's the wrong format
        """

        (start, end) = super().get_start_end_pages(doc)

        # The TOC only returns the Contents page, so we have to read the text to find what pages we are looking for
        outline = doc.get_toc()
        contents_page = list(filter(lambda a: a[1].strip() == "Contents", outline))

        # This document doesn't use the Contents page, it's the wrong format
        if contents_page == []:
            return (start, end)

        # Get the text from the Contents page
        contents_text = chr(12).join([page.get_text() for page in doc.pages(contents_page[0][2] - 1, contents_page[0][2], 1)])

        # Get the page numbers from the sections we want
        start_ret = re.findall("Review\s+Criteria\s*\.*\s*(\d{1,2})", contents_text) # Review Criteria .......... XX
        end_ret = re.findall("Review\s+Process\s*\.*\s*(\d{1,2})", contents_text)    # Review Process ........... XX

        start = start if start_ret == [] else int(start_ret[0])
        end = end if end_ret == [] else int(end_ret[0])

        return (start, end)


    # Private classes
    def get_download_link(self, url, btn_text):
        """
        Input: url: Url to BJA funding opportunity site (e.g. https://bja.ojp.gov/funding/opportunities/o-bja-2023-171621)
               btn_text: text of the button that we are getting the link from
        Output: Url to the pdf of the grant application
        """

        # Make html request and obtain all <a> tags
        request = requests.get(url)
        html = request.text
        soup = BeautifulSoup(html, 'lxml')
        find_all_a = soup.find_all("a")

        # Find button in xml and get its href link
        download_btn = list(filter(lambda a: a.text.strip() == btn_text, find_all_a))
        return download_btn[0].get("href")




