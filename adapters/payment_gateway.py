from abc import ABC, abstractmethod
from domain.models import Order
import stripe,os

class AbstractPaymentGateway(ABC) : 

    @abstractmethod
    def create_checkout_url(self, order : Order) -> str : 
        raise NotImplementedError()

    @abstractmethod
    def has_valid_signature(self, **kwargs) -> bool: 
        raise NotImplementedError()


class StripePaymentGateway(AbstractPaymentGateway): 

    def __init__(self, stripe_token ):
        self._stripe_client = stripe.StripeClient(api_key=stripe_token)

    def create_checkout_url(self, order):
        line_items = []
        for item in order.items:
            line_items.append({
                'quantity' : item.quantity,
                'price_data': {
                    'currency' : 'usd',
                    'product_data' : {
                        'name' : f"Product id : " + str(item.product_id)
                    },
                    'unit_amount' : item.price * 100
                },
            })
        stripe_request = self._stripe_client.v1.checkout.sessions.create(
            params={
                "payment_method_types" : ['card'],
                "line_items": line_items,
                'mode':"payment",
                'metadata' : {'order_id' : str(order.order_id)},
                "success_url":os.environ.get("STRIPE_SUCCESS_URL"),
                "cancel_url":os.environ.get("STRIPE_CANCEL_URL"),
            }
        )
        return stripe_request.url

    def has_valid_signature(self, body,signature):
        try :
            verified = self._stripe_client.construct_event(
                body,
                signature,
                os.environ.get("STRIPE_ENDPOINT_SECRET")
            )
            return True
        except Exception as error:
            print(f"An error occurred : {error}")
            return False 
    

class FakePaymentGateway (AbstractPaymentGateway) :

    def __init__(self):
        self.payments = []

    def create_checkout_url(self, order):
        url = "https://example.com/checkout/order/" + str(order.order_id)
        self.payments.append(url)
        return url

    def has_valid_signature(self, body):
        return True


class PaymentAdapter :

    def __init__(self, service : AbstractPaymentGateway):
        self.service = service

    def checkout(self, order : Order) -> str:
        url = self.service.create_checkout_url(order)
        return url


