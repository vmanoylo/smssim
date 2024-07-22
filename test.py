import time
import unittest
import random

import main


class TestProducer(unittest.TestCase):
    def test_negative(self):
        for i in random.choices(range(1000), k=100):
            self.assertEqual(0, len(list(main.producer(-i))))

    def test_count(self):
        for i in random.choices(range(1000), k=100):
            self.assertEqual(i, len(list(main.producer(i))))

    def test_message(self):
        for message, phone_number in main.producer(100):
            self.assertIsInstance(message, str)
            self.assertLessEqual(len(message), 100)


class TestSender(unittest.TestCase):
    def setUp(self):
        self.messages = 1000
        self.producer = main.producer(self.messages)
        self.passed = 0
        self.failed = 0

    def update(self, success, time):
        if success:
            self.passed += 1
        else:
            self.failed += 1

    def test_passing(self):
        main.sender(self.producer, self.update, 0, 0)
        self.assertEqual(self.passed, self.messages)
        self.assertEqual(self.failed, 0)

    def test_failing(self):
        main.sender(self.producer, self.update, 0, 1)
        self.assertEqual(self.passed, 0)
        self.assertEqual(self.failed, self.messages)

    def test_coin_flip(self):
        main.sender(self.producer, self.update, 0, 0.5)
        self.assertGreater(self.passed, 0)
        self.assertGreater(self.failed, 0)
        self.assertEqual(self.passed + self.failed, self.messages)
        self.assertAlmostEqual(self.passed, self.failed, delta=self.messages * 0.1)

    def test_time(self):
        start = time.time()
        main.sender(main.producer(100), self.update, 0.01, 0)
        end = time.time()
        self.assertAlmostEqual(end - start, 1, delta=0.2)

class TestProgressMonitor(unittest.TestCase):
    pass


class TestSimulator(unittest.TestCase):
    pass


if __name__ == "__main__":
    unittest.main()
