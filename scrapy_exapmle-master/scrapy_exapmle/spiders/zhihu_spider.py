# -*- coding: utf-8 -*-
import datetime
import json
import random

import re
import scrapy
from scrapy import FormRequest
from scrapy import Request
try:
    import cookielib
except BaseException:
    import http.cookiejar as cookielib


from scrapy_exapmle.spiders.login import login, isLogin
from scrapy_exapmle.items import TopicItem, QuestionItem, AnswerItem, UserItem


class ZhihuSpiderSpider(scrapy.Spider):
    name = "zhihu_spider"
    start_urls = [
        'https://www.zhihu.com/topics'
    ]

    user_agent_list = [
        'User-Agent:Mozilla/5.0 (Windows NT 10.0; WOW64; Trident/7.0; .NET4.0C; '
        '.NET4.0E; .NET CLR 2.0.50727; .NET CLR 3.0.30729; .NET CLR 3.5.30729; InfoPath.3; rv:11.0) like Gecko',
        'User-Agent:Opera/9.80 (Macintosh; Intel Mac OS X 10.6.8; U; en) Presto/2.8.131 Version/11.11',
        'User-Agent:Opera/9.80 (Windows NT 6.1; U; en) Presto/2.8.131 Version/11.11',
        'User-Agent: Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; Maxthon 2.0)',
        'User-Agent: Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; Avant Browser)',
        'User-Agent: Mozilla/5.0 (Windows NT 6.1; WOW64; rv:50.0) Gecko/20100101 Firefox/50.0',
        'User-Agent: Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) '
        'Chrome/54.0.2840.99 Safari/537.36',
        'User-Agent: Mozilla/5.0 (Windows NT 6.1; WOW64; Trident/7.0; rv:11.0) like Gecko']

    #

    def set_headers(self, url):
        # agent = "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:50.0) Gecko/20100101 Firefox/50.0"
        agent = self.user_agent_list[random.randint(0, 7)]
        headers={
        "Host": "www.zhihu.com",
         "User-Agent": agent,
        }
        headers['Referer'] = url
        return headers

    def start_requests(self):
        if isLogin():
            print('您已经登录')
        else:
            # account = input('请输入你的用户名\n>  ')
            # secret = input("请输入你的密码\n>  ")
            account = '15728689495'
            secret = 'q12345'
            login(secret, account)
        for url in self.start_urls:
            yield Request(
                url=url,
                headers=self.set_headers('https://www.zhihu.com'),
                cookies=cookielib.LWPCookieJar(filename='cookies')
            )

    def parse(self, response):
        topic_xpath_rule = '//li[@class="zm-topic-cat-item"]/a/text()'
        topic_names = response.selector.xpath(topic_xpath_rule).extract()

        topic_xpath_rule = '//li[@class="zm-topic-cat-item"]/@data-id'
        topic_ids = response.selector.xpath(topic_xpath_rule).extract()

        print("获取话题")
        for i in range(len(topic_ids)):
            params = {
                "topic_id": int(topic_ids[i]),
                "offset": 0,
                "hash_id": "d17ff3d503b2ebce086d2f3e98944d54"}
            yield FormRequest(
                url='https://www.zhihu.com/node/TopicsPlazzaListV2',
                method='POST',
                # headers=self.set_headers2('https://www.zhihu.com/topics'),
                headers=self.set_headers('https://www.zhihu.com/topics'),
                cookies=cookielib.LWPCookieJar(filename='cookies'),
                # formdata={'method': 'next', 'params': '{"topic_id":988,"offset":0,"hash_id":
                # "d17ff3d503b2ebce086d2f3e98944d54"}'},
                formdata={
                    'method': 'next',
                    'params': str(params).replace("\'", "\"").replace(" ", "")},
                callback=self.topic_parse,
                meta={'topic_name': topic_names[i]}
            )

    def topic_parse(self, response):
        if response.status in [400, 403, 302]:
            response.request.meta["change_proxy"] = True
            print(
                "答案抓取出现问题：{url}".format(
                    url=response.request.headers["Referer"]))
            pass
        else:
            # 名字，描述，链接，图片
            json_object = json.loads(response.body_as_unicode())
            json_content = ''.join(json_object['msg'])

            pattern = re.compile('<strong>(.*?)</strong>')
            subtopic_names = re.findall(pattern, json_content)

            pattern = re.compile('<a target="_blank" href="([^"]*)".*?>')
            subtopic_urls = re.findall(pattern, json_content)

            # 获取话题的精华回答
            for i in range(len(subtopic_names)):
                base_url = "https://www.zhihu.com" + subtopic_urls[i]
                yield Request(
                    url=base_url + "/top-answers",
                    headers=self.set_headers(base_url + "/hot"),
                    cookies=cookielib.LWPCookieJar(filename='cookies'),
                    callback=self.top_answers_parse,
                )

    # 爬取精华答案页面（获取答案链接）
    def top_answers_parse(self, response):
        if response.body in [
            "banned",
            b"{'reason': b'Bad Request', 'status': 400}",
            "{'reason': b'Bad Request', 'status': 400}",
        ]:
            req = response.request
            req.meta["change_proxy"] = True
            yield req
        else:
            # 获取topic和描述
            # https://www.zhihu.com/topic/19551137/top-answers
            end = response.url.rfind("/")
            topic_id = int(response.url[28:end])
            topic_name_xpath_rule = '//h1[@class="zm-editable-content"]/text()'
            topic_name = response.selector.xpath(
                topic_name_xpath_rule).extract_first()

            topic_description_xpath_rule = '//div[@id="zh-topic-desc"]/div[@class="zm-editable-content"]/text()'
            topic_description = response.selector.xpath(
                topic_description_xpath_rule).extract_first()

            # 存入数据库
            topic_item = TopicItem()
            topic_item['type'] = 'topic'
            topic_item['topic_id'] = topic_id
            topic_item['topic_name'] = topic_name
            topic_item['topic_description'] = topic_description
            yield topic_item

            answer_url_xpath_rule = '//div[@class="feed-item feed-item-hook folding"]/link/@href'
            answer_urls_temp = response.selector.xpath(
                answer_url_xpath_rule).extract()
            answer_urls = [
                "https://www.zhihu.com" +
                temp for temp in answer_urls_temp]  # 获取答案链接

            for answer_url in answer_urls:
                yield Request(
                    url=answer_url,
                    headers=self.set_headers(None),
                    cookies=cookielib.LWPCookieJar(filename='cookies'),
                    callback=self.answer_parse,
                    meta={'topic_id': topic_id}
                )

    def answer_parse(self, response):
        if response.body in [
            "banned",
            b"{'reason': b'Bad Request', 'status': 400}",
            "{'reason': b'Bad Request', 'status': 400}",
        ]:
            req = response.request
            req.meta["change_proxy"] = True
            yield req
        else:
            question_id = int(response.url[31:response.url.find('/answer/')])

            # 问题标题
            question_title_xpath_rule = '//h1[@class="QuestionHeader-title"]/text()'
            question_title_temp = response.selector.xpath(
                question_title_xpath_rule).extract_first()

            question_title = question_title_temp.replace("\n", "")

            # 问题内容
            question_content_xpath_rule = '//span[@class="RichText"]/text()'
            question_content_temp = response.selector.xpath(
                question_content_xpath_rule).extract_first()
            if question_content_temp is not None:
                question_content = question_content_temp.replace("\n", "")
                # print (question_content)
            else:
                question_content = None
            # 将问题存入数据库
            question_item = QuestionItem()
            question_item['type'] = 'question'
            question_item['question_id'] = question_id
            question_item['topic_id'] = response.meta['topic_id']
            question_item['question_title'] = question_title
            question_item['question_content'] = question_content
            yield question_item

            # 爬回答者链接
            answerer_url_xpath_rule = '//a[@class="UserLink-link"]/@href'
            answerer_url_temp = response.selector.xpath(
                answerer_url_xpath_rule).extract_first()
            if answerer_url_temp is None:
                answerer_url = None
            else:
                answerer_url = "https://www.zhihu.com" + \
                    answerer_url_temp + "/answers"  # 获取回答者链接

            # 答案id
            start = response.url.rfind("/") + 1
            answer_id = int(response.url[start:])

            # 答案赞数
            # answer_agreements_xpath_rule = '//span[@class="count"]/text()'
            answer_agreements_xpath_rule = '//button[@class="Button VoteButton VoteButton--up"]/text()'
            answer_agreements_temp = response.selector.xpath(
                answer_agreements_xpath_rule).extract_first()
            index = answer_agreements_temp.find('K')
            if index != -1:
                answer_agreements = int(answer_agreements_temp[:index]) * 1000
            else:
                answer_agreements = int(answer_agreements_temp)
            # print answer_agreements

            # 答案最后编辑时间
            answer_date_xpath_rule = '//span[@data-tooltip]/text()'
            answer_date_temp = response.selector.xpath(
                answer_date_xpath_rule).extract_first()
            # 注：由于爬的是高赞答案，时间都比较长，所以一般都满足"编辑于 2017-01-11"这个格式，正常答案不一定
            if answer_date_temp is None:
                answer_date = "null"  # 未处理解析发布后未编辑的文章时间
            else:
                answer_date = answer_date_temp[4:]

            text = response.body_as_unicode()
            # <span class="RichText CopyrightRichText-richText" itemprop="text" >
            pattern = re.compile(
                '<span class="RichText CopyrightRichText-richText".+?>(.+?)</span>')  # 注意回车！
            result_temp = pattern.findall(text, re.S)
            if len(result_temp) > 0:
                answer_content = result_temp[0].replace("<br>", "  ")  # 解析到的答案还未进一步处理
            else:
                answer_content = "未解析到"

            # 将答案存入数据库
            answer_item = AnswerItem()
            answer_item['type'] = 'answer'
            answer_item['question_id'] = question_id             # 所回答的问题的id
            answer_item['answer_id'] = answer_id                 # 答案id
            answer_item['answer_content'] = answer_content       # 答案内容
            answer_item['answer_agreements'] = answer_agreements  # 答案赞数
            answer_item['answer_edit_time'] = answer_date        # 编辑时间
            yield answer_item

            yield Request(
                url=answerer_url,
                # headers = self.set_headers3(response.url),
                headers=self.set_headers(response.url),
                cookies=cookielib.LWPCookieJar(filename='cookies'),
                callback=self.user_parse,
                meta={'answer_item': answer_item}
            )

    def user_parse(self, response):
        if response.body in [
            "banned",
            b"{'reason': b'Bad Request', 'status': 400}",
            "{'reason': b'Bad Request', 'status': 400}",
        ]:
            req = response.request
            req.meta["change_proxy"] = True
            yield req
        else:
            # 获取user数据
            user_name_xpath_rule = '//span[@class="ProfileHeader-name"]/text()'
            user_name = response.selector.xpath(
                user_name_xpath_rule).extract_first()
            # print (user_name)

            short_description_xpath_rule = '//span[@class="RichText ProfileHeader-headline"]/text()'
            short_description = response.selector.xpath(
                short_description_xpath_rule).extract_first()

            user_avatar_xpath_rule = '//img[@class="Avatar Avatar--large UserAvatar-inner"]/@src'
            user_avatar = response.selector.xpath(
                user_avatar_xpath_rule).extract_first()

            user_gender_xpath_rule = '//svg[@class="Icon Icon--male"]'
            if response.selector.xpath(
                    user_gender_xpath_rule).extract_first() is None:
                user_gender = 0
            else:
                user_gender = 1

            data_xpath_rule = '//div[@id="data"]/@data-state'
            data = response.selector.xpath(data_xpath_rule).extract_first()

            pattern = re.compile(r'description":"(.+?)"')
            result = pattern.findall(data)
            user_description = result[0] if len(
                result) > 0 else None   # 简介，有链接的会取不全，还没解决

            pattern = re.compile(r'job":{"name":"(.+?)"')
            result = pattern.findall(data)
            user_job = result[0] if len(result) > 0 else None           # 工作

            pattern = re.compile(r'business":{"name":"(.+?)"')
            result = pattern.findall(data)
            user_business = result[0] if len(result) > 0 else None      # 行业

            pattern = re.compile(r'locations":\[{"name":"(.+?)"')
            result = pattern.findall(data)
            user_location = result[0] if len(result) > 0 else None      # 所在地

            # 将用户存入数据库
            user_item = UserItem()
            user_item['type'] = 'user'
            user_item['user_name'] = user_name           # 名字
            user_item['user_avatar'] = user_avatar       # 头像
            user_item['user_gender'] = user_gender       # 性别
            user_item['user_short_description'] = short_description  # 一句话描述
            user_item['user_long_description'] = user_description    # 个人简介
            user_item['user_location'] = user_location   # 居住地
            user_item['user_job'] = user_job             # 工作
            user_item['user_business'] = user_business   # 行业
            yield user_item
