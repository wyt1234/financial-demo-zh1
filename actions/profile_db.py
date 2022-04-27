import os
import sqlalchemy as sa
from sqlalchemy import Column, Integer, String, DateTime, REAL
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.engine.base import Engine
from typing import Dict, Text, List, Union, Optional

from random import choice, randrange, sample, randint
from numpy import arange
from datetime import datetime, timedelta
import pytz

utc = pytz.UTC

GENERAL_ACCOUNTS = {
    # "recipient": [
    #     "katy parrow",
    #     "evan oslo",
    #     "william baker",
    #     "karen lancaster",
    #     "kyle gardner",
    #     "john jacob",
    #     "percy donald",
    #     "lisa macintyre",
    # ],
    "recipient": [
        "小吴",
        "小郑",
        "小李",
        "爸爸",
        "小张",
        "小王",
        "小钱",
        "小孙",
    ],
    # "vendor": ["target", "starbucks", "amazon"],
    "vendor": ["百货超市", "星巴克", "亚马逊"],
    # "depositor": ["interest", "employer"],
    "depositor": ["利息", "工作单位"]
}

ACCOUNT_NUMBER_LENGTH = 12
CREDIT_CARD_NUMBER_LENGTH = 14

Base = declarative_base()



class Finance(Base):
    __tablename__ = "finance"
    id = Column(Integer, primary_key=True)
    name = Column(String(255))
    type = Column(String(255))
    rate = Column(String(255))
    minimum_amount = Column(String(255))
    description = Column(String(255))

class Account(Base):
    """Accounts table.
    `session_id` is only meaningful for accounts generated by conversation sessions,
    when it is equal to `tracker.sender_id`.
    Since `id` autoincrements, it is used to generate unique account numbers by
    adding leading zeros to it.
    """

    __tablename__ = "account"
    id = Column(Integer, primary_key=True)
    session_id = Column(String(255))
    account_holder_name = Column(String(255))
    currency = Column(String(255))


class CreditCard(Base):
    """Credit cards table. `account_id` is an `Account.id`"""

    __tablename__ = "creditcards"
    id = Column(Integer, primary_key=True)
    credit_card_name = Column(String(255))
    minimum_balance = Column(REAL)
    current_balance = Column(REAL)
    account_id = Column(Integer)


class Transaction(Base):
    """Transactions table. `to/from_acount_number` are `Account.id`s with leading zeros"""

    __tablename__ = "transactions"
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime)
    amount = Column(REAL)
    from_account_number = Column(String(14))
    to_account_number = Column(String(14))


class RecipientRelationship(Base):
    """Valid recipients table. `account_id` and `recipient_account_id` are `Account.id`'s"""

    __tablename__ = "recipient_relationships"
    id = Column(Integer, primary_key=True)
    account_id = Column(Integer)
    recipient_account_id = Column(Integer)
    recipient_nickname = Column(String(255))


def create_database(database_engine: Engine, database_name: Text):
    """Try to connect to the database. Create it if it does not exist"""
    try:
        database_engine.connect()
    except sa.exc.OperationalError:
        default_db_url = f"sqlite:///{database_name}.db"
        default_engine = sa.create_engine(default_db_url)
        conn = default_engine.connect()
        conn.execute("commit")
        conn.execute(f"CREATE DATABASE {database_name}")
        conn.close()


