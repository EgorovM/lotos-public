import datetime


def parse_take_text(today, city_id, hour):
    if city_id == 1:
        if hour < 13 and today.weekday() <= 4:
            delta = 1
        elif hour >= 13 and today.weekday() <= 3:
            delta = 2
        elif today.weekday() > 3:
            delta = 8 - today.weekday()
    else:
        if today.weekday() == 4:
            delta = 4
        elif hour >= 13 and today.weekday() == 3:
            delta = 4
        elif hour < 13 and today.weekday() <= 3:
            delta = 2
        elif hour >= 13 and today.weekday() <= 3:
            delta = 3
        elif today.weekday() > 3:
            delta = 9 - today.weekday()

    next_date = today + datetime.timedelta(days=delta)
    month_name = next_date.strftime('%B')

    return f'Вы можете сдать анализы {next_date.day} {month_name}';


for delta in range(-1, 6):
     d = datetime.datetime.now() + datetime.timedelta(days=delta)
     print(d.day, d.strftime('%B'), d.strftime('%A'))
     print('в спб до 13:00', parse_take_text(d, 1, 12))
     print('в спб после 13:00', parse_take_text(d, 1, 14))
     print('вне спб до 13:00', parse_take_text(d, 2, 12))
     print('вне спб после 13:00', parse_take_text(d, 2, 15))
