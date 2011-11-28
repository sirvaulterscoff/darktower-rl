class PartitionedQueue:
    """ Idea taken from http://roguebasin.roguelikedevelopment.org/index.php/A_priority_queue_based_turn_scheduling_system
    This collection holds list of elements, which can be retrieved using dequeue() method.
    Each item in list is a tuple(priority, value). Queue has waterline, which limits the number of elements to be retrieved.
    If an element has cost greater than waterline None is returned
    """
    def __init__(self):
        self.__queue = []
        self.waterline = 0.0

    def __len__(self):
        return len(self.__queue)

    def enqueue(self, value, cost = 0.0):
        """
            Append a new element to the queue
            according to its priority.
        """

        tuple = [cost, value]

        # Insert the tuple in sorted position in the queue.  If a
        # tuple with equal priority is encountered, the new tuple is
        # inserted after it.

        finalPos = 0
        high = len(self)
        while finalPos < high:
            middle = (finalPos + high) // 2
            if tuple[0] < self.__queue[middle][0]:
                high = middle
            else:
                finalPos = middle + 1

        self.__queue.insert(finalPos, tuple)

    def dequeue(self):
        """
            Pop the value with the lowest priority.
        """
        if not len(self.__queue):
            return None
        if self.__queue[0][0] > self.waterline:
            return None

        return self.__queue.pop(0)[1]

    def erase(self, value):
        """
            Removes an element from the queue by value.
        """

        self.__erase(value, lambda a, b: a == b)

    def adjustPriorities(self, add):
        """
            Increases all priorities.
        """

        for v in self.__queue:
            v[0] += add
    
    def erase_ref(self, value):
        """
            Removes an element from the queue by reference.
        """

        self.__erase(value, lambda a, b: a is b)

    def __erase(self, value, test):
        """
            All tupples t are removed from the queue
            if test(t[1], value) evaluates to True.
        """

        i = 0
        while i < len(self.__queue):
            if test(self.__queue[i][1], value):
                del self.__queue[i]
            else:
                i += 1

class Scheduler(object):
    def __init__(self):
        self._queue = PartitionedQueue()

    def schedule(self, cost, action):
        self._queue.enqueue(action, cost)

    def schedule_player_action(self, cost, action):
        self._queue.enqueue(action, cost)
        self._queue.waterline = cost

    def next_turn(self):
        self._queue.adjustPriorities(-self._queue.waterline)
        self.waterline = 0

    def set_waterline(self, cost):
        self._queue.waterline = cost
    waterline = property(fset = set_waterline)

    def get_scheduled(self):
        x = self._queue.dequeue()
        while x:
            yield x
            x = self._queue.dequeue()
