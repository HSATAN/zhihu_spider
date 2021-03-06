# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html
import pymongo

from scrapy_exapmle.items import TopicItem, QuestionItem, AnswerItem, UserItem


class ScrapyExapmlePipeline(object):

    def process_item(self, item, spider):
        return item


class MongoPipeline(object):
    collection_name = 'topics'
    def process_item(self, item, spider):
        return item


class MongoPipeline(object):
    collection_name = 'topic'

    def __init__(self, mongo_uri, mongo_db):
        self.mongo_uri = mongo_uri
        self.mongo_db = mongo_db

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            mongo_uri=crawler.settings.get('MONGO_URI'),
            mongo_db=crawler.settings.get('MONGO_DATABASE', 'items')
        )

    def open_spider(self, spider):
        self.client = pymongo.MongoClient(self.mongo_uri, 27017)
        self.db = self.client[self.mongo_db]

    def close_spider(self, spider):
        self.client.close()

    def process_item(self, item, spider):
        if isinstance(item, TopicItem):
            self.collection_name = 'topic'
        elif isinstance(item, QuestionItem):
            self.collection_name = 'question'
        elif isinstance(item, AnswerItem):
            self.collection_name = 'answer'
        elif isinstance(item, UserItem):
            self.collection_name = 'user'
        else:
            self.collection_name = 'other'
        collection_name = self.collection_name
        self.db[collection_name].insert(dict(item))
        return item
