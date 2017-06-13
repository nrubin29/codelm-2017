from django.contrib.auth.models import User

from competition.models import Division

with open('teams.csv') as raw_file:
    raw_data = raw_file.readlines()
    del raw_data[0]  # Remove the headings.

    for school in raw_data:
        [timestamp,
         teacher_name,
         teacher_school,
         teacher_email,
         teacher_phone,
         intermediate_people,
         advanced_people,
         expert_people,
         languages,
         bringing_computers,
         computer_provided,
         which_environments,
         intermediate_password,
         advanced_password,
         expert_password] = school.split(',')

        intermediate, advanced, expert = None, None, None

        if intermediate_people != '':
            intermediate = (intermediate_people.replace('|', ', '), intermediate_password.strip(), 'int', 1)

        if advanced_people != '':
            advanced = (advanced_people.replace('|', ', '), advanced_password.strip(), 'adv', 2)

        if expert_people != '':
            expert = (expert_people.replace('|', ', '), expert_password.strip(), 'exp', 3)

        for team_data in {intermediate, advanced, expert} - {None}:
            username = teacher_school.lower().replace(' ', '') + team_data[2]
            user = User.objects.create_user(username=username, password=team_data[1])

            team = user.team
            team.division = Division.objects.get(id=team_data[3])
            team.school = teacher_school
            team.people = team_data[0]
            team.save()

            print(username + ',' + team_data[1])
