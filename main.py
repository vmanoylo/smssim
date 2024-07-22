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
    update: Callable[[bool], None],
    mean_wait_time: float,
    failure_rate: float,
) -> None:
    if mean_wait_time < 0:
        raise ValueError("mean_wait_time must be non-negative")
    if not 0 <= failure_rate <= 1:
        raise ValueError("failure_rate must be between 0 and 1")
    for _ in producer:
        t = random.uniform(0, 2 * mean_wait_time)
        time.sleep(t)
        update(random.random() >= failure_rate)


class ProgressMonitor:
    def __init__(
        self, display: Callable[[int, int, float], None], update_interval: float
    ) -> None:
        if update_interval < 0:
            raise ValueError("update_interval must be non-negative")
        self.display = display
        self.update_interval = update_interval
        self.running = True
        self.sent = 0
        self.failed = 0
        self.sending_time = 0
        self.start_time = None

    def run(self) -> None:
        self.start_time = time.time()
        wake = self.start_time
        while self.running:
            self.show()
            wake += self.update_interval
            wait = wake - time.time()
            if wait > 0:
                time.sleep(wake - time.time())
            else:  # skipped frame
                wake = time.time()
        self.show()

    def stop(self) -> None:
        self.running = False

    def show(self) -> None:
        t = time.time() - self.start_time
        sent = self.sent
        failed = self.failed
        self.display(sent, failed, t)

    def update(self, success: bool) -> None:
        if success:
            self.sent += 1
        else:
            self.failed += 1


def text_display(sent: int, failed: int, t: float) -> None:
    messages = sent + failed
    per_sent = t / sent if sent > 0 else float("inf")
    per_message = t / messages if messages > 0 else float("inf")
    print(
        f"Sent: {sent}\nFailed: {failed}\nTime: {t:.4f}\nPer message: {per_message:.4f}\nPer sent message: {per_sent:.4f}\n"
    )


class TrackingTextDisplay:
    def __init__(self):
        self.sent = []
        self.failed = []
        self.times = []

    def display(self, sent: int, failed: int, t: float) -> None:
        self.sent.append(sent)
        self.failed.append(failed)
        self.times.append(t)
        text_display(sent, failed, t)


def simulate(
    update_interval: float,
    num_senders: int,
    mean_wait_time: float,
    failure_rate: float,
    num_messages: int = 1000,
    display: Callable[[int, int, float], None] = text_display,
) -> None:
    if mean_wait_time < 0:
        raise ValueError("mean_wait_time must be non-negative")
    if not 0 <= failure_rate <= 1:
        raise ValueError("failure_rate must be between 0 and 1")
    if update_interval < 0:
        raise ValueError("update_interval must be non-negative")
    monitor = ProgressMonitor(display, update_interval)
    messages = producer(num_messages)
    sender_threads = []
    for _ in range(num_senders):
        sender_thread = threading.Thread(
            target=sender,
            args=(messages, monitor.update, mean_wait_time, failure_rate),
        )
        sender_threads.append(sender_thread)
        sender_thread.start()
    monitor_thread = threading.Thread(target=monitor.run)
    monitor_thread.start()
    for sender_thread in sender_threads:
        sender_thread.join()
    monitor.stop()
    monitor_thread.join()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--num_messages", type=int, default=1000, help="Number of messages to send."
    )
    parser.add_argument(
        "--num_senders", type=int, default=100, help="Number of sender threads."
    )
    parser.add_argument(
        "--mean_wait_time",
        type=float,
        default=1,
        help="Mean wait time to send a message, non-negative.",
    )
    parser.add_argument(
        "--failure_rate",
        type=float,
        default=0.1,
        help="Failure rate for sending messages, between 0 and 1.",
    )
    parser.add_argument(
        "--update_interval",
        type=float,
        default=1,
        help="Interval for updating progress, non-negative.",
    )
    parser.add_argument(
        "--display",
        type=str,
        default="text_then_graph",
        help="Display option for progress monitoring (text | text_then_graph | none).",
    )
    args = parser.parse_args()

    variables = vars(args)
    end_display = False
    match args.display:
        case "none":
            variables["display"] = lambda *_: None
            simulate(**variables)
        case "text":
            variables["display"] = text_display
            simulate(**variables)
        case "text_then_graph":
            display = TrackingTextDisplay()
            variables["display"] = display.display
            simulate(**variables)
            from matplotlib import pyplot as plt

            title = f"num_messages={args.num_messages}, num_senders={args.num_senders}, mean_wait_time={args.mean_wait_time}, failure_rate={args.failure_rate}"
            plt.figure(num=title)
            plt.plot(display.times, display.sent, label="Sent")
            plt.plot(display.times, display.failed, label="Failed")
            plt.xlabel("Time (seconds)")
            plt.ylabel("Messages")
            plt.title(title, wrap=True)
            plt.legend()
            plt.show()
        case _:
            raise ValueError(f"Unknown display option: {args.display}")
