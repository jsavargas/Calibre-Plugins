#!/usr/bin/env python
# vim:fileencoding=UTF-8:ts=4:sw=4:sta:et:sts=4:ai
from __future__ import (unicode_literals, division, absolute_import,
                        print_function)

__license__   = 'GPL v3'
__copyright__ = '2011, Grant Drake <grant.drake@gmail.com>, 2016-2020 updates by David Forrester <davidfor@internode.on.net>'
__docformat__ = 'restructuredtext en'

import socket, re, datetime
from collections import OrderedDict
from threading import Thread
import six
from six import text_type as unicode

from lxml.html import fromstring, tostring

from calibre.ebooks.metadata.book.base import Metadata
from calibre.library.comments import sanitize_comments_html
from calibre.utils.cleantext import clean_ascii_chars
from calibre.utils.localization import canonicalize_lang

import calibre_plugins.goodreads.config as cfg

def clean_html(raw):
    from calibre.ebooks.chardet import xml_to_unicode
    from calibre.utils.cleantext import clean_ascii_chars
    return clean_ascii_chars(xml_to_unicode(raw, strip_encoding_pats=True,
                                resolve_entities=True, assume_utf8=True)[0])

def parse_html(raw):
    raw = clean_html(raw)
    from html5_parser import parse
    return parse(raw)


class Worker(Thread): # Get details

    '''
    Get book details from Goodreads book page in a separate thread
    '''

    def __init__(self, url, result_queue, browser, log, relevance, plugin, timeout=20):
        Thread.__init__(self)
        self.daemon = True
        self.url, self.result_queue = url, result_queue
        self.log, self.timeout = log, timeout
        self.relevance, self.plugin = relevance, plugin
        self.browser = browser.clone_browser()
        self.cover_url = self.goodreads_id = self.isbn = None

        lm = {
                'eng': ('English', 'Englisch'),
                'fra': ('French', 'Français'),
                'ita': ('Italian', 'Italiano'),
                'dut': ('Dutch',),
                'deu': ('German', 'Deutsch'),
                'spa': ('Spanish', 'Espa\xf1ol', 'Espaniol'),
                'jpn': ('Japanese', u'日本語'),
                'por': ('Portuguese', 'Português'),
                }
        self.lang_map = {}
        for code, names in lm.items():
            for name in names:
                self.lang_map[name] = code

    def run(self):
        try:
            self.get_details()
        except:
            self.log.exception('get_details failed for url: %r'%self.url)

    def get_details(self):
        try:
            self.log.info('Goodreads book url: %r'%self.url)
            raw = self.browser.open_novisit(self.url, timeout=self.timeout).read().strip()
        except Exception as e:
            if callable(getattr(e, 'getcode', None)) and \
                    e.getcode() == 404:
                self.log.error('URL malformed: %r'%self.url)
                return
            attr = getattr(e, 'args', [None])
            attr = attr if attr else [None]
            if isinstance(attr[0], socket.timeout):
                msg = 'Goodreads timed out. Try again later.'
                self.log.error(msg)
            else:
                msg = 'Failed to make details query: %r'%self.url
                self.log.exception(msg)
            return

        raw = raw.decode('utf-8', errors='replace')
        #open('c:\\goodreads.html', 'wb').write(raw)

        if '<title>404 - ' in raw:
            self.log.error('URL malformed: %r'%self.url)
            return

        try:
#             from calibre.ebooks.chardet import xml_to_unicode
#             raw = clean_ascii_chars(xml_to_unicode(raw,
#                                                strip_encoding_pats=True, resolve_entities=True)[0])
#             root = fromstring(raw)
            root = parse_html(raw)
        except:
            msg = 'Failed to parse goodreads details page: %r'%self.url
            self.log.exception(msg)
            return

        try:
            # Look at the <title> attribute for page to make sure that we were actually returned
            # a details page for a book. If the user had specified an invalid ISBN, then the results
            # page will just do a textual search.
            title_node = root.xpath('//title')
            if title_node:
                page_title = title_node[0].text.strip()
                if page_title is None or page_title.find('search results for') != -1:
                    self.log.error('Failed to see search results in page title: %r'%self.url)
                    return
        except:
            msg = 'Failed to read goodreads page title: %r'%self.url
            self.log.exception(msg)
            return

        errmsg = root.xpath('//*[@id="errorMessage"]')
        if errmsg:
            msg = 'Failed to parse goodreads details page: %r'%self.url
            msg += tostring(errmsg, method='text', encoding=unicode).strip()
            self.log.error(msg)
            return

        self.parse_details(root)

    def parse_details(self, root):
