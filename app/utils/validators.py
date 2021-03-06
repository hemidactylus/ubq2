# validators.py: custom validators for use with WTForms

from wtforms.validators import ValidationError, StopValidation

from app.utils.htmlColors import isColorExpression

# a validator is any function accepting (form,field) as arguments
# and capable of raising wtforms.validators.ValidationError

class ColorExpression():
    '''
        Validates HTML colors ('#FFCC0B', 'purple', etc)
    '''
    def __init__(self,message=None):
        if not message:
            message='Please insert an HTML color.'
        self.message=message

    def __call__(self,form,field):
        if not isColorExpression(field.data):
            raise ValidationError(self.message)

class NoDuplicateID():
    '''
        the form must have a member existingIDs=[list of str], a member thisID=str and newItem=bool
        if newItem: field must not be among the existingIds
        if not newItem: field must be == thisID
    '''
    def __init__(self,fieldname=None):
        if not fieldname:
            fieldname='ID'
        self.fieldname=fieldname

    def __call__(self,form,field):
        if form.newItem:
            if field.data in form.existingIDs:
                raise ValidationError('%s exists already.' % self.fieldname)
        else:
            if field.data != form.thisID:
                raise ValidationError('Cannot change %s.' % self.fieldname)

class IntegerString():
    '''
        Validates (optionally empty strings or) integer-looking strings
    '''
    def __init__(self, allowEmpty=True, message=None):
        if not message:
            message='Please insert a number%s.' % (' or leave blank' if allowEmpty else '')
        self.message=message
        self.allowEmpty=allowEmpty

    def __call__(self,form,field):
        if self.allowEmpty and field.data=='':
            return
        try:
            qnum=int(field.data)
        except:
            # we interrupt the validation chain since usually the next ones, if any, assume numeric
            raise StopValidation(self.message)
        return

class TimeExpression():
    '''
        Validates time-looking expressions in the form n:m with n in 0-23 and m in 0-59
    '''
    def __init__(self, message=None):
        if not message:
            message='Please insert time as "hours:minutes".'
        self.message=message

    def __call__(self,form,field):
        parts=field.data.split(':')
        if  len(parts)==2:
            try:
                _h=int(parts[0])
                _m=int(parts[1])
                if _h>23 or _h<0 or _m>59 or _m<0:
                   raise StopValidation(self.message)
            except:
                raise StopValidation(self.message)
        else:
            raise StopValidation(self.message)