class ProfileDB:
    def __init__(self, db_engine: Engine):
        self.engine = db_engine
        self.create_tables()
        self.session = self.get_session()

    def get_session(self) -> Session:
        return sessionmaker(bind=self.engine, autoflush=True)()

    def create_tables(self):
        CreditCard.__table__.create(self.engine, checkfirst=True)
        Transaction.__table__.create(self.engine, checkfirst=True)
        RecipientRelationship.__table__.create(self.engine, checkfirst=True)
        Account.__table__.create(self.engine, checkfirst=True)

    def get_account(self, id: int):
        """Get an `Account` object based on an `Account.id`"""
        return self.session.query(Account).filter(Account.id == id).first()

    def get_account_from_session_id(self, session_id: Text):
        """Get an `Account` object based on a `Account.session_id`"""
        # if the action server restarts in the middle of a conversation, the db will need to be repopulated outside of an action_session_start
        if not self.check_session_id_exists(session_id):
            self.populate_profile_db(session_id)
        account = (
            self.session.query(Account).filter(Account.session_id == session_id).first()
        )
        return account

    @staticmethod
    def get_account_number(account: Union[CreditCard, Account]):
        """Get a bank or credit card account number by adding the appropriate number of leading zeros to an `Account.id`"""
        if type(account) is CreditCard:
            return f"%0.{CREDIT_CARD_NUMBER_LENGTH}d" % account.id
        else:
            return f"%0.{ACCOUNT_NUMBER_LENGTH}d" % account.id

    def get_account_from_number(self, account_number: Text):
        """Get a bank or credit card account based on an account number"""
        if len(account_number) == CREDIT_CARD_NUMBER_LENGTH:
            return (
                self.session.query(CreditCard)
                    .filter(CreditCard.id == int(account_number))
                    .first()
            )
        else:
            return (
                self.session.query(Account)
                    .filter(Account.id == int(account_number))
                    .first()
            )

    def get_recipient_from_name(self, session_id: Text, recipient_name: Text):
        """Get a recipient based on the nickname.
        Take the first one if there are multiple that match.
        """
        account = self.get_account_from_session_id(session_id)
        recipient = (
            self.session.query(RecipientRelationship)
                .filter(RecipientRelationship.account_id == account.id)
                .filter(RecipientRelationship.recipient_nickname == recipient_name.lower())
                .first()
        )
        recipient_account = self.get_account(recipient.recipient_account_id)
        return recipient_account

    def list_known_recipients(self, session_id: Text):
        """List recipient nicknames available to an account holder"""
        recipients = (
            self.session.query(RecipientRelationship.recipient_nickname)
                .filter(
                RecipientRelationship.account_id
                == self.get_account_from_session_id(session_id).id
            )
                .all()
        )
        return [recipient.recipient_nickname for recipient in recipients]

    def check_session_id_exists(self, session_id: Text):
        """Check if an account for `session_id` already exists"""
        return self.session.query(
            self.session.query(Account.session_id)
                .filter(Account.session_id == session_id)
                .exists()
        ).scalar()

    def get_account_balance(self, session_id: Text):
        """Get the account balance for an account"""
        account_number = self.get_account_number(
            self.get_account_from_session_id(session_id)
        )
        spent = float(
            self.session.query(sa.func.sum(Transaction.amount))
                .filter(Transaction.from_account_number == account_number)
                .all()[0][0]
        )
        earned = float(
            self.session.query(sa.func.sum(Transaction.amount))
                .filter(Transaction.to_account_number == account_number)
                .all()[0][0]
        )
        return earned - spent

    def get_currency(self, session_id: Text):
        """Get the currency for an account"""
        return (
            self.session.query(Account.currency)
                .filter(Account.session_id == session_id)
                .first()[0]
        )

    def search_transactions(
            self,
            session_id: Text,
            start_time: Optional[datetime] = None,
            end_time: Optional[datetime] = None,
            deposit: bool = False,
            vendor: Optional[Text] = None,
    ):
        """Find all transactions for an account between `start_time` and `end_time`.
        Looks for spend transactions by default, set `deposit` to `True` to search earnings.
        Looks for transactions with anybody by default, set `vendor` to search by vendor
        """
        account = self.get_account_from_session_id(session_id)
        account_number = self.get_account_number(account)
        if deposit:
            transactions = self.session.query(Transaction).filter(
                Transaction.to_account_number == account_number
            )
        elif vendor:
            to_account = (
                self.session.query(Account.id)
                    .filter(Account.session_id.startswith("vendor_"))
                    .filter(Account.account_holder_name == vendor.lower())
                    .first()
            )
            to_account_number = self.get_account_number(to_account)
            transactions = (
                self.session.query(Transaction)
                    .filter(Transaction.from_account_number == account_number)
                    .filter(Transaction.to_account_number == to_account_number)
            )
        else:
            transactions = self.session.query(Transaction).filter(
                Transaction.from_account_number == account_number
            )
        if start_time:
            transactions = transactions.filter(Transaction.timestamp >= start_time)
        if end_time:
            transactions = transactions.filter(Transaction.timestamp <= end_time)

        return transactions

    def list_credit_cards(self, session_id: Text):
        """List valid credit cards for an acccount"""
        account = self.get_account_from_session_id(session_id)
        cards = (
            self.session.query(CreditCard)
                .filter(CreditCard.account_id == account.id)
                .all()
        )
        return [card.credit_card_name for card in cards]

    def get_credit_card(self, session_id: Text, credit_card_name: Text):
        """Get a `CreditCard` object based on the card's name and the `session_id`"""
        account = self.get_account_from_session_id(session_id)
        return (
            self.session.query(CreditCard)
                .filter(CreditCard.account_id == account.id)
                .filter(CreditCard.credit_card_name == credit_card_name.lower())
                .first()
        )

    def get_credit_card_balance(
            self,
            session_id: Text,
            credit_card_name: Text,
            balance_type: Text = "current_balance",
    ):
        """Get the balance for a credit card based on its name and the balance type"""
        balance_type = "_".join(balance_type.split())
        card = self.get_credit_card(session_id, credit_card_name)
        # fixme
        balance_type = 'minimum_balance' if '最低' in balance_type else 'current_balance'
        return getattr(card, balance_type)

    @staticmethod
    def list_balance_types():
        """List valid balance types for credit cards"""
        return [
            " ".join(name.split("_"))
            for name in CreditCard.__table__.columns.keys()
            if name.endswith("balance")
        ]

    def list_vendors(self):
        """List valid vendors"""
        vendors = (
            self.session.query(Account.account_holder_name)
                .filter(Account.session_id.startswith("vendor_"))
                .all()
        )
        return [vendor.account_holder_name for vendor in vendors]

    def pay_off_credit_card(
            self, session_id: Text, credit_card_name: Text, amount: float
    ):
        """Do a transaction to move the specified amount from an account to a credit card"""
        account = self.get_account_from_session_id(session_id)
        account_number = self.get_account_number(account)
        credit_card = (
            self.session.query(CreditCard)
                .filter(CreditCard.account_id == account.id)
                .filter(CreditCard.credit_card_name == credit_card_name.lower())
                .first()
        )
        self.transact(
            account_number,
            self.get_account_number(credit_card),
            amount,
        )
        credit_card.current_balance -= amount
        if amount < credit_card.minimum_balance:
            credit_card.minimum_balance -= amount
        else:
            credit_card.minimum_balance = 0
        self.session.commit()

    def add_session_account(self, session_id: Text, name: Optional[Text] = ""):
        """Add a new account for a new session_id. Assumes no such account exists yet."""
        self.session.add(
            Account(session_id=session_id, account_holder_name=name, currency="$")
        )

    def add_credit_cards(self, session_id: Text):
        """Populate the creditcard table for a given session_id"""
        # credit_card_names = ["iron bank", "credit all", "emblem", "justice bank"]
        credit_card_names = ["工商银行", "上海农商银行"]
        credit_cards = [
            CreditCard(
                credit_card_name=cardname,
                minimum_balance=choice([20, 30, 40]),
                current_balance=choice(
                    [round(amount, 2) for amount in list(arange(20, 500, 0.01))]
                ),
                account_id=self.get_account_from_session_id(session_id).id,
            )
            for cardname in credit_card_names
        ]
        self.session.add_all(credit_cards)

    def check_general_accounts_populated(
            self, general_account_names: Dict[Text, List[Text]]
    ):
        """Check whether tables have been populated with global values for vendors, recipients, and depositors"""
        account_names = set(
            [
                name
                for list_names in general_account_names.values()
                for name in list_names
            ]
        )
        existing_accounts = self.session.query(Account.account_holder_name).filter(
            Account.account_holder_name.in_(account_names)
        )
        existing_account_names = set(
            [account.account_holder_name for account in existing_accounts.all()]
        )
        return account_names == existing_account_names

    def add_general_accounts(self, general_account_names: Dict[Text, List[Text]]):
        """Populate tables with global values for vendors, recipients, and depositors"""
        general_accounts = [
            Account(session_id=f"{prefix}_{id}", account_holder_name=name)
            for prefix, names in general_account_names.items()
            for id, name in enumerate(names)
        ]

        for account in general_accounts:
            self.session.merge(account)
        self.session.commit()

    def add_recipients(self, session_id: Text):
        """Populate recipients table"""
        account = self.get_account_from_session_id(session_id)
        recipients = (
            self.session.query(Account.account_holder_name, Account.id)
                .filter(Account.session_id.startswith("recipient_"))
                .all()
        )
        session_recipients = sample(recipients, choice(list(range(3, len(recipients)))))
        relationships = [
            RecipientRelationship(
                account_id=account.id,
                recipient_account_id=recipient.id,
                recipient_nickname=recipient.account_holder_name,
            )
            for recipient in session_recipients
        ]
        self.session.add_all(relationships)

    def add_transactions(self, session_id: Text):
        """Populate transactions table for a session ID with random transactions"""
        account_number = self.get_account_number(
            self.get_account_from_session_id(session_id)
        )
        vendors = (
            self.session.query(Account)
                .filter(Account.session_id.startswith("vendor_"))
                .all()
        )
        depositors = (
            self.session.query(Account)
                .filter(Account.session_id.startswith("depositor_"))
                .all()
        )

        start_date = utc.localize(datetime(2019, 1, 1))
        end_date = utc.localize(datetime.now())
        number_of_days = (end_date - start_date).days

        for vendor in vendors:
            rand_spend_amounts = sample(
                [round(amount, 2) for amount in list(arange(5, 50, 0.01))],
                number_of_days // 2,
            )

            rand_dates = [
                (start_date + timedelta(days=randrange(number_of_days)))
                for x in range(0, len(rand_spend_amounts))
            ]

            spend_transactions = [
                Transaction(
                    from_account_number=account_number,
                    to_account_number=self.get_account_number(vendor),
                    amount=amount,
                    timestamp=date,
                )
                for amount, date in zip(rand_spend_amounts, rand_dates)
            ]

            self.session.add_all(spend_transactions)

        for depositor in depositors:
            if depositor.account_holder_name == "interest":
                rand_deposit_amounts = sample(
                    [round(amount, 2) for amount in list(arange(5, 20, 0.01))],
                    number_of_days // 30,
                )
            else:
                rand_deposit_amounts = sample(
                    [round(amount, 2) for amount in list(arange(1000, 2000, 0.01))],
                    number_of_days // 14,
                )

            rand_dates = [
                (start_date + timedelta(days=randrange(number_of_days)))
                for x in range(0, len(rand_deposit_amounts))
            ]

            deposit_transactions = [
                Transaction(
                    from_account_number=self.get_account_number(depositor),
                    to_account_number=account_number,
                    amount=amount,
                    timestamp=date,
                )
                for amount, date in zip(rand_deposit_amounts, rand_dates)
            ]

            self.session.add_all(deposit_transactions)

    def populate_profile_db(self, session_id: Text):
        """Initialize the database for a conversation session.
        Will populate all tables with sample values.
        If general accounts have already been populated, it will only
        add account-holder-specific values to tables.
        """
        if not self.check_general_accounts_populated(GENERAL_ACCOUNTS):
            self.add_general_accounts(GENERAL_ACCOUNTS)
        if not self.check_session_id_exists(session_id):
            self.add_session_account(session_id)
            self.add_recipients(session_id)
            self.add_transactions(session_id)
            self.add_credit_cards(session_id)

        self.session.commit()

    def transact(
            self, from_account_number: Text, to_account_number: Text, amount: float
    ):
        """Add a transation to the transaction table"""
        timestamp = datetime.now()
        transaction = Transaction(
            from_account_number=from_account_number,
            to_account_number=to_account_number,
            amount=amount,
            timestamp=timestamp,
        )
        self.session.add(transaction)
        self.session.commit()
