# hoya1-capstone

## File Reader Code
BaseFileReader is the parent class of all file readers. Its abstract function extract_text() is implemented in each child class to extract the desired text from the document. 
extract_text() takes in a boolean argument that indicates whether the function should return only regex matches. The regex list is also in BaseFileReader, and can be edited. 

BaseHtmlReader and BasePdfReader are child classes of BaseFileReader, and have implemented extract_text() to scrape the text of an entire HTML or PDF document. 

BjaGrantReader is a child class of BasePdfReader, which utilizes the function get_start_end_pages() to specify which sections of the grant should be read. 
This class has a couple additional functions that allow the user to enter the url of the BJA site that contains a "download" button for the grant. It will pull the grant application pdf from this button before reading the text.

NihGrantReader is a child class of BasePdfReader, which implements the function extract_text() to read specific sections of the NIH grant application.

To create new grant specific classes, please inherit from BasePdfReader and override get_start_end_pages() or inherit from BaseHtmlReader and override extract_text(). 
BjaGrantReader and NihGrantReader can be used as examples.

## LoadCensusArchive.py
This script calls the Census API and copies the necessary data for the matching algorithm into a local SQL database census_archive.db. It can be run at any time to update the database.
Currently this script reads Census API data from the years 2019 through 2022.

## final.py
Contains all streamlit code to take in a grant url from the user, perform our matching algorithm, and display relevant datasets with hyperlinks to the census data website.
