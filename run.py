import time
from random import randint

import arrow
import requests

import config
import preferences
from auth import cookie, api_key, user_agent, center_id

headers = {"accept": "application/json",
           "apikey": api_key,
           "appversion": "7",
           "referer": "https://www.cure.fit/cult/classbooking?pageFrom=cultCLP&pageType=classbooking",
           "user-agent": user_agent,
           "dnt": "1",
           "osname": "browser",
           "origin": "https://www.cure.fit",
           "content-type": "application/json",
           "cookie": cookie}


def get_upcoming_classes():
    res = requests.get(config.classes_api_url.format(center_id), headers=headers)

    res_json = res.json()
    print("res_json: ", res_json, flush=True)

    return res_json['classByDateList']


def get_classes_for_today():
    class_by_date_list = get_upcoming_classes()

    return class_by_date_list[0]


def get_classes_for_upcoming_days():
    return get_upcoming_classes()


def get_preferred_availability_status():
    upcoming_days_and_classes = get_classes_for_upcoming_days()
    count_of_upcoming_days = len(upcoming_days_and_classes)

    booked_count = 0
    for classes_on_day in upcoming_days_and_classes:
        print("\n\nLooking for preferred classes for ", classes_on_day['id'], flush=True)

        # print("classes_on_day: ", classes_on_day, flush=True)
        time_class_list = classes_on_day['classByTimeList']

        # Get time preference
        preferred_times = preferences.preferred_times
        preferred_classes = preferences.preferred_classes

        if preferred_times:
            print("Preference for time found: ", preferred_times, flush=True)

        time_class_map = {}
        for time_class in time_class_list:
            time_class_map[time_class['id']] = time_class

        for preferred_time in preferred_times:
            print("Looking for your favourite classes at ", preferred_time, flush=True)
            # print("time_class_map is: ", time_class_map)

            classes_today_at_preferred_time = time_class_map.get(preferred_time)
            if not classes_today_at_preferred_time:
                booked_count += 1
                print("No classes at preferred time found, skipping to next preferred time", flush=True)
                continue

            if classes_today_at_preferred_time['disableGroup'] == True:
                print("The time slot is already booked. Skipping...", flush=True)
                booked_count += 1
                continue

            available_classes_id_map = {}
            for scheduled_class in classes_today_at_preferred_time['classes']:
                workout_id = scheduled_class['id']
                workout_state = scheduled_class['state']

                workout_name = scheduled_class['workoutName']

                if scheduled_class['availableSeats'] == 0:
                    print("Whooaa! {} is not available!".format(workout_name), flush=True)

                    if workout_name not in preferred_classes:
                        print("Doesn't matter, you don't care about {}! Meh!".format(workout_name), flush=True)
                    # else:
                    #     print("{} not available right now".format(workout_name))
                else:
                    available_classes_id_map[workout_name] = workout_id

            # print("Available classes for {} are: ".format(preferred_time, available_classes_id_map), flush=True)

            # Now we know available classes for this day
            # Let's walk through preferences
            class_booked = False
            for preferred_class_name in preferred_classes:
                if not class_booked:
                    if preferred_class_name in available_classes_id_map:
                        # Make sure you're not booking the class at 6:55am for a 7am class
                        preferred_hour = preferred_time[0:preferred_time.find(":")]
                        preferred_minute = preferred_time[preferred_time.find(":") + 1:-1][0:2]

                        arrow_ts_at_preferred_time = arrow.now().replace(hour=preferred_hour, minute=preferred_minute)

                        secs_to_class_start = arrow_ts_at_preferred_time.timestamp - int(time.time())

                        if secs_to_class_start > preferences.booking_ban_before_class_start_time:
                            print("Booking your preferred class of {} for {}".format(
                                preferred_class_name,
                                preferred_time
                            ), flush=True)
                        else:
                            print("Less than 3 hours before class starts, not booking", flush=True)
                            continue

                        print("Booking your preferred class of {} for {}".format(
                            preferred_class_name,
                            preferred_time
                        ), flush=True)

                        class_booked = book_class_using_id(available_classes_id_map[preferred_class_name])

                        if class_booked:
                            print("{} has been booked! My purpose is over. So long and thanks for all the fish..".format(
                                preferred_class_name), flush=True)
                            booked_count += 1
                            break
                    else:
                        print("{} is not available".format(preferred_class_name), flush=True)
                else:
                    print("Class already booked! WTF am I running here for? Fix me!", flush=True)

    return bool(count_of_upcoming_days == booked_count)


def book_class_using_id(class_id):
    #print("I was going to book, but remembered that I haven't been implemented yet :/ Class ID: {}".format(class_id))
    book = True

    if book:
        booking_url = config.book_class_url.format(class_id)

        booking_status = requests.post(booking_url, headers=headers)
        print("Class booking status: {}".format(booking_status.json()), flush=True)

    return class_id


def try_in_randomized_time():
    i = 0
    while True:
        is_booked = get_preferred_availability_status()

        if not is_booked:
            sleep_time = randint(5, 20)*60
            print("\n\nSleeping for {} minutes\n\n\n\n".format(sleep_time // 60), flush=True)
            time.sleep(sleep_time)
            i += 1
        else:  # All sorted, booked!!!!
            now = arrow.now()
            t = now.time()

            arrow_ts_near_next_schedule = arrow.now().replace(hour=21, minute=randint(20, 59))
            if t.hour > 21:
                arrow_ts_near_next_schedule = arrow.now().replace(days=1, hour=21, minute=randint(20, 59))

            secs_to_next_schedule = arrow_ts_near_next_schedule.timestamp - int(time.time())
            sleep_time = secs_to_next_schedule

            # Aiming for the new day that is yet to come! Added after 10pm
            if 19 < t.hour < 23:
                # Shift gear to check more frequently
                sleep_time = randint(15, 30) * 60

            # if t.hour >= 22, Booked for the new day too!
            print("Class booked! {} attempts made. Do good with your health!\nExiting..".format(i), flush=True)

            print("\n\nSleeping for {} minutes. Gonna wake up at: {}\n\n".format(
                sleep_time // 60,
                arrow_ts_near_next_schedule),
                flush=True)
            time.sleep(sleep_time)
            print("\n\nTrying to book next day, Master!\n\n\n\n", flush=True)
            i = 0


if __name__ == "__main__":
    try_in_randomized_time()
    # get_preferred_availability_status()
