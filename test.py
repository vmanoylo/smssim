import unittest
import random

import main


class TestProducer(unittest.TestCase):
    def test_count(self):
        for i in random.choices(range(1000), k=100):
            c = 0
            for _ in main.producer(i):
                c += 1
            self.assertEqual(i, c)

    def test_message(self):
        for message, phone_number in main.producer(100):
            self.assertIsInstance(message, str)
            self.assertLessEqual(len(message), 100)


class TestSender(unittest.TestCase):
    pass


class TestProgressMonitor(unittest.TestCase):
    pass


class TestSimulator(unittest.TestCase):
    pass


if __name__ == "__main__":
    unittest.main()
