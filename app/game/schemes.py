from marshmallow import Schema, fields


class ChatStatRequestSchema(Schema):
    chat_id = fields.Int(required=True)


class ChatStatResponseSchema(Schema):
    games_played = fields.Int(required=True)
    casino_cash = fields.Int(required=True)
