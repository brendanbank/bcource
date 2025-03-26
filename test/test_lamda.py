


class Test():
    def __init__(self):
        self.counter = 1
        self.data = lambda : self.increate_counter
    
    
    @property
    def increate_counter(self):
        self.counter += 1
        return self.counter
    
    
print (1)

test = Test()
x = test.data()



print (test.data())
print (test.data())
print (test.data())
print (test.data())

    

