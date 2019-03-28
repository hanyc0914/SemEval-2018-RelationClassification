import subprocess
import re
import random
from bs4 import BeautifulSoup, NavigableString

from numba import jit
from constant import *


class Paper:
    def __init__(self, text_id: str="", title: str="", abstract: str="", entity_id: list=[], entity_str: list=[]):
        self.id = text_id
        self.title = title
        self.abstract = abstract
        self.entity_id = entity_id
        self.entity_str = entity_str

    def __repr__(self):
        entity_list = ["%s: %s" % (i, string) for i, string in zip(
            self.entity_id, self.entity_str)]
        entity = "\n".join(entity_list)
        return "Paper %s\n\nTitle: %s\n\nAbstract:\n\n%s\n\nEntities:\n\n%s" % (self.id, self.title, self.abstract, entity)


def loadPaper(filename):
    papers = []  # list of Paper object
    with open(filename, 'r') as text_raw:
        raw_xml = text_raw.read()

    xml = BeautifulSoup(raw_xml, features="html.parser")

    texts = xml.doc.findAll('text')

    for text in texts:
        paper = Paper(text_id=text["id"], title=text.title.text)

        abstract = ""
        for abstract_item in text.abstract.contents:
            try:
                abstract += str(abstract_item.text)
            except:
                abstract += str(abstract_item)

        paper.abstract = abstract

        entities = text.findAll('entity')
        entity_id = []
        entity_str = []
        for entity in entities:
            entity_id.append(entity["id"])
            entity_str.append(entity.text)

        paper.entity_id = entity_id
        paper.entity_str = entity_str
        papers.append(paper)

    return papers


def loadRelation(filename):
    entity_pair_relation = {}  # (entity1, entity2): relation
    with open(filename, 'r') as relation_raw:
        raw_lines = relation_raw.readlines()
    for string in raw_lines:
        relation_str, rest_of_str = string.split('(', 1)
        relation_encode = rela2id[relation_str]
        entity1, entity2 = rest_of_str.split(',')[:2]
        if entity2.endswith(')\n'):
            entity2 = entity2[:-2]
        entity_pair_relation[(entity1, entity2)] = relation_encode

    return entity_pair_relation


def scorerEval(pred_file, key_file):
    """ evaluation using the scorer """
    cmd = f'perl {score_script_path} {pred_file} {key_file}'
    result = subprocess.check_output(
        cmd, stderr=subprocess.STDOUT, shell=True).decode()
    return result


def getMacroResult(pred_file, key_file):
    """ get macro precision, recall and f1 score """
    score = scorerEval(pred_file, key_file)
    P_str = re.findall(r'P\s+=\s+\d+\.\d+\%', score)[-1]
    P = float(re.search(r'\d+\.\d+', P_str).group(0))
    R_str = re.findall(r'R\s+=\s+\d+\.\d+\%', score)[-1]
    R = float(re.search(r'\d+\.\d+', R_str).group(0))
    F1_str = re.findall(r'F1\s+=\s+\d+\.\d+\%', score)[-1]
    F1 = float(re.search(r'\d+\.\d+', F1_str).group(0))
    return P, R, F1


@jit
def fastF1(result, predict, trueValue):
    """
    f1 score
    """
    trueNum = 0
    recallNum = 0
    precisionNum = 0
    for index, values in enumerate(result):
        if values == trueValue:
            recallNum += 1
            if values == predict[index]:
                trueNum += 1
        if predict[index] == trueValue:
            precisionNum += 1
    R = trueNum / recallNum if recallNum else 0
    P = trueNum / precisionNum if precisionNum else 0
    f1 = (2 * P * R) / (P + R) if (P + R) else 0
    print(P, R, f1)
    return P, R, f1


def scoreSelf(predict):
    with open('%skeys.test.1.1.txt' % data_path, 'r') as f:
        result = [rela2id[ii.split('(')[0]] for ii in f.readlines()]
    p, r = 0, 0
    for ii in range(6):
        tp, tr, _ = fastF1(result, predict, ii)
        p += tp
        r += tr
    p /= 6
    r /= 6
    f1 = (2 * p * r) / (p + r) if (p + r) else 0
    print(p, r, f1)


# Test utilities
if __name__ == "__main__":

    P, R, F1 = getMacroResult('%skeys.test.1.1.txt' % test_data_path,
                              '%skeys.test.1.1.txt' % test_data_path)
    print(P, R, F1)
    P, R, F1 = getMacroResult('%s1.1random.txt' % prediction_path,
                              '%skeys.test.1.1.txt' % test_data_path)
    print(P, R, F1)

    papers = loadPaper('%s1.1.text.xml' % train_data_path)
    print(papers[0])

    relations = loadRelation('%s1.1.relations.txt' % train_data_path)
    print(list(relations)[:10])