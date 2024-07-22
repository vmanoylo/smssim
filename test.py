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

    def test_coin_flip(self):
        producer = main.producer(100)
        passed = 0
        failed = 0

        def update(success, time):
            nonlocal passed, failed
            if success:
                passed += 1
            else:
                failed += 1

        main.sender(producer, update, 0, 0.5)
        self.assertGreater(passed, 0)
        self.assertGreater(failed, 0)
        self.assertEqual(passed + failed, 100)
        self.assertAlmostEqual(passed, failed, delta=10)


class TestProgressMonitor(unittest.TestCase):
    pass


class TestSimulator(unittest.TestCase):
    pass


if __name__ == "__main__":
    unittest.main()
