from marshmallow import Schema, fields


class StartCashSchema(Schema):
    start_cash = fields.Int(required=True)
