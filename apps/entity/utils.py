def get_form_error_code(error_type):
    if error_type is 'null':
        return 901
    elif error_type is 'invalid':
        return 902
    else:
        print(f'no error_code for {error_type}')
        return 999
