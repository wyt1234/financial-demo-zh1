import json
import os
import random
from typing import Dict, Text, Any, List
import logging
from dateutil import parser
import sqlalchemy as sa

from rasa_sdk.interfaces import Action
from rasa_sdk.events import (
    SlotSet,
    EventType,
    ActionExecuted,
    SessionStarted,
    Restarted,
    FollowupAction,
    UserUtteranceReverted,
)
from rasa_sdk import Tracker, FormValidationAction
from rasa_sdk.executor import CollectingDispatcher

from actions.parsing import (
    parse_duckling_time_as_interval,
    parse_duckling_time,
    get_entity_details,
    parse_duckling_currency,
)

from actions.profile_db import create_database, ProfileDB

from actions.custom_forms import CustomFormValidationAction

import datetime

import numpy as np
import spacy
from loguru import logger

import cn2an
import chinese2digits as c2d

PROFILE_DB_NAME = os.environ.get("PROFILE_DB_NAME", "profile")
PROFILE_DB_URL = os.environ.get("PROFILE_DB_URL", f"sqlite:///{PROFILE_DB_NAME}.db")
ENGINE = sa.create_engine(PROFILE_DB_URL)
create_database(ENGINE, PROFILE_DB_NAME)

profile_db = ProfileDB(ENGINE)


#########数字抽取#########


def to_digit(s: str):
    output = cn2an.transform(s, "cn2an")
    output = c2d.takeNumberFromString(output)
    output = output['digitsStringList']
    return output


########### spacy语义相似度###########
time1 = datetime.datetime.now()
nlp = spacy.load('zh_core_web_md')
time2 = datetime.datetime.now()
logger.info(f'spacy model加载完成，耗时{time2 - time1}秒')


def sentences_similarity(sentences, corpus, topk=3, min_simil=0) -> List:
    similarities = []
    for n, s in enumerate(sentences):
        for q in corpus:
            token_s = nlp(s)
            token_q = nlp(q)
            simil = token_s.similarity(token_q)
            # logger.info('simil {}'.format(float(simil)))
            similarities.append({'q': q, 'simil': float(simil)})
    similarities = filter(lambda x: x['simil'] >= min_simil, similarities)
    similarities = sorted(similarities, key=lambda x: x['simil'], reverse=True)
    logger.info(similarities[:topk])
    return similarities[:topk]


#####购买理财产品##########

# 在没有slot的情况下，推荐理财产品
class ActionRecommandFinancialProducts(Action):
    """推荐理财产品"""

    def name(self) -> Text:
        return "recommand_finance_product"

    async def run(
            self,
            dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any],
    ) -> List[Dict]:
        all_pd = profile_db.list_finance_pd()
        random.shuffle(all_pd)
        # slot_finance_product = tracker.get_slot("finance_product")
        # if not slot_finance_product:
        text = (f"正在查询最新的理财产品...")
        dispatcher.utter_message(text=text)
        pd_name_list = [f"{i + 1}、 {pd.name} \n" for i, pd in enumerate(all_pd)]
        text = (f"给您推荐以下几款产品：\n" + ''.join(pd_name_list))
        dispatcher.utter_message(text=text)
        text = (f"可以告诉小张您想要询问的产品名称，或者想了解第几个产品")
        dispatcher.utter_message(text=text)
        all_pd = profile_db.to_json_all(all_pd)
        return [SlotSet('recommand_list', all_pd)]


# 用户对收益率表示关心
class ActionAboutRate(Action):
    """用户对收益率表示关心"""

    def name(self) -> Text:
        return "action_concern_rate"

    async def run(
            self,
            dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any],
    ) -> List[Dict]:
        text = (f"亲亲已经为您重点考虑收益率相关信息，么么")
        dispatcher.utter_message(text)
        return [SlotSet('concern_rate', True)]


# 处理用户指定列表的顺序
class ActionHandleWhichOne(Action):
    """用户指定列表的顺序"""

    def name(self) -> Text:
        return "action_handle_which_one"

    async def run(
            self,
            dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any],
    ) -> List[Dict]:
        latest_message = tracker.latest_message['text']
        output_list = to_digit(latest_message)
        which_order = int(output_list[0])
        if latest_message.find('倒数') >= 0:
            text = (f"您选中倒数第{which_order}个产品:")
            dispatcher.utter_message(text=text)
            which_order = -which_order
        else:
            text = (f"您选中第{which_order}个产品:")
            dispatcher.utter_message(text=text)
            which_order = which_order - 1
        slot_recommand_list = tracker.get_slot("recommand_list")
        pd = json.loads(slot_recommand_list)[which_order]
        #
        text = (f"{pd['name']}")
        dispatcher.utter_message(text=text)
        return [SlotSet('finance_product', pd['name'])]


