#!/usr/bin/env python
#-*- coding:utf-8 -*-

import webbrowser
import math
import urllib2
import urllib
import urlparse
import re
import os
import ClientCookie
from urllib import urlencode
from BeautifulSoup import BeautifulSoup
from datetime import datetime
from dateutil.relativedelta import relativedelta

MONTHS = {
    "jan.": '01',
    "fev.": '02',
    "mar.": '03',
    "abr.": '04',
    "mai.": '05',
    "jun.": '06',
    "jul.": '07',
    "ago.": '08',
    "set.": '09',
    "out.": '10',
    "nov.": '11',
    "dez.": '12',
}

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
        "tbm": "nws",
        "tbs": "sbd:1",
    }
    _results_hash = []
    _results = []

    _start = 0

    def __init__(self, query, begin_date=datetime.strptime("01/01/2011", "%d/%m/%Y"), end_date=datetime.now(), part=1):
        self.query = query
        self.begin_date = begin_date
        self.end_date = end_date
        self.part = part
        self.loaded = self.loadStats()

    def loadStats(self):
        if os.path.exists("stats.txt") and os.path.exists("results_hash.txt") and os.path.exists("results.txt"):
            f = open("stats.txt")
            content = f.readlines()
            self._dateranges = eval(content[0])
            self._daterange = content[1][:-1]
            self._page = eval(content[2])
            f.close()

            f = open("results_hash.txt")
            self._results_hash = eval(f.read())
            f.close()

            f = open("results.txt")
            self._results = eval(f.read())
            f.close()

#            return True
        return False

    def _total(self, soup):
        total = soup.find("div", id="subform_ctrl").findAll("div")[1].string
        try:
            num = re.search(r"\d\S+", total).group(0)
            if num.find(".") > 0:
                num = num.replace(".", "")
            return int(num)
        except:
            return 0

    def _pages(self, soup):
        # pages = len(soup.find("table", id="nav").findAll("td")) - 2
        start = 1
        # if pages >= self.PER_PAGE:
        results = self._total(soup)
        pages = results / self.PER_PAGE
#        if self.loaded and self._page:
#            start = self._page
#            self._page = None
        return range(start, pages + 1)

    def makeParams(self):
        data = self.params
        if self._start != 0:
            data.update(self.getParamsPage())
        return urlencode(data)

    def request(self, daterange):
        self.params["q"] = self.query + daterange
        url = self.URL % self.makeParams()
        request = urllib2.Request(
            url,
            headers=self.headers
        )
        response = ClientCookie.urlopen(request)
        return response.read()

    def results(self):
        results = []

#        try:
        dateranges = self.makeRange()
        for daterange in dateranges:  # [:1]:
            print "RANGE ---> %s" % daterange
            response = self.request(daterange)
            soup = BeautifulSoup(response)
            self.makeFile(daterange, soup=soup, name=daterange.strip())
            self.soup = soup
            pages = self._pages(soup)
            date = self._real_parts[dateranges.index(daterange)][0]

            for page in pages:  # [0:5]:
                print "Pagina %s" % page
                results += self.parseResultsOfPage(soup, date.strftime("%d/%m/%Y"))
                self.next()
                response = self.request(daterange)
                soup = BeautifulSoup(response)
                self.soup = soup
