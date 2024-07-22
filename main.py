import random
import time
import threading
import argparse
import string
from typing import Iterable, Callable
from dataclasses import dataclass


@dataclass
class Message:
    message: str
    phone: str


MessageQueue = Iterable[Message]


def producer(num_messages: int) -> MessageQueue:
    for _ in range(num_messages):
        message = "".join(
            random.choices(
                string.printable,
                k=random.randint(0, 100),
            )
        )
        phone_number = "".join(random.choices("1234567890", k=10))
        yield Message(message, phone_number)


def sender(
    producer: MessageQueue,
    update: Callable[[bool, float], None],
    mean_wait_time: float,
    failure_rate: float,
) -> None:
    for _ in producer:
        t = random.uniform(0, 2 * mean_wait_time)
        time.sleep(t)
        update(random.random() >= failure_rate, t)


class ProgressMonitor:
    def __init__(self, update_interval: float) -> None:
        self.update_interval = update_interval
        self.running = True
        self.sent = 0
        self.failed = 0
        self.sending_time = 0
        self.start_time = None

    def run(self) -> None:
        self.start_time = time.time()
        updates = 0
        while self.running:
            self.show()
            updates += 1
            wake = self.start_time + updates * self.update_interval
            time.sleep(wake - time.time())

    def stop(self) -> None:
        self.running = False

    def show(self) -> None:
        t = time.time() - self.start_time
        sent = self.sent
        failed = self.failed
        messages = sent + failed
        per_sent = t / sent if sent > 0 else float("inf")
        per_message = t / messages if messages > 0 else float("inf")
        print(
            f"Sent: {sent}\nFailed: {failed}\nTime: {t:.4f}\nPer message: {per_message:.4f}\nPer sent message: {per_sent:.4f}\n"
        )

    def update(self, success: bool, time: float) -> None:
        if success:
            self.sending_time += time
            self.sent += 1
        else:
            self.failed += 1


def simulate(
    update_interval: float,
    num_senders: int,
    mean_wait_time: float,
    failure_rate: float,
    num_messages: int = 1000,
) -> None:
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
    monitor.stop()
    print("DONE")
    monitor.show()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--num_messages", type=int, default=1000)
    parser.add_argument("--num_senders", type=int, default=100)
    parser.add_argument("--mean_wait_time", type=float, default=1)
    parser.add_argument("--failure_rate", type=float, default=0.1)
    parser.add_argument("--update_interval", type=float, default=1)
    args = parser.parse_args()

    variables = {
        "num_messages": args.num_messages,
        "num_senders": args.num_senders,
        "mean_wait_time": args.mean_wait_time,
        "failure_rate": args.failure_rate,
        "update_interval": args.update_interval,
    }

    simulate(**variables)
