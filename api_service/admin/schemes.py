from marshmallow import Schema, fields


class AdminLoginSchema(Schema):
    email = fields.Str(required=True)
    password = fields.Str(required=True, load_only=True)


class AdminCurrentSchema(Schema):
    id = fields.Int(required=False)
    email = fields.Str(required=True)
