# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html


from scrapy import Field, Item


class ScrapyExapmleItem(Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    pass


class TopicItem(Item):
    # topic = Field()
    type = Field()
    topic_id = Field()  # 话题id
    topic_name = Field()  # 话题名
    topic_description = Field()  # 话题描述


class QuestionItem(Item):
    type = Field()
    question_id = Field()            #问题id
    topic_id = Field()               #话题id
    question_title = Field()         #问题标题
    question_content = Field()       #问题具体内容

class UserItem(Item):
    type = Field()
    # user_id = scrapy.Field()              #页面没有用户id
    user_name = Field()              #名字
    user_avatar = Field()            #头像
    user_gender = Field()            #性别
    user_short_description = Field() #一句话描述
    user_long_description = Field()  #个人简介
    user_location = Field()          #居住地
    user_job = Field()               #工作
    user_business = Field()          #行业
    user_school = Field()            #学校


class AnswerItem(Item):
    type = Field()
    question_id = Field()            #所回答的问题的id
    answer_id = Field()              #答案id
    answerer_name = Field()          #回答者名字
    answer_content = Field()         #答案内容
    answer_agreements = Field()      #答案赞数
    answer_edit_time = Field()       #编辑时间


