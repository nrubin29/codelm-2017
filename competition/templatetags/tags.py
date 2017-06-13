from django import template

from competition.models import Settings

register = template.Library()


@register.simple_tag(name='is_not_special')
def is_not_special(team):
    return team and not team.is_special


@register.filter(name='lang_mode')
def lang_mode(lang):
    return {
        'JV': 'text/x-java',
        'PY': 'text/x-python',
        'CP': 'text/x-c++src'
    }[lang]


@register.filter(name='solved')
def solved(team, problem):
    # data = team.gradedsubmission_set if Settings.objects.get().mode == 'G' else team.uploadsubmission_set
    #
    # for submission in data.filter(problem=problem).all():
    #     if submission.all_correct:
    #         return True
    #
    # return False

    return any([submission.all_correct for prob, submission in team.solved_problems if prob == problem])


@register.filter(name='correct_submission_id')
def correct_submission_id(team, problem):
    latest = team.submission_set.filter(problem=problem).latest('datetime')

    if latest.all_correct:
        return latest.full_id

    else:
        return None