#        except Exception, e:
#            print "ERROR ----> %s" % e
#            self.resultsToFile(dateranges, daterange, page, results)

        return results

    def parseResultsOfPage(self, soup, _date):
        results = []
        self._results_hash = []

        data = soup.find("div", id="res").findAll("li", {"class": "g"})

        for i in xrange(0, len(data)):
            try:
                url = data[i].find("td", {"valign": "top"}).find("h3").find("a")["href"]
                url = url.split("&sa")[0]
            except Exception:
                url = data[i].find("h3").find("a")["href"]

            try:
                title = data[i].find("td", {"valign": "top"}).find("h3").text
            except Exception:
                title = data[i].find("h3").text

            if not hash(title) in self._results_hash:
                try:
                    description = data[i].find("td", {"valign": "top"}).find("div").text
                except Exception:
                    description = data[i].find("div").text

                if url.startswith("/url?q="):
                    url = url.replace("/url?q=", "")

                try:
                    source, date = data[i].find("td", {"valign": "top"}).find("span", {"class": "f"}).text.split('-')
                    if date.strip() == u'31 dez. 1969':
                        date = _date
                    else:
                        if date.endswith(u"atrás"):
                            now = datetime.now()
                            quantity, time, past = date.strip().split(" ")
                            quantity = int(quantity)
                            if time == "horas":
                                date = (now - relativedelta(hours=quantity)).strftime("%d/%m/%Y")
                            elif time == "minutos":
                                date = (now - relativedelta(minutes=quantity)).strftime("%d/%m/%Y")
                        else:
                            day, month, year = date.strip().split(" ")
                            date = "%s/%s/%s" % (day, MONTHS[month], year)

                except Exception, e:
                    print "----------------", e
                    source = ""
                    date = _date

                results.append({
                    "title": title,
                    "url": url,
                    "description": description,
                    "source": source.strip(),
                    "date": date.strip()
                })
                self._results_hash.append(hash(title))
        return results

    def resultsToFile(self, dateranges, daterange, page, results):
        f = file("stats.txt", "w")
        f.write(str(dateranges) + "\n")
        f.write(str(daterange) + "\n")
        f.write(str(page) + "\n")
        f.close()

        f = file("results_hash.txt", "w")
        f.write(str(self._results_hash))
        f.close()

        f = file("results.txt", "w")
        f.write(str(self._results + results))
        f.close()

    def getParamsPage(self):
        url = self.soup.find("table", id="nav").find("a")["href"]
        parse = urlparse.urlparse(url)
        data = dict(urlparse.parse_qsl(parse.query))
        data.pop("q")
        return data

    def next(self):
        self._start += self.PER_PAGE
        return self._start

    def prev(self):
        self._start -= self.PER_PAGE
        return self._start

    def page(self, page):
        self._start = (page * self.PER_PAGE) - self.PER_PAGE
        return self.results()

    def makeFile(self, daterange, soup=None, name=None, data=None):
        if soup is None:
            if not data is None:
                response = data
            else:
                response = self.request(daterange)
            f = open("test.html", "w")
            f.write(BeautifulSoup(response).prettify())
            f.close()
        else:
            f = open("%s.html" % name, "w")
            f.write(soup.prettify())
            f.close()

    def toJulianDate(self, DD=0, MM=0, YY=0):
        GGG = 1
        if (YY <= 1585):
            GGG = 0

        JD = -1 * math.floor(7 * (math.floor((MM + 9) / 12) + YY) / 4)
        S = 1

        if (MM - 9) < 0:
            S = -1

        A = abs(MM - 9)
        J1 = math.floor(YY + S * math.floor(A / 7))
        J1 = -1 * math.floor((math.floor(J1 / 100) + 1) * 3 / 4)
        JD = JD + math.floor(275 * MM / 9) + DD + (GGG * J1)
        JD = JD + 1721027 + 2 * GGG + 367 * YY

        if (DD == 0 and MM == 0 and YY == 0):
            raise RuntimeError("Please enter a meaningful date!")
        else:
            return int(JD)

    def makeRange(self):
        if self.loaded:
            return self._dateranges[self._dateranges.index(self._daterange):]
        begin_date = self.begin_date
        end_date = begin_date + relativedelta(months=+self.part)
        parts = []
        self._real_parts = []

        while end_date < self.end_date:
            parts.append(self.range(begin_date, end_date))
            self._real_parts.append((begin_date, end_date))
            begin_date = end_date
            end_date = begin_date + relativedelta(months=+self.part)
        parts.append(self.range(begin_date, self.end_date))
        self._real_parts.append((begin_date, end_date))
        parts.reverse()
        return parts

    def range(self, begin_date=None, end_date=None):
        if begin_date is None:
            begin_date = self.begin_date

        if end_date is None:
            end_date = self.end_date

        if self.begin_date is None or self.end_date is None:
            return ""
        return " daterange:%s-%s" % (
            self.toJulianDate(
                begin_date.day,
                begin_date.month,
                begin_date.year
            ),
            self.toJulianDate(
                end_date.day,
                end_date.month,
                end_date.year
            )
        )