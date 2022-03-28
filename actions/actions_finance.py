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


#####购买理财产品##########
class ActionBuyFinancialProducts(Action):
    """购买理财产品"""

    def name(self) -> Text:
        """Unique identifier of the action"""
        return "buy_financial_products "

    async def run(
            self,
            dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any],
    ) -> List[Dict]:
        """Executes the action"""
        slots = {
        }
        finance_product = tracker.get_slot("finance_product")
        finance_amount = tracker.get_slot("finance_amount")
        text = (f"您已成功购买理财产品：{finance_product},购买金额为：{finance_amount}")
        dispatcher.utter_message(text=text)
        return []


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
        text = (f"根据您的喜好，给您推荐以下几款产品：\n"
                f"-鑫增利添添盈A款，预期年化收益率2.5% \n"
                f"-鑫增利添添盈B款，预期年化收益率2.3% \n"
                f"-幸福货币基金C款，预期年化收益率2.7% "
                )
        dispatcher.utter_message(text=text)
        return []
