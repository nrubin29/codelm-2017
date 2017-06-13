from django.contrib.auth.models import User

from competition.models import Division

for div, password, div_id in (('int', 'intermediate', 1), ('adv', 'advanced', 2), ('exp', 'expertpass', 3)):
    for i in range(1, 6):
        username = 'sig' + div + str(i)

        try:
            # I forgot to mark the accounts as special so I added this instead of doing it manually :D
            user = User.objects.get(username=username)
            team = user.team
            team.special = True
            team.save()
        except User.DoesNotExist:
            user = User.objects.create_user(username=username, password=password)
            team = user.team
            team.division = Division.objects.get(id=div_id)
            team.school = 'SIG'
            team.people = 'SIG Developer'
            team.special = True
            team.save()

        print(username + ',' + password)