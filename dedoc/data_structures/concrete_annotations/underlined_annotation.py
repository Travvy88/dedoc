from flask_restx import fields, Api, Model

from dedoc.data_structures.annotation import Annotation


class UnderlinedAnnotation(Annotation):
    name = "underlined"
    valid_values = ["True", "False"]

    def __init__(self, start: int, end: int, value: str) -> None:
        try:
            bool(value)
        except ValueError:
            raise ValueError("the value of underlined annotation should be True or False")
        super().__init__(start=start, end=end, name=UnderlinedAnnotation.name, value=value)

    @staticmethod
    def get_api_dict(api: Api) -> Model:
        return api.model('UnderlinedAnnotation', {
            'start': fields.Integer(description='annotation start index', required=True, example=0),
            'end': fields.Integer(description='annotation end index', required=True, example=4),
            'value': fields.String(description='indicator if the text is underlined or not',
                                   required=True,
                                   example="True",
                                   enum=UnderlinedAnnotation.valid_values)
        })