#         self.log.error("parse_details: root='%s'" % root)
#         self.log.error("parse_details: root='%s'" % tostring(root))
        try:
            goodreads_id = self.parse_goodreads_id(self.url)
        except:
            self.log.exception('Error parsing goodreads id for url: %r'%self.url)
            goodreads_id = None

        try:
            title = self.parse_title(root)
        except:
            self.log.exception('Error parsing title for url: %r'%self.url)
            title = None

        try:
            authors = self.parse_authors(root)
        except:
            self.log.exception('Error parsing authors for url: %r'%self.url)
            authors = []

        if not title or not authors or not goodreads_id:
            self.log.error('Could not find title/authors/goodreads id for %r'%self.url)
            self.log.error('Goodreads: %r Title: %r Authors: %r'%(goodreads_id, title,
                authors))
            return

        mi = Metadata(title, authors)
        self.log.info('parse_details - goodreads_id: {0}, mi: {1}'.format(goodreads_id,mi))
        mi.set_identifier('goodreads', goodreads_id)
        self.goodreads_id = goodreads_id

        try:
            (series, series_index) = self.parse_series(root)
#             self.log.info("parse_series - series='%s', series_index='%s'" % (series, series_index))
            if series is not None:
#                 self.log.info("setting series info - series='%s', series_index='%s'" % (series, series_index))
                mi.series = series
                mi.series_index = series_index
        except:
            self.log.exception('Error parsing series for url: %r'%self.url)

        try:
            isbn = self.parse_isbn(root)
            if isbn is not None:
                self.isbn = mi.isbn = isbn
        except:
            self.log.exception('Error parsing ISBN for url: %r'%self.url)

        try:
            get_asin = cfg.plugin_prefs[cfg.STORE_NAME][cfg.KEY_GET_ASIN]
            if get_asin is not None:
                asin = self.parse_asin(root)
                if asin is not None:
                    mi.set_identifier('amazon', asin)
        except:
            self.log.exception('Error parsing ASIN for url: %r'%self.url)

        try:
            mi.rating = self.parse_rating(root)
        except:
            self.log.exception('Error parsing ratings for url: %r'%self.url)

        try:
            mi.comments = self.parse_comments(root)
        except:
            self.log.exception('Error parsing comments for url: %r'%self.url)

        try:
            self.cover_url = self.parse_cover(root)
        except:
            self.log.exception('Error parsing cover for url: %r'%self.url)
        mi.has_cover = bool(self.cover_url)

        try:
            tags = self.parse_tags(root)
            if tags is not None:
                mi.tags = tags
        except:
            self.log.exception('Error parsing tags for url: %r'%self.url)

        try:
            print(root)

            ## calibre-customize -b .
            mi.publisher, mi.pubdate = self.parse_publisher_and_date(root)


            mi.set('#gr1',8.8)
            mi.set('#gr_ratingss',9.9)


            mi.publisher = f"{mi.publisher} | {self.parse_rating_withcount(root)}" 


            self.log.info("publisher: ", mi.publisher)
        except:
            self.log.exception('Error parsing publisher (i.e. goodreads ratings/reviews) for url: %r'%self.url)

        try:
            lang = self._parse_language(root)
            if lang is not None:
                mi.language = lang
        except:
            self.log.exception('Error parsing language for url: %r'%self.url)

        mi.source_relevance = self.relevance

        if self.goodreads_id is not None:
            if self.isbn is not None:
                self.plugin.cache_isbn_to_identifier(self.isbn, self.goodreads_id)
            if self.cover_url is not None:
                self.plugin.cache_identifier_to_cover_url(self.goodreads_id,
                        self.cover_url)

        self.plugin.clean_downloaded_metadata(mi)

        self.result_queue.put(mi)

    def parse_goodreads_id(self, url):
        return re.search('/show/(\d+)', url).groups(0)[0]

    def parse_title(self, root):
        title_node = root.xpath('//div[@id="metacol"]/h1[@id="bookTitle"]')
        if not title_node:
            return None
        title_text = title_node[0].text.strip()
        self.log.error("parse_title:: title_text='%s'" % title_text)
        return title_text

    def parse_series(self, root):
