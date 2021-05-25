import csv
import io
import math
import string


def argmax(args: dict):
    max_f = -math.inf
    max_key = None
    for i in args.keys():
        if max_f < args[i]:
            max_f, max_key = args[i], i
    return max_key


def merge(a, b):
    for k in b.keys():
        a[k] = a.get(k, 0) + b[k]
    return a


class NaiveBayesClassifier:
    def __init__(self, alpha):
        self.__alpha = alpha
        self.__classes = {}
        self.__C = set()
        self.__words_in_classes = {}
        self.__words = {}
        self.__d = 0

    def fit(self, X, y):
        X_cleared = [clean(x).lower() for x in X]
        self.__C = self.__C.union(set(y))
        for c in self.__C:
            self.__classes[c] = self.__classes.get(c, 0) + len(list(filter(lambda x: x == c, y)))

        words = {}
        words_in_classes = {}
        word_set = set()
        for x, c in zip(X_cleared, y):
            words_in_classes[c] = words_in_classes.get(c, {})
            for word in x.split():
                word_set.add(word)
                words[word] = words.get(word, 0) + 1
                words_in_classes[c][word] = words_in_classes[c].get(word, 0) + 1

        for c in self.__C:
            self.__words_in_classes[c] = merge(self.__words_in_classes.get(c, {}), words_in_classes.get(c, {}))
        self.__words = merge(words, self.__words)
        self.__d = len(self.__words)

    def __calc_prob(self, word, c):
        n_i_c = self.__words_in_classes[c].get(word, 0)
        n_c = self.__words.get(word, 0)
        return (n_i_c + self.__alpha) / (n_c + self.__d * self.__alpha)

    def predict(self, X):
        predictions = []
        len_C = len(self.__C)
        for x in [clean(x).lower() for x in X]:
            probs = {}
            for c in self.__C:
                prob = math.log(self.__classes[c] / len_C)
                for word in x.split():
                    prob += math.log(self.__calc_prob(word, c))
                probs[c] = prob
            predictions.append(argmax(probs))
        return predictions

    def score(self, X_test, y_test):
        score = 0
        for x, y in zip(self.predict([clean(x).lower() for x in X_test]), y_test):
            if x == y:
                score += 1
        return score / len(y_test)


def get_data(file_path):
    with io.open(file_path, "r", encoding="utf-8") as file:
        data = list(csv.reader(file, delimiter="\t"))
    X, y = [], []
    for target, msg in data:
        X.append(msg)
        y.append(target)
    return [X, y]


def clean(s):
    translator = str.maketrans("", "", string.punctuation)
    return s.translate(translator)


