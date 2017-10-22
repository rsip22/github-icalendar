# -*- coding: utf-8 -*-
import unittest
import vcr
import os

"""
TODO: Write tests
Specifications:
a. if no repo and label in config, does the feed indeed get all issues
from repos the user has access to?
b. if repo in config, does the feed get all issues from that repo,
from all labels?
c. if repo AND label in config, does the feed get all issues with that label,
from the repo specified - and not from other repos?
d. if only label in config, does the feed get all issues with that label,
from all repos?
e. if more than one label in config, does the feed get all issues that contain
each label?
"""


class GenerateIcalTest(unittest.TestCase):
    @vcr.use_cassette(filter_headers=['authorization'])
    def testSimple(self):
        # pudb.set_trace()
        from github_icalendar.main import generate_ical
        conf = {'api_token': os.getenv('GITHUB_TOKEN', 'fake_key')}
        ical_object = generate_ical(conf)
        self.assertIsNotNone(ical_object)
