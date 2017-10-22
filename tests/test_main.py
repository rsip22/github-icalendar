# -*- coding: utf-8 -*-
import unittest
import vcr
import os

# vamos:
# 1) criar uma funcao pra criar o objeto conf, jah com a API key do ambiente
#    (depois a gente pode incrementar essa funcao pra mais coisas)
# 2) tirar fora o VCR pq ele tah complicando as coisas...
# 3) escrever testes para:
#    a. sem especificar repo e label, feed pega todas issues de repos que tem acesso
#    b. especificando repo, feed pega todas issues daquele repo
#    c. especificando repo e label, feed pega todas issues com aquela label, daquele repo. não pega de outros repos
#       e nem de outras labels
#    d. especificando apenas label, feed pega todas issues com aquela label, de todos repos que tem acesso. não pega
#       outras labels

class GenerateIcalTest(unittest.TestCase):
    @vcr.use_cassette(filter_headers=['authorization'])
    def testSimple(self):
        # pudb.set_trace()
        from github_icalendar.main import generate_ical
        conf = {'api_token': os.getenv('GITHUB_TOKEN', 'fake_key')}
        ical_object = generate_ical(conf)
        self.assertIsNotNone(ical_object)
        label_list = [l for l in ical_object.splitlines() if l.startswith('LABEL')]
        self.assertIsNotNone(label_list)
