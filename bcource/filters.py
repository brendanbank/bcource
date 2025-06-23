from flask import request, g


class Filters():
    def __init__(self, name):
        self.name = name
        self.filters = []
        self.filter_ids = 0
        self.filter_dict = {}
        
        if g.is_mobile == True:
            self.filters_checked = False
            self.show = False
        else:
            self.filters_checked = True
            self.show = True

    def _add_filter(self, filter):
        self.filters.append(filter)
        self.filter_dict[filter.id] = filter
        
    def __iter__(self):
        for filter in self.filters:
            yield filter
            
    def new_filter(self, id, text):
        filter = Filter(id, text)
        self._add_filter(filter)
        return (filter)
    
    def get_filter(self,id):
        if id in self.filter_dict.keys():
            return self.filter_dict[id]
        
        return None
    
    def process_filters(self):    
        for filter in self.filters:
            items =  request.args.getlist(filter.id)
            
            if len(items):
                self.filters_checked = True
                
            for item in items:
                
                filter.item_check(item)

                
        show_submit = request.args.get('show_submit', None)
        show = request.args.get('show', None)
        
        if  show_submit == str("noshow") or show_submit == None and not self.filters_checked and not show :
            self.show = False
        else:
            self.show = True

        return(self)

    def __repr__(self)->str:
        return f'<{self.__class__.__name__} name="{self.name}, filters="{self.filters}">'

    def get_item_is_checked(self,id, value):
        if self.get_filter(id) and  self.get_filter(id).get_item(value):
            return self.get_filter(id).get_item(value).checked
        
        else:
            return False

    def get_items_checked(self, id):
        if self.get_filter(id):
            return self.get_filter(id).get_items_checked()
        return []

class Filter():
    def __init__(self, id, name):
        self.id = id
        self.name = name
        self.filter_items = []
        self.filter_items_dict = {}
    
    def add_filter_item(self, id, name):
        item = FilterItem(id,name)
        self.filter_items.append(item)
        self.filter_items_dict[str(id)] = item
        
    def item_check(self,item_id):
        if str(item_id) in self.filter_items_dict:
            self.filter_items_dict[str(item_id)].checked = True
            
    def get_item(self, id):
        if str(id) in self.filter_items_dict:
            return self.filter_items_dict[str(id)]
        else:
            print (f'not id: {id} items{self.filter_items_dict}')

    def get_items_checked(self):
        items = []
        for item in self.filter_items:
            if item.checked:
                items.append(item.id)
                
        return (items)
    
    def __iter__(self):
        for item in self.filter_items:
            yield item
            
    def __repr__(self)->str:
        return f'<{self.__class__.__name__} id = {self.id} name="{self.name}, filter_items="{self.filter_items}">'
    
class FilterItem():
    def __init__(self, id, name):
        self.name = name
        self.id = id
        self.checked = False
        
    def __repr__(self)->str:
        return f'<{self.__class__.__name__} id = {self.id} name="{self.name}, checked="{self.checked}">'

