import threading
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
        for message in main.producer(100):
            self.assertLessEqual(len(message.message), 100)


class TestSender(unittest.TestCase):
    def setUp(self):
        self.messages = 1000
        self.producer = main.producer(self.messages)
        self.passed = 0
        self.failed = 0

    def update(self, success):
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

    def test_negative_mean(self):
        with self.assertRaises(ValueError):
            main.sender(self.producer, self.update, -1, 0)


class TestProgressMonitor(unittest.TestCase):
    def setUp(self):
        self.sent = 0
        self.failed = 0
        self.total_time = 0
        self.updates = 0
        self.monitor = main.ProgressMonitor(self.mock_display, 0.1)
        self.monitor_thread = threading.Thread(target=self.monitor.run)

    def mock_display(self, sent, failed, t):
        self.sent = sent
        self.failed = failed
        self.total_time = t
        self.updates += 1

    def test_show(self):
        self.monitor_thread.start()
        time.sleep(0.41)
        self.monitor.stop()
        self.monitor_thread.join()
        self.assertEqual(self.updates, 6)  # 5 updates + 1 stop
        self.assertAlmostEqual(self.total_time, 0.5, delta=0.1)

    def test_update(self):
        for _ in range(10):
            self.monitor_thread.start()
            sent = random.randint(0, 10)
            failed = random.randint(0, 10)
            for _ in range(sent):
                self.monitor.update(True)
            for _ in range(failed):
                self.monitor.update(False)
            self.monitor.stop()
            self.monitor_thread.join()
            self.assertEqual(self.sent, sent)
            self.assertEqual(self.failed, failed)
            self.setUp()

    def test_instant_monitor(self):
        monitor = main.ProgressMonitor(self.mock_display, 0)
        thread = threading.Thread(target=monitor.run)
        thread.start()
        time.sleep(0.1)
        monitor.stop()
        thread.join()
        self.assertEqual(self.sent, 0)
        self.assertEqual(self.failed, 0)
        self.assertGreater(self.total_time, 0)
        self.assertGreater(self.updates, 0)

    def test_negative_interval(self):
        with self.assertRaises(ValueError):
            main.ProgressMonitor(self.mock_display, -1)


class TestSimulator(unittest.TestCase):
    pass


if __name__ == "__main__":
    unittest.main()
