from bottle import template, route, run, redirect, request
from bs4 import BeautifulSoup
import requests
from sqlalchemy import *
from sqlalchemy.orm import declarative_base, sessionmaker, Session
import app.classifier as classifier
import os

bayes = classifier.NaiveBayesClassifier(0.01)

template_dir = "app/templates"


Base = declarative_base()
engine = create_engine(f"sqlite:///{os.environ.get('DB_PATH')}")
session = sessionmaker(bind=engine)


def get_all_with_label(s: Session):
    return s.query(News).filter(News.label != None).all()


def get_all_without_label(s: Session):
    return s.query(News).filter(News.label == None).all()


@route('/')
def index():
    redirect("/news")


@route('/news')
def news_list():
    s = session()
    rows = get_all_without_label(s)
    return template(f'{template_dir}/news_template', rows=rows)


@route('/add_label')
def add_label():
    label = request.params["label"]
    new_id = request.params["id"]
    page = request.params["page"]
    s: Session = session()
    record: News = s.query(News).filter(News.id == new_id).first()
    record.label = label
    bayes.fit([record.title], [record.label])
    s.commit()
    redirect(f'/{page}')


@route('/update_news')
def update_news():
    page = request.params["page"]
    add_news_to_db(session(), News)
    redirect(f'/{page}')


def add_news_to_db(s: Session, News):
    news = get_all_news()
    records = set(map(new_to_pair, s.query(News).all()))
    for new in news:
        pair = (new["title"], new["author"])
        if pair not in records:
            new = News(**new)
            s.add(new)
    s.commit()


@route('/recommendations')
def recommendations():
    s = session()
    unclassified_news = get_all_without_label(s)
    classified_news = []
    for label, new in zip(bayes.predict([x.title for x in unclassified_news]), unclassified_news):
        classified_new: News = new
        classified_new.label = label
        classified_news.append(classified_new)
    return template(f'{template_dir}/news_recommendations', rows=classified_news)


def new_to_pair(new):
    return new.title, new.author


class News(Base):
    __tablename__ = "news"
    id = Column(Integer, primary_key=True)
    title = Column(String)
    author = Column(String)
    url = Column(String)
    comments = Column(Integer)
    points = Column(Integer)
    label = Column(String)


Base.metadata.create_all(bind=engine)


def extract_next_page(page_n):
    soup = BeautifulSoup(requests.get(f"https://news.ycombinator.com/news?p={page_n}").text, "html.parser")

    athings = soup.find_all("tr", {"class": "athing"})
    if len(athings) == 0:
        return None

    subtexts = soup.find_all("td", {"class": "subtext"})

    news = []
    for i in range(len(athings)):
        new = extract_news(athings[i], subtexts[i])
        if new != {}:
            news.append(new)
    return news


def extract_news(page, subtext):
    new = {}

    a_tags = subtext.find_all("a")

    author = subtext.find("a", {"class": "hnuser"})
    if author is None:
        return {}
    new["author"] = author.text

    comments = a_tags[3].text.strip().split("\xa0")
    if len(comments) == 1:
        comments = 0
    else:
        comments = int(comments[0])
    new["comments"] = comments

    points = int(subtext.find("span").text.strip().split(" ")[0])
    new["points"] = points

    title_tag = page.find_all("td", {"class": "title"})[1]

    title = title_tag.a.text
    new["title"] = title

    url_span = title_tag.span
    if url_span is None:
        return {}
    url = url_span.a.span.text
    new["url"] = url
    return new


def get_news(n_pages):
    news = []
    for i in range(1, n_pages + 1):
        page = extract_next_page(i)
        if page is None:
            return news
        news.extend(page)
    return news


def get_all_news():
    news = []
    i = 1
    while True:
        page = extract_next_page(i)
        i += 1
        if page is None:
            return news
        news.extend(page)


def setup():
    s: Session = session()
    classified = get_all_with_label(s)
    bayes.fit([x.title for x in classified], [x.label for x in classified])


def start_server():
    setup()

    run(host="localhost", port=8080)


if __name__ == '__main__':
    start_server()
