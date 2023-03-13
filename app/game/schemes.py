from marshmallow import Schema, fields


class ChatStatRequestSchema(Schema):
    chat_id = fields.Int(required=True)


class ChatStatResponseSchema(Schema):
    games_played = fields.Int(required=True)
    casino_cash = fields.Int(required=True)


class UserStatRequestSchema(Schema):
    user_id = fields.Int(required=True)


class UserStatResponseSchema(Schema):
    user_id = fields.Int(required=True)
    number_of_gamechats = fields.Int(required=True)
    player_stat = fields.Nested("PlayerStatSchema", many=True)


class PlayerStatSchema(Schema):
    game_id = fields.Int(required=True)
    games_played = fields.Int(required=True)
    games_won = fields.Int(required=True)
    games_lost = fields.Int(required=True)
