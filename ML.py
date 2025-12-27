import random
class MLWrapper():
    def __init__(self, controller):
        self.controller = controller



    def getmove(self, v):
        ''' currently just returns a random move'''
        return random.choice(self.controller.get_all_actions())