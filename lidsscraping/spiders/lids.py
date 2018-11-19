import scrapy
from lidsscraping.items import LidsscrapingItem
import re
import urlparse


class LidsSpider(scrapy.Spider):
    name = "lids_spider"
    allowed_domains = ['www.lids.com']
    start_url = 'https://www.lids.com/'

    header = {
        'User-Agent': 'Slackbot-LinkExpanding 1.0 (+https://api.slack.com/robots)'
    }

    def start_requests(self):
        yield scrapy.Request(self.start_url, callback=self.parse_categories,
                             headers=self.header, dont_filter=True)

    def parse_categories(self, response):
        categories = response.xpath('//ul[@class="sub-navigation-list"]'
                                    '/li[@class="yCmsComponent"]/a/@href').extract()
        for category in categories:
            category_link = urlparse.urljoin(response.url, category)
            yield scrapy.Request(category_link, callback=self.parse_pagination,
                                 headers=self.header, dont_filter=True)

    def parse_pagination(self, response):
        page_count = response.xpath('//ul[@class="pagination"]'
                                    '/li[contains(@class, "last-page")]/a/text()').extract()
        if page_count:
            page_count = page_count[0]
            for i in range(1, int(page_count) + 1):
                pagination_link = response.url + '?page=' + str(i)
                yield scrapy.Request(pagination_link, callback=self.parse_links, headers=self.header)

    def parse_links(self, response):
        links = response.xpath('//ul[contains(@class, "product-listing")]'
                               '//li[contains(@class, "product-item")]'
                               '/a[@class="thumb"]/@href').extract()
        for link in links:
            link = urlparse.urljoin(response.url, link)
            yield scrapy.Request(link, callback=self.parse_product, headers=self.header)

    def parse_product(self, response):
        item = LidsscrapingItem()

        item['url'] = response.url

        price = response.xpath('//span[@class="price"]/text()').extract()
        if price:
            item['price'] = price[0]

        name = response.xpath('//div[@class="product-details-name"]/*[@class="name"]/text()').extract()
        if name:
            item['name'] = name[0]

        sku = re.search('"sku":"(\d+)",', response.body).group(1)
        item['sku'] = sku

        availability = re.search('"availability":"(.*?)",', response.body).group(1)
        availability = availability.split('https://schema.org/')[1]
        item['availability'] = availability

        yield item
