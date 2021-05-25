import os
import threading
import time

import pytest
import requests
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy import *

from app.classifier import *
from app.main import get_all_with_label, get_all_without_label, add_news_to_db, start_server


class TestClassifier:
    @staticmethod
    def __get_data():
        X, y = get_data("tests/tests_data/data.txt")
        return X[:3900], y[:3900], X[3900:], y[3900:]

    def test_score(self):
        X_train, y_train, X_test, y_test = self.__get_data()

        model = NaiveBayesClassifier(10**-7)
        model.fit(X_train, y_train)

        score = model.score(X_test, y_test)
        print(f"Current score: {score}")
        assert score > 0.95

    def test_equal_results(self):
        X_train, y_train, X_test, y_test = self.__get_data()

        model1 = NaiveBayesClassifier(10**-7)
        model2 = NaiveBayesClassifier(10**-7)

        model1.fit(X_train, y_train)

        model2.fit(X_train[:100], y_train[:100])
        model2.fit(X_train[100:], y_train[100:])

        assert model1.score(X_test, y_test) == model2.score(X_test, y_test)


class TestDB:
    __Base = declarative_base()
    __engine = create_engine(f"sqlite:///{os.environ.get('DB_PATH')}")
    __session = sessionmaker(bind=__engine)

    __need_to_init_db = False

    class __News(__Base):
        __tablename__ = "news"
        id = Column(Integer, primary_key=True)
        title = Column(String)
        author = Column(String)
        url = Column(String)
        comments = Column(Integer)
        points = Column(Integer)
        label = Column(String)

    __Base.metadata.create_all(bind=__engine)

    @pytest.fixture(autouse=True, scope="session")
    def __init_db(self):
        if self.__need_to_init_db:
            add_news_to_db(self.__session(), self.__News)
            self.__need_to_init_db = False

    def test_all_with_labels(self):
        records = get_all_with_label(self.__session())
        assert len(records) > 0
        for row in records:
            assert row.label is not None

    def test_all_without_labels(self):
        records = get_all_without_label(self.__session())
        assert len(records) > 0
        for row in records:
            assert row.label is None


class TestWeb:
    @pytest.fixture(autouse=True, scope="session")
    def __init_server(self):
        print("Starting server...")
        server_thread = threading.Thread(target=start_server, args=())
        server_thread.daemon = True
        server_thread.start()
        time.sleep(5)

    @staticmethod
    def __test_request(url, expected_code):
        link = f"http://localhost:8080/{url}"
        response = requests.get(link)
        assert response.status_code == expected_code

    def test_index(self):
        self.__test_request("", 200)

    def test_news(self):
        self.__test_request("news", 200)

    def test_add_label_fail(self):
        self.__test_request("add_label", 500)

    def test_update_news_fail(self):
        self.__test_request("update_news", 500)

    def test_add_label_ok(self):
        self.__test_request("add_label?label=good&id=1&page=news", 200)

    def test_update_news_ok(self):
        self.__test_request("update_news?page=news", 200)

    def test_recommendations(self):
        self.__test_request("recommendations", 200)
