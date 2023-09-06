import datetime


def get_input(msg):
    out = None

    while out is None:
        out = str(input("Please add " + msg + ": "))

    return out


birthday_age = None

while birthday_age is None:
    try:
        birthday_year = abs(int(input("Please add year of birth: ")))
        today = datetime.date.today()
        current_year = today.year

        if len(str(birthday_year)) == 4 and birthday_year <= current_year:
            birthday_age = current_year - birthday_year
        else:
            print("Year can't be higher than ", current_year)
    except ValueError:
        print("Invalid birthday year")

birthday_name = get_input("birthday name")
invitation_name = get_input("your name")
personalize = get_input("personalized message")

print('\n{0} let''s celebrate your {1} years of awesomeness!\n' 
      'Wishing you a day filled \033[1mwith\033[0m joy \033[1mand\033[0m laughter \033[1mas\033[0m you ' 
      'turn {1}!\n'
      '{2}\n'
      'With love \033[1mand\033[0m best wishes,\n'
      '{3}'.format(birthday_name.capitalize(), birthday_age,
                   personalize, invitation_name.capitalize()))