#         self.log.error("parse_series: root='%s'" % tostring(root))
        series_node = root.xpath('//div[@id="metacol"]/h2[@id="bookSeries"]/a')
#         self.log.error("parse_series: series_node='%s'" % series_node)
#         self.log.error("parse_series: len(series_node)='%s'" % len(series_node))
#         self.log.error("parse_series: series_node='%s'" % repr(series_node))
        self.log.error("parse_series: series_node[0]='%s'" % tostring(series_node[0]))
#         self.log.error("parse_series: series_node[0].text='%s'" % series_node[0].text)
        if not series_node:
            return (None, None)
        series_text = series_node[0].text.strip()
        self.log.error("parse_series: series_text='%s'" % series_text)
        if not series_text:
            return (None, None)
        # Series can look like:
        # "(Series Name #1-3)"
        # "(Series Name #1)"
        # "(Series Name #05)"
        # "(Series Name 0.5)"
        self.log.error("parse_series: series_text='%s'" % series_text)
        series_text = series_text.strip('(').strip(')')
        series = series_text
        series_index = None
#         if series_text[0] == '(':
#             series_text = series_text[1:]
#         if series_text[-1] == ')':
#             series_text = series_text[:-1]
        self.log.error("parse_series: series_text after stripping parantheses='%s'" % series_text)
        series_split = series_text.split(' ')
        if len(series_split) > 1:
            series_index_str = series_split[-1]
            series_name = series_text[:-(len(series_index_str) + 1)]
            self.log.error("parse_series: series_name='%s', series_index_str='%s'" % (series_name, series_index_str))
            series_index_str = series_index_str.strip('#')
            if series_index_str.find('-'):
                # The series is specified as 1-3, 1-7 etc.
                # In future we may offer config options to decide what to do,
                # such as "Use start number", "Use value xxx" like 0 etc.
                # For now will just take the start number and use that
                series_index = series_index_str.partition('-')[0].strip()
            else:
                series_index = series_index_str
            try:
                series_index = float(series_index)
                series = series_name
            except ValueError:
                self.log.error("parse_series: exception converting series_index: %s" % series_index)
                # We have a series index which isn't really a series index
        self.log.error("parse_series: returning - series_name='%s', series_index='%s'" % (series_name, series_index))
        return (series, series_index)

    def parse_authors(self, root):
        # Build a dict of authors with their contribution if any in values
        div_authors = root.xpath('//div[@id="metacol"]/div[@id="bookAuthors"]')
        if not div_authors:
            return
        authors_html = tostring(div_authors[0], method='text', encoding=unicode).replace('\n','').strip()
        if authors_html.startswith('by'):
            authors_html = authors_html[2:]
        authors_type_map = OrderedDict()
        for a in authors_html.split(','):
            self.log.info('parse_authors - author: %s'%a)
            author = a.strip()
            if author.startswith('more…'):
                author = author[5:]
            elif author.endswith('…less'):
                author = author[:-5]
            author_parts = author.strip().split('(')
            if len(author_parts) == 1:
                authors_type_map[author_parts[0]] = ''
            else:
                authors_type_map[author_parts[0]] = author_parts[1][:-1]
        # User either requests all authors, or only the primary authors (latter is the default)
        # If only primary authors, only bring them in if:
        # 1. They have no author type specified
        # 2. They have an author type of 'Goodreads Author'
        # 3. There are no authors from 1&2 and they have an author type of 'Editor'
        get_all_authors = cfg.plugin_prefs[cfg.STORE_NAME][cfg.KEY_GET_ALL_AUTHORS]
        authors = []
        valid_contrib = None
        for a, contrib in authors_type_map.items():
            self.log.info('parse_authors - author: %s'%a)
            if get_all_authors:
                authors.append(a)
            else:
                if not contrib or contrib == 'Goodreads Author':
                    authors.append(a)
                elif len(authors) == 0:
                    authors.append(a)
                    valid_contrib = contrib
                elif contrib == valid_contrib:
                    authors.append(a)
                else:
                    break
        return authors

    def parse_rating(self, root):