# 处理用户指定模糊指代产品名
class ActionMatchProduct(Action):
    """处理用户指定模糊指代产品名"""

    def name(self) -> Text:
        return "action_match_product"

    async def run(
            self,
            dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any],
    ) -> List[Dict]:
        latest_message = tracker.latest_message['text']
        all_pd = profile_db.list_finance_pd()
        most_likely_pd = sentences_similarity(latest_message, [pd.name for pd in all_pd])[0]['q']
        text = f"您指的是{most_likely_pd}"
        dispatcher.utter_message(text)
        return [SlotSet('finance_product', most_likely_pd)]


# 详细介绍理财产品
class ActionFinancialProductsDetail(Action):
    """详细介绍理财产品"""

    def name(self) -> Text:
        return "action_finance_detail"

    async def run(
            self,
            dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any],
    ) -> List[Dict]:
        all_pd = profile_db.list_finance_pd()
        finance_product = tracker.get_slot("finance_product")
        if finance_product:
            text = (f"小张给您仔细介绍下：")
            dispatcher.utter_message(text=text)
            choose_pd = [x for x in all_pd if x.name == finance_product][0]
            text = (f"{choose_pd.name},利率为{choose_pd.rate}%，{choose_pd.description}")
            dispatcher.utter_message(text=text)
            text = (f"您想看看其他产品吗，或者也可以喊小张帮您下单购买它噢~")
            dispatcher.utter_message(text=text)
        else:
            # todo
            # text = (f"正在为您详细介绍全部产品")
            # dispatcher.utter_message(text=text)
            text = (f"您可以指定某个产品名称或者告诉我列表的第几个，小张给您重点介绍一下~")
            dispatcher.utter_message(text=text)
        return []


# 输入购买的金额
class ActionFillFinancialAmount(Action):
    """输入购买的金额"""

    def name(self) -> Text:
        return "fill_products_amount"

    async def run(
            self,
            dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any],
    ) -> List[Dict]:
        """Executes the action"""
        latest_message = tracker.latest_message['text']
        number = to_digit(latest_message)[0]
        text = (f"您输入购买的金额为{number}元")
        dispatcher.utter_message(text=text)
        return [SlotSet('finance_amount', number)]


# 核对信息无误
class ActionCheckBeforeBuyFinancial(Action):
    """核对信息无误"""

    def name(self) -> Text:
        return "check_before_buy_financial_products"

    async def run(
            self,
            dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any],
    ) -> List[Dict]:
        """Executes the action"""
        latest_message = tracker.latest_message['text']
        most_likely_choose = sentences_similarity(latest_message, ['正确', '不对'])[0]['q']
        if most_likely_choose == '正确':
            text = (f"好的，核对信息无误，正在为您下单")
            dispatcher.utter_message(text=text)
            return [SlotSet('confirm_purchase', True)]
        else:
            text = (f"好的，正在为您取消，您可以重新选择，谢谢")
            dispatcher.utter_message(text=text)
            return [SlotSet('confirm_purchase', False)]


# 下单
class ActionBuyFinancialProducts(Action):
    """确认下单"""

    def name(self) -> Text:
        return "buy_financial_products"

    async def run(
            self,
            dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any],
    ) -> List[Dict]:
        """Executes the action"""
        finance_product = tracker.get_slot("finance_product")
        finance_amount = tracker.get_slot("finance_amount")
        confirm_purchase = tracker.get_slot("confirm_purchase")
        if not finance_product:
            text = (f"抱歉还没有选择产品")
            dispatcher.utter_message(text=text)
            return [SlotSet('success_purchase', False)]
        text = (f"您已成功购买理财产品：{finance_product},购买金额为：{finance_amount}")
        dispatcher.utter_message(text=text)
        # 下单后清空所有的slot
        slots = {
            "which_one": None,
            "finance_product": None,
            "finance_amount": None,
            "confirm_purchase": None,
            "concern_rate": None,
            "success_purchase": True,
        }
        return [SlotSet(slot, value) for slot, value in slots.items()]
