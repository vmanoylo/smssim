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
        self.producer = main.producer(100)
        self.passed = 0
        self.failed = 0

    def update(self, success, time):
        if success:
            self.passed += 1
        else:
            self.failed += 1

    def test_passing(self):
        main.sender(self.producer, self.update, 0, 0)
        self.assertEqual(self.passed, 100)
        self.assertEqual(self.failed, 0)

    def test_failing(self):
        main.sender(self.producer, self.update, 0, 1)
        self.assertEqual(self.passed, 0)
        self.assertEqual(self.failed, 100)

    def test_coin_flip(self):
        main.sender(self.producer, self.update, 0, 0.5)
        self.assertGreater(self.passed, 0)
        self.assertGreater(self.failed, 0)
        self.assertEqual(self.passed + self.failed, 100)
        self.assertAlmostEqual(self.passed, self.failed, delta=10)


class TestProgressMonitor(unittest.TestCase):
    pass


class TestSimulator(unittest.TestCase):
    pass


if __name__ == "__main__":
    unittest.main()
