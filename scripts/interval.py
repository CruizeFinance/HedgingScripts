class Interval(object):

    def __init__(self,
                 left_border=0,
                 right_border=0,
                 name='empty'):
        self.left_border = left_border
        self.right_border = right_border
        self.name = name