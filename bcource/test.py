
class Test():
    def __init__(self, taglist=None):
        
        if not taglist:
            self.taglist=[]
        else:
            self.taglist=taglist

        
        self.taglist.append(self.__class__.tag_name)
        
        print (self.taglist)

class TestC(Test):
    tag_name = "TestC"

class TestA(TestC):
    tag_name = "TestA"
    
class TestB(Test):
    tag_name = "TestB"
    
TestB()
TestA()