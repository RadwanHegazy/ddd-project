
from abc import ABC, abstractmethod

class AbstractNotificationClient(ABC) : 

    @abstractmethod
    def send_message(self, to : str, message : str) : 
        raise NotImplementedError()


class FakeNotificationClient(AbstractNotificationClient) : 

    def __init__(self):
        self.msgs = []

    def send_message(self, to, message):
        msg = f"Sending Message to : {to} \n {message}"
        self.msgs.append(msg)

class EmailNotificationClient(AbstractNotificationClient) : 

    def send_message(self, to, message): 
        pass

class NotificationAdapter :

    def __init__(self, client : AbstractNotificationClient):
        self.client = client

    def send (self, to : str, message : str) -> None :
        self.client.send_message(to, message)