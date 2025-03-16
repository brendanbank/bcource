from wtforms import TextAreaField
from bcource.admin.content import Content

class TagMixIn(object):
    def on_form_prefill(self, form, id):
        
        if self.tag_field:
            record = self.model.query.filter(id==id).first()
            self.pkkey= f'{record.__class__.__name__}_{id}'
            
            content = Content.get_tag(self.pkkey)
                        
            form[self.tag_field_name].data = content.text
            form[self.tag_field_name].label.text += f' (tag = {self.pkkey})'
        
        return super(TagMixIn, self).on_form_prefill(form, id)

    def __init__(self,*args, **kwargs):
        
        self.tag_field = None
        self.tag_field_name = None
        if "tag_field" in kwargs:
            self.tag_field = kwargs["tag_field"]
            self.tag_field_name = f'{self.tag_field}_2'
            self.tag_field_description = None
            
            self.column_exclude_list  = list((self.tag_field,))
            self.form_excluded_columns = list((self.tag_field,))
                                              
            del(kwargs["tag_field"])

        super(TagMixIn, self).__init__(*args, **kwargs) 
        
    def scaffold_form(self):
        form_class = super(TagMixIn, self).scaffold_form()
        setattr(form_class, self.tag_field_name, TextAreaField(self.tag_field))
        return form_class

    def on_model_change(self, form, model, is_created):
        
        if form[self.tag_field_name].data != None:
            tag = Content.get_tag(self.pkkey)
            
            tag.text = form[self.tag_field_name].data
            
            update_field = getattr(model, self.tag_field)
            
            if update_field:
                update_field = self.pkkey
                
        return super(TagMixIn, self).on_model_change(form, model, is_created)
