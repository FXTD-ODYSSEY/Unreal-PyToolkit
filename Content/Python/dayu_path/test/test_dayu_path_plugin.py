#!/usr/bin/env python
# -*- encoding: utf-8 -*-

__author__ = 'andyguo'

from unittest import TestCase

from dayu_path.plugin import DayuPathPlugin, DayuPath


class TestDayuPathPlugin(TestCase):
    def test_register_func(self):
        class callable_object(object):
            def __call__(self, *args, **kwargs):
                return args[1:], kwargs

        def plug_func(*args, **kwargs):
            return args[1:], kwargs

        self.assertTrue(DayuPathPlugin.register_func(plug_func))
        self.assertIn(plug_func.__name__, dir(DayuPath))
        self.assertEqual(DayuPath('/test').plug_func(1, 2, 3, key='value'),
                         ((1, 2, 3), {'key': 'value'}))

        @DayuPathPlugin.register_func
        def plug_func_deco(self, *args, **kwargs):
            return args, kwargs

        self.assertIn(plug_func.__name__, dir(DayuPath))
        self.assertEqual(DayuPath('/test').plug_func(1, 2, 3, key='value'),
                         ((1, 2, 3), {'key': 'value'}))

        self.assertFalse(DayuPathPlugin.register_func(callable_object()))
        self.assertFalse(DayuPathPlugin.register_func([]))

        def scan(*args, **kwargs):
            return 'duplicated func name'

        self.assertFalse(DayuPathPlugin.register_func(scan))

    def test_register_attribute(self):
        self.assertTrue(DayuPathPlugin.register_attribute('new_key'))
        self.assertIn('new_key', dir(DayuPath))
        self.assertIsNone(DayuPath.new_key)

        self.assertTrue(DayuPathPlugin.register_attribute('new_key_2',
                                                          default_value=111))
        self.assertIn('new_key_2', dir(DayuPath))
        self.assertEqual(DayuPath.new_key_2, 111)

        self.assertFalse(DayuPathPlugin.register_attribute(u'中文属性'))
        self.assertFalse(DayuPathPlugin.register_attribute('new_key'))
        self.assertFalse(DayuPathPlugin.register_attribute('frame'))
        self.assertFalse(DayuPathPlugin.register_attribute([]))

        try:
            delattr(DayuPath, 'new_key')
            delattr(DayuPath, 'new_key_2')
        except:
            self.failureException()

    def test_unregister(self):
        def add_test_data():
            def plug_func(*args, **kwargs):
                return args[1:], kwargs

            DayuPathPlugin.register_func(plug_func)
            DayuPathPlugin.register_attribute('key_1', default_value='value_1')
            DayuPathPlugin.register_attribute('key_2', default_value=[1, 2, 3])

        add_test_data()

        self.assertTrue(DayuPathPlugin.unregister('plug_func'))
        self.assertTrue(DayuPathPlugin.unregister('key_1'))
        self.assertTrue(DayuPathPlugin.unregister('key_2'))
        self.assertFalse(DayuPathPlugin.unregister('key_1'))
        self.assertFalse(DayuPathPlugin.unregister('key_2'))
        self.assertFalse(DayuPathPlugin.unregister('key_3'))