#         rating_node = root.xpath('//div[@id="metacol"]/div[@id="bookMeta"]/span[@class="value rating"]/span')
        rating_node = root.xpath('//span[@itemprop="ratingValue"]')
#         rating_node = root.xpath('//div[@id="metacol"]/div[@id="details"]/div[@class="buttons"]/div[@id="bookDataBox"]/div/div[@itemprop="inLanguage"]')
        self.log.info("parse_rating: rating_node=", rating_node)
        if rating_node and len(rating_node) > 0:
            try:
                self.log.info("parse_rating: have rating node - rating_node[0].text=", rating_node[0].text)
                rating_text = rating_node[0].text
                rating_value = float(rating_text)
                return rating_value
            except:
                self.log.info("parse_rating: Exception getting rating")
                import traceback
                traceback.print_stack()
                return None

    def parse_comments(self, root):
        # Look for description in a second span that gets expanded when interactively displayed [@id="display:none"]
        description_node = root.xpath('//div[@id="descriptionContainer"]/div[@id="description"]/span')
        if description_node:
            desc = description_node[0] if len(description_node) == 1 else description_node[1]
            less_link = desc.xpath('a[@class="actionLinkLite"]')
            if less_link is not None and len(less_link):
                desc.remove(less_link[0])
            comments = tostring(desc, method='html', encoding=unicode).strip()
            while comments.find('  ') >= 0:
                comments = comments.replace('  ',' ')
            comments = sanitize_comments_html(comments)
            return comments

    def parse_cover(self, root):
        imgcol_node = root.xpath('//div[@class="bookCoverPrimary"]/a/img/@src')
        if imgcol_node:
            img_url = imgcol_node[0]
            # Unfortunately Goodreads sometimes have broken links so we need to do
            # an additional request to see if the URL actually exists
            info = self.browser.open_novisit(img_url, timeout=self.timeout).info()
            if int(info.get('Content-Length')) > 1000:
                return img_url
            else:
                self.log.warning('Broken image for url: %s'%img_url)

    def parse_isbn(self, root):
        data_nodes = root.xpath('//div[@id="metacol"]/div[@id="details"]/div[@class="buttons"]/div[@id="bookDataBox"]/div')
#         self.log.info("parse_isbn: data_nodes=", data_nodes)
        if data_nodes:
            for data_node in data_nodes:
                id_type = tostring(data_node, method='text', encoding=unicode).strip()
#                 self.log.info("parse_isbn: id_type=", id_type)
                if 'ISBN' in id_type:
#                     self.log.info("parse_isbn: Have ISBN node=", tostring(data_node))
                    # The first line does not contain an ISBN or an ISBN13 so check the next line
                    isbn_title_node = data_node.xpath('./div')[0]
                    id_type = tostring(isbn_title_node, method='text', encoding=unicode).strip()
#                     self.log.info("parse_isbn: id_type=", id_type)
                    if id_type == 'ISBN':
                        isbn10_data = tostring(data_node.xpath('./div')[1], method='text', encoding=unicode).strip()
                        isbn13_pos = isbn10_data.find('ISBN13:')
                        if isbn13_pos == -1:
                            return isbn10_data[:10]
                        else:
                            return isbn10_data[isbn13_pos+8:isbn13_pos+21]
                    elif id_type == 'ISBN13':
                        # We have just an ISBN13, without an ISBN10
                        return tostring(data_node.xpath('./div')[1], method='text', encoding=unicode).strip()
                    break

