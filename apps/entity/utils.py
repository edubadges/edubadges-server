from mainsite.exceptions import BadgrValidationError


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
                try:
                    fields[attr].append({
                        'error_code': get_form_error_code(vars(error)['code']),
                        'error_message': error
                    })
                except TypeError as e:  # TODO: make this recursive for endless depth
                    sub_fields = {}
                    for sub_attr, sub_errors in error.items():
                        sub_fields[sub_attr] = []
                        for sub_error in sub_errors:
                            sub_fields[sub_attr].append({
                                'error_code': get_form_error_code(vars(sub_error)['code']),
                                'error_message': sub_error
                            })
                    fields[attr].append(sub_fields)
        raise BadgrValidationError(error_message=fields, error_code=999)
