import random 
from typing import Tuple 
from datetime import date, timedelta

# TODO: Code the dynamic behaviors for the solar panel and the battery


class Battery(object):
    """
    rated_capacity <float>: 
    """
    def __init__(self, **kwargs):
        self.rated_capacity: float = kwargs['rated_capacity']
        self.capacity: float = 2.0 

    def construct_asks(self, capacity, expiration_date) -> float:
        return 0.0 

    def get_percent_charge(self):
        percentage = self.capacity/self.rated_capacity
        assert percentage <= 1.0 
        return percentage


class SolarPanel(object):
    """
    rating <float>: 
    """
    def __init__(self, **kwargs): 
        self.rating: float = kwargs['rating'] 

    def get_reliability(self):
        # f(x, y, ...) -> [0, 1]
        return round(random.uniform(0, 1), 2) 

    def construct_expiration_date(self) -> date:
        # For now, very simple, simply adds 10 days to the current date
        expiration_date = date.today() + timedelta(days=10)
        return expiration_date

    def construct_requested_capacity(self) -> float: 
        # For now, just return a random number between 0 and self.rating
        requested_capacity = random.uniform(1, self.rating)
        return round(requested_capacity, 2)

    def construct_contract(self) -> Tuple[float, date]: 
        expiration_date = self.construct_expiration_date()
        requested_capacity = self.construct_requested_capacity()

        output = (requested_capacity, expiration_date)
        return output 


if __name__ == "__main__":
    # MARK: Playground 
    print(date.today())
    print(date.today() + timedelta(days=10))
