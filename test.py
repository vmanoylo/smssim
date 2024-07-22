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
    def test_passing(self):
        producer = main.producer(100)
        passed = 0
        failed = 0

        def update(success, time):
            nonlocal passed, failed
            if success:
                passed += 1
            else:
                failed += 1

        main.sender(producer, update, 0, 0)
        self.assertEqual(passed, 100)
        self.assertEqual(failed, 0)

    def test_failing(self):
        producer = main.producer(100)
        passed = 0
        failed = 0

        def update(success, time):
            nonlocal passed, failed
            if success:
                passed += 1
            else:
                failed += 1

        main.sender(producer, update, 0, 1)
        self.assertEqual(passed, 0)
        self.assertEqual(failed, 100)


class TestProgressMonitor(unittest.TestCase):
    pass


class TestSimulator(unittest.TestCase):
    pass


if __name__ == "__main__":
    unittest.main()
