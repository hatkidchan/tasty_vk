import json


class KeyboardColors:
    PRIMARY = 'primary'
    SECONDARY = 'secondary'
    POSITIVE = 'positive'
    NEGATIVE = 'negative'


class KeyboardButton:
    def __init__(self,
                 text='Text',
                 payload=None,
                 color=KeyboardColors.PRIMARY):
        self.text = text
        self.payload = payload
        self.color = color

    def jsonify(self):
        payload = self.payload or {}
        if not isinstance(payload, str):
            payload = json.dumps(payload)
        return {
            'action': {
                'type': 'text',
                'payload': payload,
                'label': self.text
            },
            'color': self.color
        }


class KeyboardLayout:
    def __init__(self, one_time=False):
        self.one_time = one_time
        self.buttons = []

    def append(self, *buttons):
        if len(self.buttons) == 10:
            raise IndexError('Keyboard items count reached limit')
        if len(buttons) > 4:
            raise IndexError('Row size reached limit of 4 items')
        for btn in buttons:
            if not isinstance(btn, KeyboardButton):
                message = 'Element must be a KeyboardButton, not %r' % type(btn)
                raise TypeError(message)
        self.buttons.append(list(buttons))

    def jsonify(self):
        buttons = [
            [
                btn.jsonify()
                for btn
                in row
            ] for row
            in self.buttons
        ]
        return json.dumps({
            'buttons': buttons,
            'one_time': self.one_time,
        })


class InlineKeyboardLayout(KeyboardLayout):
    def __init__(self):
        super().__init__()
        self.buttons = []

    def jsonify(self):
        buttons = [
            [
                btn.jsonify()
                for btn
                in row
            ] for row
            in self.buttons
        ]
        return json.dumps({
            'buttons': buttons,
            'inline': True,
        })