#         isbn_node = root.xpath('//div[@id="metacol"]/div[@id="details"]/div[@class="buttons"]/div[@id="bookDataBox"]/div[1]/div')
#         self.log.info("parse_isbn: isbn_node=", isbn_node)
#         if isbn_node:
#             id_type = tostring(isbn_node[0], method='text', encoding=unicode).strip()
#             self.log.info("parse_isbn: id_type=", id_type)
# #             id_type = tostring(isbn_node[1], method='text', encoding=unicode).strip()
# #             self.log.info("parse_isbn: id_type=", id_type)
#             if 'ISBN' not in id_type:
#                 # The first line does not contain an ISBN or an ISBN13 so check the next line
#                 isbn_node = root.xpath('//div[@id="metacol"]/div[@id="details"]/div[@class="buttons"]/div[@id="bookDataBox"]/div[2]/div')
#                 id_type = tostring(isbn_node[0], method='text', encoding=unicode).strip()
#             if id_type == 'ISBN':
#                 isbn10_data = tostring(isbn_node[1], method='text', encoding=unicode).strip()
#                 isbn13_pos = isbn10_data.find('ISBN13:')
#                 if isbn13_pos == -1:
#                     return isbn10_data[:10]
#                 else:
#                     return isbn10_data[isbn13_pos+8:isbn13_pos+21]
#             elif id_type == 'ISBN13':
#                 # We have just an ISBN13, without an ISBN10
#                 return tostring(isbn_node[1], method='text', encoding=unicode).strip()

    def parse_asin(self, root):
        data_nodes = root.xpath('//div[@id="metacol"]/div[@id="details"]/div[@class="buttons"]/div[@id="bookDataBox"]/div')
#         self.log.info("parse_asin: data_nodes=", data_nodes)
        if data_nodes:
            for data_node in data_nodes:
                id_type = tostring(data_node, method='text', encoding=unicode).strip()
#                 self.log.info("parse_isbn: id_type=", id_type)
                if 'ASIN' in id_type:
#                     self.log.info("parse_asin: Have ISBN node=", tostring(data_node))
                    # The first line does not contain an ISBN or an ISBN13 so check the next line
                    asin_title_node = data_node.xpath('./div')[0]
                    id_type = tostring(asin_title_node, method='text', encoding=unicode).strip()
#                     self.log.info("parse_asin: id_type=", id_type)
                    if id_type == 'ASIN':
                        return tostring(data_node.xpath('./div')[1], method='text', encoding=unicode).strip()
                    break

