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

    @staticmethod
    def is_lower(interval_1, interval_2):
        if interval_1.right_border <= interval_2.left_border:
            return True
        else:
            return False