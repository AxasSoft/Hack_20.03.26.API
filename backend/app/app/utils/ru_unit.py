def ru_unit(n, first_form, second_form, third_form):
    value = n % 20

    if value == 1:
        return first_form
    if 2 <= value <= 4:
        return second_form
    return third_form