#         asin_node = root.xpath('//div[@id="metacol"]/div[@id="details"]/div[@class="buttons"]/div[@id="bookDataBox"]/div[1]/div')
#         if asin_node:
#             id_type = tostring(asin_node[0], method='text', encoding=unicode).strip()
#             if id_type != 'ASIN':
#                 # The first line does not contain ASIN so check the next line
#                 asin_node = root.xpath('//div[@id="metacol"]/div[@id="details"]/div[@class="buttons"]/div[@id="bookDataBox"]/div[2]/div')
#                 id_type = tostring(asin_node[0], method='text', encoding=unicode).strip()
#             if id_type == 'ASIN':
#                 asin_data = tostring(asin_node[1], method='text', encoding=unicode).strip()
#                 return asin_data

    def parse_publisher_and_date(self, root):
        publisher = None
        pub_date = None
        publisher_node = root.xpath('//div[@id="metacol"]/div[@id="details"]/div[2]')
        if publisher_node:
            # Publisher is specified within the div above with variations of:
            #  Published December 2003 by Books On Tape <nobr class="greyText">(first published 1982)</nobr>
            #  Published June 30th 2010
            # Note that the date could be "2003", "December 2003" or "December 10th 2003"
            publisher_node_text = tostring(publisher_node[0], method='text', encoding=unicode)
            # See if we can find the publisher name
            pub_text_parts = publisher_node_text.partition(' by ')
            if pub_text_parts[2]:
                publisher = pub_text_parts[2].strip()
                if '(first' in publisher:
                    # The publisher name is followed by (first published xxx) so strip that off
                    publisher = publisher.rpartition('(first')[0].strip()

            # Now look for the pubdate. There should always be one at start of the string
            pubdate_text_match = re.search('Published[\n\s]*([\w\s]+)', pub_text_parts[0].strip())
            pubdate_text = None
            if pubdate_text_match is not None:
                pubdate_text = pubdate_text_match.groups(0)[0]
            # If we have a first published section of text use that for the date.
            if '(first' in publisher_node_text:
                # For the publication date we will use first published date
                # Note this date could be just a year, or it could be monthname year
                pubdate_text_match = re.search('.*\(first published ([\w\s]+)', publisher_node_text)
                if pubdate_text_match is not None:
                    first_pubdate_text = pubdate_text_match.groups(0)[0]
                    if pubdate_text and first_pubdate_text[-4:] == pubdate_text[-4:]:
                        # We have same years, use the first date as it could be more accurate
                        pass
                    else:
                        pubdate_text = first_pubdate_text
            if pubdate_text:
                pub_date = self._convert_date_text(pubdate_text)
        return (publisher, pub_date)

    def parse_tags(self, root):
        # Goodreads does not have "tags", but it does have Genres (wrapper around popular shelves)
        # We will use those as tags (with a bit of massaging)
        genres_node = root.xpath('//div[@class="stacked"]/div/div/div[contains(@class, "bigBoxContent")]/div/div[@class="left"]')
        #self.log.info("Parsing tags")
        if genres_node:
            #self.log.info("Found genres_node")
            genre_tags = list()
            for genre_node in genres_node:
                sub_genre_nodes = genre_node.xpath('a')
                genre_tags_list = [sgn.text.strip() for sgn in sub_genre_nodes]
                #self.log.info("Found genres_tags list:", genre_tags_list)
                if genre_tags_list:
                    genre_tags.append(' > '.join(genre_tags_list))
            calibre_tags = self._convert_genres_to_calibre_tags(genre_tags)
            if len(calibre_tags) > 0:
                return calibre_tags

    def _convert_genres_to_calibre_tags(self, genre_tags):
        # for each tag, add if we have a dictionary lookup
        calibre_tag_lookup = cfg.plugin_prefs[cfg.STORE_NAME][cfg.KEY_GENRE_MAPPINGS]
        calibre_tag_map = dict((k.lower(),v) for (k,v) in calibre_tag_lookup.items())
        tags_to_add = list()
        for genre_tag in genre_tags:
            tags = calibre_tag_map.get(genre_tag.lower(), None)
            if tags:
                for tag in tags:
                    if tag not in tags_to_add:
                        tags_to_add.append(tag)
        return list(tags_to_add)

    def _convert_date_text(self, date_text):
        # Note that the date text could be "2003", "December 2003" or "December 10th 2003"
        year = int(date_text[-4:])
        month = 1
        day = 1
        if len(date_text) > 4:
            text_parts = date_text[:len(date_text)-5].partition(' ')
            month_name = text_parts[0]
            # Need to convert the month name into a numeric value
            # For now I am "assuming" the Goodreads website only displays in English
            # If it doesn't will just fallback to assuming January
            month_dict = {"January":1, "February":2, "March":3, "April":4, "May":5, "June":6,
                "July":7, "August":8, "September":9, "October":10, "November":11, "December":12}
            month = month_dict.get(month_name, 1)
            if len(text_parts[2]) > 0:
                day = int(re.match('([0-9]+)', text_parts[2]).groups(0)[0])
        from calibre.utils.date import utc_tz
        return datetime.datetime(year, month, day, tzinfo=utc_tz)

    def _parse_language(self, root):
        lang_node = root.xpath('//div[@id="metacol"]/div[@id="details"]/div[@class="buttons"]/div[@id="bookDataBox"]/div/div[@itemprop="inLanguage"]')
        if lang_node:
            self.log.info("_parse_language: Have language node")
            raw = tostring(lang_node[0], method='text', encoding=unicode).strip()
            self.log.info("_parse_language: raw=", raw)
            ans = self.lang_map.get(raw, None)
            self.log.info("_parse_language: ans=", ans)
            if ans:
                return ans
            ans = canonicalize_lang(raw)
            self.log.info("_parse_language: ans=", ans)
            if ans:
                return ans

    def parse_rating_withcount(self, root):
        rating_node = root.xpath('//span[@itemprop="ratingValue"]')
        rating_count = root.xpath('//*[@itemprop="ratingCount"]/@content')
        
        self.log.info("parse_rating_withcount: rating_node=", rating_node)
        self.log.info("parse_rating_withcount: rating_count=", rating_count)
        if rating_node and len(rating_node) > 0:
            try:
                self.log.info("parse_rating_withcount: have rating node - rating_node[0].text.strip()=", rating_node[0].text.strip())
                self.log.info("parse_rating_withcount: have rating count - rating_count[0]=", rating_count[0])
                rating_text = "Rating: " + rating_node[0].text.strip() + " | Reviews: " + rating_count[0]
                self.log.info("parse_rating_withcount: rating_text=", rating_text)
                return rating_text
            except:
                self.log.info("parse_rating_withcount: Exception getting rating")
                import traceback
                traceback.print_stack()
                return None
                