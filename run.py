import requests
import time

import config
import preferences

from random import randint
from auth import cookie, api_key, user_agent, center_id


headers = {"accept": "application/json",
           "apikey": api_key,
           "appversion": "7",
           "referer": "https://www.cure.fit/cult/classbooking/{}?centerId={}&pageType=classbooking".format(
               center_id,
               center_id
           ),
           "user-agent": user_agent,
           "dnt": "1",
           "origin": "https://www.cure.fit",
           "content-type": "application/json",
           "cookie": cookie}


def get_upcoming_classes():
    res = requests.get(config.classes_api_url.format(center_id), headers=headers)

    res_json = res.json()
    # print("res_json: ", res_json)

    return res_json['classByDateList']


def get_classes_for_today():
    class_by_date_list = get_upcoming_classes()

    return class_by_date_list[0]


def get_preferred_availability_status():
    classes_today = get_classes_for_today()
    print("Looking for preferred classes for ", classes_today['id'])

    # print("classes_today: ", classes_today)
    time_class_list = classes_today['classByTimeList']

    # Get time preference
    preferred_times = preferences.preferred_times
    preferred_classes = preferences.preferred_classes

    if preferred_times:
        print("Preference for time found: ", preferred_times)

    time_class_map = {}
    for time_class in time_class_list:
        time_class_map[time_class['id']] = time_class

    for preferred_time in preferred_times:
        print("Looking for your favourite classes at ", preferred_time)
        # print("time_class_map is: ", time_class_map)

        classes_today_at_preferred_time = time_class_map[preferred_time]

        if classes_today_at_preferred_time['disableGroup'] == True:
            print("The time slot is already booked. Skipping...")
            continue

        available_classes_id_map = {}
        for scheduled_class in classes_today_at_preferred_time['classes']:
            workout_id = scheduled_class['id']
            workout_state = scheduled_class['state']

            workout_name = scheduled_class['workoutName']

            if scheduled_class['availableSeats'] == 0:
                print("Whooaa! {} is not available!".format(workout_name))

                if workout_name not in preferred_classes:
                    print("Doesn't matter, you don't care about that! Meh!")
                # else:
                #     print("{} not available right now".format(workout_name))
            else:
                available_classes_id_map[workout_name] = workout_id

        print("Available classes for {} are: ".format(preferred_time, available_classes_id_map))

        # Now we know available classes for this day
        # Let's walk through preferences
        class_booked = False
        for preferred_class_name in preferred_classes:
            if not class_booked:
                if preferred_class_name in available_classes_id_map:
                    print("Booking your preferred class of {} for {}".format(
                        preferred_class_name,
                        preferred_time
                    ))

                    class_booked = book_class_using_id(available_classes_id_map[preferred_class_name])

                    if class_booked:
                        print("{} has been booked! My purpose is over. So long and thanks for all the fish..".format(
                            preferred_class_name))
                else:
                    print("{} is not available".format(preferred_class_name))
            else:
                print("Class already booked! WTF am I running here for? Fix me!")

        return class_booked


def book_class_using_id(class_id):
    print("I was going to book, but remembered that I haven't been implemented yet :/ Class ID: {}".format(class_id))
    # To really book or to just do a dry run
    book = True

    if book:
        booking_url = config.book_class_url.format(class_id)

        booking_status = requests.post(booking_url, headers=headers)
        print("Class booking status: {}".format(booking_status.json()))

    return class_id

def try_fav_booking():
    is_booked = False

    i = 0
    while not is_booked:
        is_booked = get_preferred_availability_status()

        sleep_time = randint(5, 20)*60
        print("\n\nSleeping for {} minutes\n\n\n\n".format(sleep_time//60))
        time.sleep(sleep_time)
        i += 1

    print("Class booked! {} attempts made. Do good with your health!\nExiting..".format(i))


if __name__ == "__main__":
    try_fav_booking()
    # get_preferred_availability_status()
