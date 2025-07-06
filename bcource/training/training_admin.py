from bcource.admin.helper import AuthModelView, CkModelView, CKTextAreaField, TagMixIn
from bcource import db, table_admin
from bcource.models import Location, Practice, Trainer, Training, TrainingType, TrainingEvent,\
    Content, Policy, Reminders


class TrainerAdmin(TagMixIn, CkModelView, AuthModelView):
    permission = "admin-trainer-edit"
    form_columns = ["user", "practice"]
    column_list = ["user", "practice"]
    

    
class PracticeAdmin(AuthModelView):
    permission = "admin-practice-edit"
    
    form_columns = ["name","shortname", "phone_number","street","address_line2","house_number","house_number_extention",
                    "postal_code","city","state","country","trainers", "locations"]
    column_list = ["name","shortname","city", "trainers"]

   
class LocationAdmin(TagMixIn, CkModelView, AuthModelView):
    permission = "admin-location-edit"

    form_columns = ["name",  "practice","phone_number", "street","address_line2",
                    "house_number","house_number_extention", "postal_code",
                    "city","state","country","latitude","longitude"]
    column_list = ["name", "practice", "street", "house_number", "city"]
    
class TrainingAdmin(AuthModelView):
    permission = "admin-training-edit"
    form_columns = ["name", "traningtype", "practice", "trainers", "trainingevents"]
    column_list = ["name", "traningtype", "practice", "trainers", "trainingevents"]


class TrainingTypeAdmin(TagMixIn, CkModelView, AuthModelView):
    permission = "admin-trainingtype-edit"
    form_columns = ["name", "practice", "policies",]
    column_list = ["name", "practice", "policies" ]
    
# class ClientTypeAdmin(AuthModelView):
#     permission = "admin-cientType-edit"
#
# class ClientAdmin(AuthModelView):
#     permission = "admin-cient-edit"

class TrainingEventAdmin(AuthModelView):
    permission = "admin-trainingevent-edit"

class PolicyAdmin(TagMixIn, CkModelView, AuthModelView):
    permission = "admin-policy-edit"
    form_columns = ["name", "trainingtypes", "practice"]
    column_list = ["name", "trainingtypes", "practice"]

table_admin.add_view(LocationAdmin(Location, db.session, category='Training', tag_field="directions"))
table_admin.add_view(PracticeAdmin(Practice, db.session, category='Training'))
table_admin.add_view(TrainerAdmin(Trainer, db.session, category='Training', tag_field="bio"))
table_admin.add_view(TrainingAdmin(Training, db.session, category='Training'))
table_admin.add_view(TrainingTypeAdmin(TrainingType, db.session, category='Training', tag_field="description"))
table_admin.add_view(TrainingEventAdmin(TrainingEvent, db.session, category='Training'))
table_admin.add_view(PolicyAdmin(Policy, db.session, category='Training', tag_field="policy"))

from wtforms import StringField
from wtforms.validators import DataRequired
from datetime import timedelta

class IntervalStringField(StringField):
    def process_data(self, value):
        # Convert timedelta to a human-readable string for display
        if isinstance(value, timedelta):
            total_seconds = int(value.total_seconds())
            days = total_seconds // (24 * 3600)
            total_seconds %= (24 * 3600)
            hours = total_seconds // 3600
            total_seconds %= 3600
            minutes = total_seconds // 60
            seconds = total_seconds % 60

            parts = []
            if days:
                parts.append(f'{days} day{"s" if not days == 1 else ""}')
            if hours:
                parts.append(f'{hours} hour{"s" if not hours == 1 else ""}')
            if minutes:
                parts.append(f"{minutes} minute{'s' if not minutes == 1 else ''}")
            if seconds:
                parts.append(f"{seconds} second{'s' if not seconds == 1 else ''}")

            if not parts and value == timedelta(0):
                self.data = "0 seconds"
            else:
                self.data = " ".join(parts)
        else:
            self.data = value

    def process_formdata(self, valuelist):
        # Convert string input back to timedelta
        if valuelist:
            try:
                # Simple parsing, you might need a more robust parser
                # For example, using a library or more complex regex
                s = valuelist[0].strip()
                if not s:
                    self.data = None
                    return

                # Basic parsing for "X days Y hours Z minutes A seconds"
                total_seconds = 0
                parts = s.split()
                i = 0
                while i < len(parts):
                    try:
                        value = int(parts[i])
                        unit = parts[i+1].lower().rstrip('s')
                        if unit == 'day':
                            total_seconds += value * 24 * 3600
                        elif unit == 'hour':
                            total_seconds += value * 3600
                        elif unit == 'minute':
                            total_seconds += value * 60
                        elif unit == 'second':
                            total_seconds += value
                        i += 2
                    except (ValueError, IndexError):
                        # Handle cases like "1 hour and 30 minutes"
                        # For simplicity, this example expects "1 hour 30 minutes"
                        # You'll likely need a more robust parsing library or design for user input.
                        self.data = None
                        raise ValueError("Invalid interval format. Use 'X days Y hours Z minutes A seconds'")
                self.data = timedelta(seconds=total_seconds)

            except ValueError as e:
                self.data = None
                raise e # Raise to show error in form
        else:
            self.data = None

class TrainingReminders(AuthModelView):
    permission = "admin-trainingevent-edit"
    column_list = ["name", "interval", "event"]
    form_columns = ["name", "interval", "event"]

    # Override the 'duration' field with your custom WTForms field
    form_overrides = {
        'interval': IntervalStringField
    }

    # If you want to customize how it appears in the list view (optional)
    column_formatters = {
        'interval': lambda s, a, d, c: str(d.interval) if d.interval else ''
    }

table_admin.add_view(TrainingReminders(Reminders, db.session, category='Training'))


