import os
import requests
from bs4 import BeautifulSoup
from whoosh.index import create_in, open_dir
from whoosh.fields import *
from whoosh.qparser import QueryParser
from whoosh import scoring
from urllib.parse import urljoin, urlparse
from spellchecker import SpellChecker  # Import the SpellChecker class

# Define a class crawler
class Crawler:
    def __init__(self, starting_url):
        # initialize the starting url
        self.starting_url = starting_url
        self.stack = [starting_url]
        self.visited = set()
        # define the index schema
        self.schema = Schema(url=TEXT(stored=True), title=TEXT(stored=True), content=TEXT(stored=True))
        self.index_dir = "whoosh_index"

        # Create or open the index directory
        if not os.path.exists(self.index_dir):
            os.mkdir(self.index_dir)

        # Try to open the existing index, or create a new one if it doesn't exist
        try:
            self.index = open_dir(self.index_dir)
        except:
            self.index = create_in(self.index_dir, self.schema)

        # instance of SpellChecker
        self.spell_check = SpellChecker()

    # function to crawl the web page
    def crawl(self):
        while self.stack:
            # remove the current url
            url = self.stack.pop(0)
            if url not in self.visited:
                # handle response errors
                try:
                    response = requests.get(url, timeout=5)
                    print(f"Current URL: {url}")

                    if response.status_code == 200:
                        # extract html content
                        soup = BeautifulSoup(response.content, 'html.parser')
                        title_text = soup.find('title').text if soup.title else "No title was found"
                        content = ' '.join(soup.stripped_strings)

                        with self.index.writer() as writer:
                            writer.add_document(url=url, title=title_text, content=content)

                        self.visited.add(url)
                        # get all the links and append them to the url
                        for link in soup.find_all('a', href=True):
                            absolute_url = urljoin(url, link['href'])
                            if urlparse(absolute_url).netloc == urlparse(self.starting_url).netloc:
                                if absolute_url not in self.visited and absolute_url not in self.stack:
                                    self.stack.append(absolute_url)

                except Exception as e:
                    print(f"Error while processing {url}: {e}")

            print(f"Stack of websites left: {self.stack}")
            print(f"Crawled websites: {self.visited}")

    # define a function to search the index
    def search(self, query):
        # spellcheck the query
        correct_query = ' '.join([self.spell_check.correction(word) for word in query.split()])
        # return the url, title, content with TF-IDF scoring
        results=[]
        with self.index.searcher(weighting=scoring.TF_IDF()) as searcher:
            query = QueryParser("content", self.index.schema).parse(correct_query)
            #search and print matched terms
            for result in searcher.search(query,terms=True):
                if result.has_matched_terms():
                    print(results.matched_terms)
                    results.append([{'url': result['url'], 'title': result['title'], 'content': result['content'], 'score': result.score}])
            
    
            return results

# Testing code
# create an instance of the crawler class
crawler = Crawler(starting_url='https://vm009.rz.uos.de/crawl/index.html')
crawler.crawl()
search_word = "plapytus"
search_results = crawler.search(search_word)
print(search_results)
