import random
import time
import threading


def producer(num_messages):
    for _ in range(num_messages):
        message = "".join(
            random.choices(
                "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890",
                k=random.randint(1, 100),
            )
        )
        phone_number = "".join(random.choices("1234567890", k=10))
        yield message, phone_number


def sender(producer, update, mean_wait_time, failure_rate):
    for message, phone_number in producer:
        while random.random() < failure_rate:
            t = random.uniform(0, 2*mean_wait_time)
            time.sleep(t)
            update(False, t)
        t = random.uniform(0, 2*mean_wait_time)
        time.sleep(t)
        update(True, t)


class ProgressMonitor:
    def __init__(self, update_interval):
        self.update_interval = update_interval
        self.running = True
        self.sent = 0
        self.failed = 0
        self.sending_time = 0
        self.start_time = None

    def run(self):
        self.start_time = time.time()
        updates = 0
        while self.running:
            self.show()
            updates += 1
            wake = self.start_time + updates * self.update_interval
            time.sleep(wake - time.time())

    def show(self):
        t = time.time() - self.start_time
        sent = self.sent
        failed = self.failed
        sending_time = self.sending_time
        per_message = t / sent if sent > 0 else float("inf")
        per_sender = sending_time / sent if sent > 0 else float("inf")
        print(
            f"Sent: {sent}\nFailed: {failed}\nTime: {t:.4f}\nPer message: {per_message:.4f}\nPer message per sender: {per_sender:.4f}\n"
        )

    def update(self, success, time):
        if success:
            self.sending_time += time
            self.sent += 1
        else:
            self.failed += 1


def simulate(update_interval, num_messages, num_senders, mean_wait_time, failure_rate):
    monitor = ProgressMonitor(update_interval)
    messages = producer(num_messages)
    sender_threads = []
    for _ in range(num_senders):
        sender_thread = threading.Thread(
            target=sender,
            args=(messages, monitor.update, mean_wait_time, failure_rate),
        )
        sender_threads.append(sender_thread)
        sender_thread.start()
    threading.Thread(target=monitor.run).start()
    for sender_thread in sender_threads:
        sender_thread.join()
    monitor.running = False
    print("DONE")
    monitor.show()


if __name__ == "__main__":
    variables = {
        "num_messages": 1000,
        "num_senders": 5,
        "mean_wait_time": 1,
        "failure_rate": 0.1,
        "update_interval": 1,
    }
    simulate(**variables)
