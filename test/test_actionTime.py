from random import randint
class MOCK:
    def __init__(self, speed):
        self.action_time = 0
        self.speed = speed


Hero = MOCK(5)
Enemy = MOCK(3)

def _action_time(Hero, Enemy):
    """ """
    combat = [Hero, Enemy]
    limit = 100

    while True:
        for fighter in combat:
            lucky = randint(-2, 10)
            fighter.action_time += fighter.speed + lucky
            if fighter.action_time >= limit:
                fighter.action_time -= limit
                return fighter
            
print(_action_time(Hero, Enemy))