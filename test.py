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
        if not enable_timing_tests:
            raise unittest.SkipTest("Timing tests are disabled")
        start = time.time()
        main.sender(main.producer(100), self.update, 0.01, 0)
        end = time.time()
        self.assertAlmostEqual(end - start, 1, delta=0.2)

    def test_negative_mean(self):
        with self.assertRaises(ValueError):
            main.sender(self.producer, self.update, -1, 0)

    def test_negative_failure(self):
        with self.assertRaises(ValueError):
            main.sender(self.producer, self.update, 0, -1)

    def test_over_failure(self):
        with self.assertRaises(ValueError):
            main.sender(self.producer, self.update, 0, 1.1)


class TestProgressMonitor(unittest.TestCase):
    def setUp(self):
        self.sent = 0
        self.failed = 0
        self.sample_times = []
        self.monitor = main.ProgressMonitor(self.mock_display, 0.1)
        self.monitor_thread = threading.Thread(target=self.monitor.run)

    def mock_display(self, sent, failed, t):
        self.sent = sent
        self.failed = failed
        self.sample_times.append(t)

    def test_interval(self):
        if not enable_timing_tests:
            raise unittest.SkipTest("Timing tests are disabled")
        self.monitor_thread.start()
        time.sleep(0.45)
        self.monitor.stop()
        self.monitor_thread.join()
        # 6 updates at 0, 0.1, 0.2, 0.3, 0.4, stop
        self.assertEqual(len(self.sample_times), 6)
        for i in range(6):
            self.assertAlmostEqual(self.sample_times[i], i * 0.1, delta=0.01)

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
        self.assertGreater(len(self.sample_times), 0)
        self.assertGreater(self.sample_times[-1], 0)

    def test_negative_interval(self):
        with self.assertRaises(ValueError):
            main.ProgressMonitor(self.mock_display, -1)


class TestSimulator(unittest.TestCase):
    def setUp(self):
        self.sent = 0
        self.failed = 0
        self.sample_times = []
        self.variables = {
            "update_interval": 0.1,
            "num_senders": 10,
            "mean_wait_time": 0.01,
            "failure_rate": 0.4,
            "num_messages": 1000,
            "display": self.mock_display,
        }

    def mock_display(self, sent, failed, t):
        self.sent = sent
        self.failed = failed
        self.sample_times.append(t)

    def test_simple(self):
        if not enable_timing_tests:
            raise unittest.SkipTest("Timing tests are disabled")
        main.simulate(
            update_interval=1,
            num_senders=1,
            mean_wait_time=0,
            failure_rate=0,
            num_messages=5,
            display=self.mock_display,
        )
        self.assertEqual(self.sent, 5)
        self.assertEqual(self.failed, 0)
        self.assertEqual(len(self.sample_times), 2)  # 1 at start + 1 at end

    def test_simulator(self):
        if not enable_timing_tests:
            raise unittest.SkipTest("Timing tests are disabled")
        main.simulate(**self.variables)
        n = self.variables["num_messages"]
        self.assertEqual(self.sent + self.failed, n)
        self.assertAlmostEqual(
            self.failed, n * self.variables["failure_rate"], delta=n * 0.2
        )
        expected_time = (
            self.variables["num_messages"]
            / self.variables["num_senders"]
            * self.variables["mean_wait_time"]
        )
        self.assertAlmostEqual(
            self.sample_times[-1], expected_time, delta=expected_time * 0.2
        )

    def test_zero_messages(self):
        self.variables["num_messages"] = 0
        main.simulate(**self.variables)
        self.assertEqual(self.sent + self.failed, 0)
        self.assertEqual(len(self.sample_times), 2)

    def test_negative_messages(self):
        self.variables["num_messages"] = -1
        main.simulate(**self.variables)
        self.assertEqual(self.sent + self.failed, 0)
        self.assertEqual(len(self.sample_times), 2)

    def test_zero_senders(self):
        self.variables["num_senders"] = 0
        main.simulate(**self.variables)
        self.assertEqual(self.sent + self.failed, 0)
        self.assertEqual(len(self.sample_times), 2)

    def test_negative_senders(self):
        self.variables["num_senders"] = -1
        main.simulate(**self.variables)
        self.assertEqual(self.sent + self.failed, 0)
        self.assertEqual(len(self.sample_times), 2)

    def test_negative_wait_time(self):
        self.variables["mean_wait_time"] = -1
        with self.assertRaises(ValueError):
            main.simulate(**self.variables)

    def test_negative_failure_rate(self):
        self.variables["failure_rate"] = -1
        with self.assertRaises(ValueError):
            main.simulate(**self.variables)

    def test_over_failure_rate(self):
        self.variables["failure_rate"] = 1.1
        with self.assertRaises(ValueError):
            main.simulate(**self.variables)

    def test_negative_interval(self):
        self.variables["update_interval"] = -1
        with self.assertRaises(ValueError):
            main.simulate(**self.variables)


if __name__ == "__main__":
    enable_timing_tests = False
    unittest.main()
