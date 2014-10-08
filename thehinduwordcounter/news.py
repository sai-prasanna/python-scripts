#! /usr/bin/env python3
import feedparser
import re
from collections import Counter
from bs4 import BeautifulSoup
import threading
import urllib.request
from queue import Queue
from urllib.error import URLError
import json


FEED_URL = 'http://www.thehindu.com/news/national/?service=rss'


class UrlDownloadThread(threading.Thread):
    """Downloads url as html and places it in url,html in url_data queue"""
    def __init__(self, queue_url, queue_url_data):
        threading.Thread.__init__(self)
        self.in_queue = queue_url
        self.out_queue = queue_url_data

    def run(self):
        while True:
            link = self.in_queue.get()
            try:
                u = urllib.request.urlopen(link)
            except URLError as e:
                print(e)
                u.close()
                continue
            html = u.read()
            u.close()
            self.out_queue.put((link, html))
            self.in_queue.task_done()


class WordCountThread(threading.Thread):
    """Word Counter accepts queue of html and a stop file, counts and returns word count"""

    def __init__(self, queue_url_data, queue_word_count, stop_words, to_lower=True):
        threading.Thread.__init__(self)
        self.in_queue = queue_url_data
        self.out_queue = queue_word_count
        self.stop_words = stop_words
        self.to_lower = to_lower

    def run(self):
        while True:
            link, html = self.in_queue.get()
            word_count = self.word_counter(html)
            self.out_queue.put((link, word_count))
            self.out_queue.task_done()
            self.in_queue.task_done()

    def word_counter(self, html):
        """Counts words in Html ,excludes those in exclude list"""
        soup = BeautifulSoup(html)

        article = ''.join([paragraph.string
                           for paragraph in
                           soup.find_all('p', {'class': 'body'})
                           if paragraph.string
                           ])
        article = soup.title.string + article
        if self.to_lower:
            article.lower()
        words = re.findall(r'[a-z]+', article.lower())
        words = [word for word in words if word not in self.stop_words]
        return Counter(words)


class HinduNewsCounter():

    def __init__(self, feed_url, stop_file, thread_count=5, number_of_links=10,
                 word_count_file=None):
        self.feed_url = feed_url
        self.stop_file = stop_file
        self.thread_count = thread_count
        self.stop_words = []
        self.number_of_links = number_of_links
        with open(self.stop_file) as f:
            self.stop_words = f.read().splitlines()
        self.word_count_file = word_count_file
        self.word_count = {}

    def get_links(self, url):
        """Get links from feed,exclude previously mined links"""
        tried_links = []
        if self.word_count_file:
            with open(self.word_count_file) as f:
                j = json.load(f)
                tried_links.extend(j.keys())

        feed = feedparser.parse(url)
        feed_entries = feed['entries']
        links = [entry['link']
                 for entry in feed_entries if entry not in tried_links]
        return links

    def jsonify_word_count(self, file_name):
        """ Dumps the wordcount and links corresponding into  Json file """
        with open(file_name, "a+") as f:
            json.dump(self.word_count, f)

    @staticmethod
    def merge_count(file_name):
        """Merges word count of all links in given link:count dictfile Counts returns merged wordcount """
        with open(file_name) as f:
            d = json.load(f)
            total_count = Counter()
            for item in d.values():
                total_count += Counter(item)
            return total_count

    def count_links(self):
        """Initialises Url ,Counter threads and jsonify_word_count"""
        queue_url = Queue()
        queue_url_data = Queue()
        queue_word_count = Queue()
        links = self.get_links(self.feed_url)

        for i in range(self.thread_count):
            t = UrlDownloadThread(queue_url, queue_url_data)
            t.setDaemon(True)
            t.start()

        for i in range(self.number_of_links):
            queue_url.put(links[i])

        for i in range(self.thread_count):
            wct = WordCountThread(
                queue_url_data, queue_word_count, self.stop_words)
            wct.setDaemon(True)
            wct.start()
        queue_url.join()
        queue_url_data.join()
        queue_word_count.join()
        for _ in range(self.number_of_links):
            link, word_count = queue_word_count.get()
            self.word_count[link] = word_count


def main():
    new = HinduNewsCounter(FEED_URL, "stop.txt", 5, 20)
    new.count_links()
    new.jsonify_word_count("count.json")
    print(HinduNewsCounter.merge_count("count.json"))

if __name__ == '__main__':
    main()
