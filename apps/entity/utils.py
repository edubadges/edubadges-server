from mainsite.exceptions import BadgrApiException400


def get_form_error_code(error_type):
    if error_type is 'null':
        return 901
    elif error_type is 'invalid':
        return 902
    else:
        print(f'no error_code for {error_type}')
        return 999


def validate_errors(serializer):
    serializer.is_valid()
    errors = serializer.errors
    if errors:
        fields = {}
        for attr, field_errors in errors.items():
            fields[attr] = []
            for error in field_errors:
                fields[attr].append({
                    'error_code': get_form_error_code(vars(error)['code']),
                    'error_message': error
                })

        raise BadgrApiException400(fields)
