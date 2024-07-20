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
        self.total_time = 0

    def run(self):
        while self.running:
            self.show()
            time.sleep(self.update_interval)

    def show(self):
        messages = self.sent + self.failed
        if messages == 0:
            return
        avg_time = self.total_time / messages if messages > 0 else float("inf")
        print(
            f"Messages sent: {self.sent}\nMessages failed: {self.failed}\nAverage time per message: {avg_time:.2f}"
        )

    def update(self, success, time):
        self.total_time += time
        if success:
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
    monitor.run()
    for sender_thread in sender_threads:
        sender_thread.join()
    print("DONE")
    monitor.show()


if __name__ == "__main__":
    variables = {
        "num_messages": 20,
        "num_senders": 5,
        "mean_wait_time": 0.1,
        "failure_rate": 0.1,
        "update_interval": 1,
    }
    simulate(**variables)
