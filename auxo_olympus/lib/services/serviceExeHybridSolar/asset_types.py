class Battery(object):
    def __init__(self, rated_capacity):
        self.rated_capacity: float = rated_capacity
        self.capacity: float = 0.0  

    def percent_charge(self):
        percentage = self.capacity/self.rated_capacity
        assert percentage <= 1.0 
        return percentage


class SolarPanel(object):
    def __init__(self): 
        self.rating: float = 0.0 

    def reliability(self):
        # f(x, y, ...) -> [0, 1]
        return 1 
