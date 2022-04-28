import os
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

#########数字抽取#########
import cn2an
import chinese2digits as c2d


def to_digit(s: str):
    output = cn2an.transform("s", "cn2an")
    output = c2d.takeNumberFromString(output)
    output = output['digitsStringList']
    return output


########### spacy语义相似度###########
time1 = datetime.datetime.now()
nlp = spacy.load('zh_core_web_md')
time2 = datetime.datetime.now()
logger.info(f'spacy model加载完成，耗时{time2 - time1}秒')


def sentences_similarity(sentences, corpus, topk=3, min_simil=0):
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
# 验证理财表单（废弃）
class ValidatePurchaseFinaceForm(FormValidationAction):
    def name(self) -> Text:
        return "validate_purchase_finance_form"

    async def validate_finance_product(
            self,
            value: Text,
            dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any],
    ) -> Dict[Text, Any]:
        finance_product = tracker.get_slot("finance_product")
        if finance_product is not None:
            # validation succeeded, set the value of the "cuisine" slot to value
            return {"finance_product": finance_product}
        else:
            # if value.find("好") >= 0 or value.find("推荐") >= 0 or value.find("是") >= 0:
            dispatcher.utter_message(response="utter_wrong_finance_product")
            # validation failed, set this slot to None, meaning the user will be asked for the slot again
            return {"finance_product": None}

    async def validate_finance_amount(
            self,
            value: Text,
            dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any],
    ) -> Dict[Text, Any]:
        amount = tracker.get_slot("finance_amount")
        if amount:
            # validation succeeded, set the value of the "cuisine" slot to value
            return {"finance_amount": amount}
        else:
            dispatcher.utter_message(response="utter_wrong_finance_product")
            # validation failed, set this slot to None, meaning the
            # user will be asked for the slot again
            return {"finance_amount": None}


# 在没有slot的情况下，推荐理财产品
class ActionRecommandFinancialProducts(Action):
    """购买理财产品"""

    def name(self) -> Text:
        """Unique identifier of the action"""
        return "recommand_finance_product"

    async def run(
            self,
            dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any],
    ) -> List[Dict]:
        finance_product = tracker.get_slot("finance_product")
        # if not finance_product:
        text = (f"正在为您查询最新的理财产品...")
        dispatcher.utter_message(text=text)
        # text = (f"根据您的喜好，给您推荐以下几款产品：\n"
        #         f"-鑫增利添添盈A款，预期年化收益率2.5% \n"
        #         f"-鑫增利添添盈B款，预期年化收益率2.3% \n"
        #         f"-幸福货币基金C款，预期年化收益率2.7% "
        #         )
        # dispatcher.utter_message(text=text)
        return []


# 详细介绍理财产品
class ActionFinancialProductsDetail(Action):

    def name(self) -> Text:
        """Unique identifier of the action"""
        return "action_finance_detail"

    async def run(
            self,
            dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any],
    ) -> List[Dict]:
        finance_product = tracker.get_slot("finance_product")
        if not finance_product:
            text = (f"正在为您详细介绍XXX产品")
        else:
            text = (f"正在为您详细介绍全部产品")
        dispatcher.utter_message(text=text)
        return []


class ActionBuyFinancialProducts(Action):
    """确认下单"""
    def name(self) -> Text:
        """Unique identifier of the action"""
        return "buy_financial_products"

    async def run(
            self,
            dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any],
    ) -> List[Dict]:
        """Executes the action"""
        slots = {
        }
        # finance_product = tracker.get_slot("finance_product")
        # finance_amount = tracker.get_slot("finance_amount")
        # text = (f"您已成功购买理财产品：{finance_product},购买金额为：{finance_amount}")
        text = (f"您已成功购买理财产品")
        dispatcher.utter_message(text=text)
        return []
