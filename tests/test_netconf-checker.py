#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
test_netconf-checker
----------------------------------
Tests for `netconf-checker` module.
"""

from betamax.fixtures import unittest
from netconf-checker import Greeting
from netconf-checker.netconf-checkerexceptions import MyException


class TestNetconf-checker(unittest.BetamaxTestCase):

    def setUp(self):
        """
        Test set up

        This is where you can setup things that you use throughout the tests. This method is called before every test.
        """
        pass

    def test_example_hello(self):
        """
        This is a test example

        You can name your test anything, as long as you prefix them with test_
        See the unittest page for more info:
        .. _a link: https://docs.python.org/2/library/unittest.html
        """
        example = Greeting()
        hello = example.hello_world()
        self.assertEqual(hello, 'Hello, world')
        example = Greeting('me')
        hello = example.hello_world()
        self.assertEqual(hello, 'Hello, me')

    def test_example_goodbye(self):
        """
        This is a test example

        You can name your test anything, as long as you prefix them with test_
        See the unittest page for more info:
        .. _a link: https://docs.python.org/2/library/unittest.html
        """
        example = Greeting()
        hello = example.goodbye_world()
        self.assertEqual(hello, 'Goodbye, world')
        example = Greeting('me')
        hello = example.goodbye_world()
        self.assertEqual(hello, 'Goodbye, me')

    def test_panic(self):
        """
        This test example looks for an exception
        """
        example = Greeting()
        self.assertRaises(MyException, example.panic_world)

    def tearDown(self):
        """
        Test tear down

        This is where you should tear down what you've setup in setUp before. This method is called after every test.
        """
        pass
