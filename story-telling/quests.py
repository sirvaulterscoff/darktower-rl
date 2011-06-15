class ResqueQuest(object):
    """Quest to resque someone"""
    def __init__(self, who, issuer):
        super(ResqueQuest, self).__init__()
        self.who, self.issuer = who, issuer
        


def filter_by_target(collection, type, who):
    filtered = filter(lambda x: isinstance(x, type), collection)
    return filter(lambda x: x.who == who, filtered)
