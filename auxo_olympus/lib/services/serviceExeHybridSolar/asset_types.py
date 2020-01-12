import random 
import datetime 
from typing import Tuple, Dict, Any
from datetime import date, timedelta

# TODO: Code the dynamic behaviors for the solar panel and the battery


# MARK: Offers
class Offer(object):   
    def __init__(self, params, offer_type='SOLICIT', sender=None, notes=None):
        """
        offer_type: one of [BID, ASK, SOLICIT]
        """
        _time_created = datetime.datetime.now()
        self.time_created = f'{_time_created:%Y-%m-%d %H:%M:%S}'
        self.time_closed = None 

        self.offer_type = offer_type       
        self.sender = sender 
        self.closed = False 
        self.params: Dict[str, Any]= params
        self.notes = notes

    def close_offer(self):
        _time_closed = datetime.datetime.now()
        self.time_closed = f'{_time_closed:%Y-%m-%d %H:%M:%S}'
        self.closed = True 

    def get_params(self) -> Dict[str, Any]:
        return self.params

    def get_time_created(self):
        return self.time_created

    def __repr__(self):
        return f"{self.sender}: {self.params}, notes: {self.notes}"


# MARK: Assets 
class Battery(object):
    """
    rated_capacity <float>: 
    """
    def __init__(self, name, **kwargs):
        self.name = name + '-B'     # append with B for battery (for debugging)
        self.rated_capacity: float = kwargs['rated_capacity']

        self.capacity: float = 2.0 
        self.open_offers = []
        self.commitements = []

    def construct_ask(self, requested_capacity, expiration_date: datetime.datetime) -> Offer or None:
        """
        Sumbits an ask in response to a solictation by a solar-panel 
        """
        todays_date = date.today()

        assert todays_date < expiration_date, "Contract has already expired" 

        # For now, things are static # TODO: Make this not static 
        if requested_capacity > self.rated_capacity - self.capacity: 
            # Not enough capacity to provide 
            return None 
        
        else: 
            # enough capacity 
            days_till_expiration: int = (date.today() - expiration_date).days

            """
            Formula for ask price given c (requested capacity), d (days till expiration):
            f(c, d) = 2.5 * (c^2)/d
            """
            ask_price: float = 2.5 * (requested_capacity**2)/days_till_expiration
            ask_params = {'ask_price': ask_price}

            ask = Offer(ask_params, offer_type='ASK', sender=self.name)

            self.open_offers.append(ask)
    
    def ask_accepted(self, ask):
        self.remove_offer(ask)
        assert ask not in self.open_offers, "Something went wrong with the ask deletion"

        ask.close_offer()
        self.commitements.append(ask)

    def remove_offer(self, offer):
        self.open_offers.remove(offer)

    def get_percent_charge(self):
        percentage = self.capacity/self.rated_capacity
        assert percentage <= 1.0 
        return percentage


class SolarPanel(object):
    """
    rating <float>: 
    """
    def __init__(self, name, **kwargs): 
        self.name = name + '-SP'        # append with SP for solar-panel (for debugging)
        self.rating: float = kwargs['rating'] 

        self.threshold: float = 1000.0     # expected revenue that is acceptable
        self.received_asks = None          # these are the asks received from this solarpanel's battery peers

    def get_reliability(self):
        # f(x, y, ...) -> [0, 1]
        return round(random.uniform(0, 1), 2) 

    def expected_revenue(self, reliability) -> float: 
        """
        Very simple for now. Meant to use client's (reliability -> profits) mapping to compute this
        """
        return 100*reliability

    def construct_expiration_date(self) -> date:
        """
        For now, very simple, simply adds 10 days to the current date
        """
        expiration_date = date.today() + timedelta(days=10)     # FIXME: Change the date 
        return expiration_date

    def construct_requested_capacity(self) -> float: 
        """
        For now, just return a random number between 0 and self.rating
        """
        requested_capacity = random.uniform(1, self.rating)
        return round(requested_capacity, 2)

    def construct_solicitation(self) -> Offer: 
        """
        Makes some expiration date, and requested capacity, and submits the solicitation
        """
        expiration_date = self.construct_expiration_date()
        requested_capacity = self.construct_requested_capacity()

        solicitation_params = {'requested_capacity': requested_capacity, 'expiration_date': expiration_date}
        solicitation = Offer(solicitation_params, offer_type='SOLICIT', sender=self.name, notes=None)
        return solicitation 


if __name__ == "__main__":
    # MARK: Playground 
    expiration_date = date.today() + timedelta(days=10)
    print((expiration_date - date.today()).days)
