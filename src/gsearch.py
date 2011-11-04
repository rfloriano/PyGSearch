import urllib2
import urlparse
import re
import ClientCookie
from urllib import urlencode
from BeautifulSoup import BeautifulSoup


class Gsearch(object):

    URL = "http://www.google.com.br/search?%s"
    PER_PAGE = 10
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows; U; Windows NT 5.0; en-GB; rv:1.8.1.12) Gecko/20080201 Firefox/2.0.0.12',
        'Accept': 'text/xml,application/xml,application/xhtml+xml,text/html;q=0.9,text/plain;q=0.8,image/png,*/*;q=0.5',
        'Accept-Language': 'en-gb,en;q=0.5',
        'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.7',
        'Connection': 'keep-alive',
    }
    query = ""
    params = {
        "client": "ubuntu",
        "channel": "fs",
        "ie": "utf-8",
        "oe": "utf-8",
    }

    _start = 0

    def __init__(self, query):
        self.query = query

    def _total(self):
        total = self.soup.find("div", id="subform_ctrl").findAll("div")[1].string
        try:
            return int(re.search(r"\d\S+", total).group(0).replace("."))
        except:
            return 0

    def _pages(self):
        pages = len(self.soup.find("table", id="nav").findAll("td"))
        if pages < self.PER_PAGE:
            return pages
        else:
            return self._total() / self.PER_PAGE

    def makeParams(self):
        data = self.params
        if self._start != 0:
            data.update(self.getParamsPage())
        return urlencode(data)

    def request(self):
        self.params["q"] = self.query
        request = urllib2.Request(
            self.URL % self.makeParams(),
            headers=self.headers
        )
        response = ClientCookie.urlopen(request)
        return response.read()

    def results(self):
        response = self.request()
        self.soup = BeautifulSoup(response)
        self.total = self._total()
        self.pages = self._pages()

        results = []

        data = self.soup.find("div", id="res").findAll("li", {"class": "g"})

        for i in xrange(0, len(data)):
            results.append({
                "title": data[i].find("h3").text,
                "description": data[i].find("div", {"class": "s"}).text,
            })
        return results

    def getParamsPage(self):
        url = self.soup.find("table", id="nav").find("a")["href"]
        parse = urlparse.urlparse(url)
        return dict(urlparse.parse_qsl(parse.query))

    def next(self):
        self._start += self.PER_PAGE
        return self.results()

    def prev(self):
        self._start -= self.PER_PAGE
        return self.results()

    def page(self, page):
        self._start = (page * self.PER_PAGE) - self.PER_PAGE
        return self.results()

    def makeFile(self):
        response = self.request()
        f = open("test.html", "w")
        f.write(response)
        f.close
