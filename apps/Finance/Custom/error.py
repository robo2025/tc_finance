class BusiCustomError(Exception):    def __init__(self,msg):        super(BusiCustomError,self).__init__()        self.msg = msg