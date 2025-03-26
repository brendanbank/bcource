from collections import OrderedDict


class Menu(object):
    def __init__(self,name, url=None, role=None, parent=None):
        
        self.sub_menus = OrderedDict()
        self.urls = {}
        self.name = name
        self.url = url
        self.role = role
        self._parent = parent
        
    def add_menu(self, name, url=None, role=None):

        if not self.sub_menus.get(name):
            self.sub_menus[name] = Menu(name=name, url=url, role=role, parent=self)
                    
            self.fill_parent_urls(url, self.sub_menus[name])

        return(self.sub_menus[name])
    
    def fill_parent_urls(self,url,menu):
        if url == None:
            return None
        
        self.urls[url]=menu
        
        if self._parent and self._parent._parent:
            self._parent.urls[url]=menu
            self._parent.fill_parent_urls(url,menu)
        
            
    def active(self, endpoint):
        
        if self.url:
            if endpoint == self.url:
                return True
        else:
            if endpoint in self.urls:
                return True
            elif self._parent:
                return self._parent.active(endpoint)
        
        return False
    
    @property
    def parent_menu(self):
        if self._parent:
            return self._parent.name
        return None
    
    def __iter__(self):
        for menu in self.sub_menus.values():
            yield menu

    def __repr__(self)->str:
        return f'<{self.__class__.__name__} name = "{self.name}" url = "{self.url}" role = "{self.role}" sub_menus = "{self.sub_menus}">'


if __name__ == "__main__":
    menu_structure = Menu('root')
    main_menu = menu_structure.add_menu('t-admin', role='trainer')
    main_menu.add_menu('Training Administration', 'training_bp.index', role='trainer')
    main_menu = menu_structure.add_menu('t-admin', role='trainer')
    main_menu.add_menu('Student Administration', 'student_bp.index', role='trainer')
    
    # print (menu_structure)
    # print (main_menu)
    # print (main_menu.sub_menus)
    #
    for i in menu_structure:
        print (i.name)
        for y in i:
            print (y.name)
    
    
