class Interval(object):

    def __init__(self,
                 left_border,
                 right_border,
                 name,
                 position_order):
        self.left_border = left_border
        self.right_border = right_border
        self.name = name
        self.position_order = position_order

    def is_lower(self, another_interval):
        if self.right_border <= another_interval.left_border:
            return True
        else:
            return False
