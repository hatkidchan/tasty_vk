
class BaseHandler:
    def __init__(self, callback, *args):
        self.callback = callback
        self.args = args
    
    def check(self, event):
        raise NotImplementedError
    
    def __call_(self, event):
        return self.callback(event)


class MessageHandler(BaseHandler):
    def __init__(self, callback):
        super().__init__(callback)
        
    def check(self, event):
        if isinstance(event, list):  # Users LongPoll
            return event[0] == 4
        else:  # Bots LongPoll
            return event['type'] == 'message_new'
    
    def __call_(self, event):
        if isinstance(event, list):
            return self.callback(event[1:])
        else:
            return self.callback(event)

