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


@dataclass
class MessageResponse:
    success: bool


import queue

MessageQueue = queue.Queue[Message | None]
ResponseQueue = queue.Queue[MessageResponse | None]


def producer(num_messages: int, queue: MessageQueue, num_senders: int) -> None:
    for _ in range(num_messages):
        message = "".join(
            random.choices(
                string.printable,
                k=random.randint(0, 100),
            )
        )
        phone_number = "".join(random.choices("1234567890", k=10))
        queue.put(Message(message, phone_number))
    for _ in range(num_senders):
        queue.put(None)


def sender(
    messages: MessageQueue,
    responses: ResponseQueue,
    mean_wait_time: float,
    failure_rate: float,
) -> None:
    if mean_wait_time < 0:
        raise ValueError("mean_wait_time must be non-negative")
    if not 0 <= failure_rate <= 1:
        raise ValueError("failure_rate must be between 0 and 1")
    for _ in iter(messages.get, None):
        t = random.uniform(0, 2 * mean_wait_time)
        time.sleep(t)
        responses.put(MessageResponse(random.random() >= failure_rate))
    responses.put(None)


def monitor(
    responses: ResponseQueue,
    update_interval: float,
    display: Callable[[int, int, float], None],
    num_senders: int,
) -> None:
    sent = 0
    failed = 0
    start_time = time.monotonic()
    next_update = start_time + update_interval

    def count():
        nonlocal num_senders
        sent, failed = 0, 0
        while True:
            try:
                response = responses.get_nowait()
                if response is None:
                    num_senders -= 1
                    continue
                if response.success:
                    sent += 1
                else:
                    failed += 1
            except queue.Empty:
                return sent, failed

    time.sleep(update_interval)
    while num_senders > 0:
        s, f = count()
        sent += s
        failed += f
        t = time.monotonic()
        display(sent, failed, t - start_time)
        while t >= next_update:
            next_update += update_interval
        time.sleep(next_update - t)


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
    messageQueue = MessageQueue()
    responseQueue = ResponseQueue()
    threading.Thread(
        target=producer, args=(num_messages, messageQueue, num_senders)
    ).start()
    sender_threads = []
    for _ in range(num_senders):
        sender_thread = threading.Thread(
            target=sender,
            args=(messageQueue, responseQueue, mean_wait_time, failure_rate),
        )
        sender_threads.append(sender_thread)
        sender_thread.start()
    monitor_thread = threading.Thread(
        target=monitor, args=(responseQueue, update_interval, display, num_senders)
    )
    monitor_thread.start()
    for sender_thread in sender_threads:
        sender_thread.join()
    monitor_thread.join()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-n",
        "--num_messages",
        type=int,
        default=1000,
        help="Number of messages to send.",
    )
    parser.add_argument(
        "-s", "--num_senders", type=int, default=100, help="Number of sender threads."
    )
    parser.add_argument(
        "-t",
        "--mean_wait_time",
        type=float,
        default=1,
        help="Mean wait time to send a message, non-negative.",
    )
    parser.add_argument(
        "-f",
        "--failure_rate",
        type=float,
        default=0.1,
        help="Failure rate for sending messages, between 0 and 1.",
    )
    parser.add_argument(
        "-u",
        "--update_interval",
        type=float,
        default=1,
        help="Interval for updating progress, non-negative.",
    )
    parser.add_argument(
        "-d",
        "--display",
        type=str,
        default="text_then_graph",
        help="Display option for progress monitoring (text | text_then_graph | predict | none).",
    )
    variables = vars(parser.parse_args())

    def decorate(plt):
        title = ", ".join(
            f"{k}={variables[k]}"
            for k in [
                "num_messages",
                "num_senders",
                "mean_wait_time",
                "failure_rate",
            ]
        )
        plt.figure(num=title)
        plt.xlabel("Time (seconds)")
        plt.ylabel("Messages")
        plt.title(title, wrap=True)

    match variables["display"]:
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

            decorate(plt)
            plt.plot(display.times, display.sent, label="Sent")
            plt.plot(display.times, display.failed, label="Failed")
            plt.legend()
            plt.show()
        case "predict":
            n = variables["num_messages"]
            t = n * variables["mean_wait_time"] / variables["num_senders"]
            failed = n * variables["failure_rate"]
            sent = n - failed
            from matplotlib import pyplot as plt

            decorate(plt)

            plt.plot([0, t], [0, sent], label="Sent")
            plt.plot([0, t], [0, failed], label="Failed")
            plt.legend()
            plt.show()
        case x:
            raise ValueError(f"Unknown display option: {x}")
