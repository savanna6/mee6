import re


re_type_switch = {
    'str': ('(.*)', str),
    'int': ('([0-9]*)', int),
    'user_id': ('<@!?([0-9]*)>', int),
    'channel_id': ('<#([0-9]*)>', int),
    'role_id': ('<@&([0-9]*)>', int),
}

def build_regex(expression):
    splitted = expression.split(' ')
    rx = [splitted[0]]
    cast_to_list = []
    for argument in splitted[1:]:
        # remove the < and >
        arg = argument[1:-1]
        [argument_name, argument_type] = arg.split(':')

        argument_regex, cast_to = re_type_switch.get(argument_type)
        cast_to_list.append(cast_to)
        rx.append(argument_regex)

    return re.compile('^' + ' '.join(rx)), cast_to_list

