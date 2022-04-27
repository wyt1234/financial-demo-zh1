import datetime

import loguru
import numpy as np
import spacy
from loguru import logger

logger.info('spacy model启动加载')
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


if __name__ == '__main__':
    sentences = ['如何更换花呗绑定银行卡']
    corpus = [
        '花呗更改绑定银行卡',
        '我什么时候开通了花呗',
        '俄罗斯警告乌克兰反对欧盟协议',
        '暴风雨掩埋了东北部；新泽西16英寸的降雪',
        '中央情报局局长访问以色列叙利亚会谈',
        '人在巴基斯坦基地的炸弹袭击中丧生',
    ]
    sentences_similarity(sentences, corpus)
