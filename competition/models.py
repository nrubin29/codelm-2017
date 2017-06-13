from datetime import timedelta

from ckeditor.fields import RichTextField
from django.contrib.auth.models import User
from django.contrib.sessions.models import Session
from django.contrib.staticfiles.templatetags.staticfiles import static
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from solo.models import SingletonModel

LANGUAGES = (
    ('JV', 'Java'),
    ('PY', 'Python'),
    ('CP', 'C++')
)

LANGUAGE_DATA = {
    'java': {
        'short_name': 'JV',
        'codemirror': 'x/text-java'
    },
    'python': {
        'short_name': 'PY',
        'codemirror': 'x/text-python'
    },
    'cpp': {
        'short_name': 'CP',
        'codemirror': 'text/x-c++src'
    }
}

MODES = (
    ('P', 'Preliminaries'),
    ('G', 'Graded Problems'),
    ('U', 'Upload Problems'),
    ('E', 'End')
)


class Settings(SingletonModel):
    open = models.BooleanField(default=False)
    mode = models.CharField(choices=MODES, max_length=1, default='E')
    graded_ending = models.DateTimeField()
    upload_ending = models.DateTimeField()


@receiver(post_save, sender=Settings)
def settings_changed(sender, instance, created, **kwargs):
    for session in Session.objects.all():
        try:
            user = User.objects.get(id=session.get_decoded().get('_auth_user_id'))
            if not user.is_staff:
                session.delete()
        except User.DoesNotExist:
            session.delete()


class Division(models.Model):
    name = models.CharField(max_length=32)
    preliminaries = models.BooleanField(default=False)

    @property
    def problem_set(self):
        settings = Settings.objects.get()

        if settings.mode == 'G':
            return self.gradedproblem_set

        elif settings.mode == 'U':
            return self.uploadproblem_set

        else:
            return GradedProblem.objects.none()

    @property
    def problems_sorted(self):
        return self.problem_set.exclude(widget='hidden').order_by('order').all()

    @property
    def teams_sorted(self):
        return sorted(self.team_set.all(), key=lambda team: -team.score)

    def __str__(self):
        return self.name


class Team(models.Model):
    user = models.OneToOneField(User)
    division = models.ForeignKey(Division, default=1)
    school = models.CharField(max_length=32, blank=True, null=True)
    people = models.CharField(max_length=128, blank=True, null=True)
    special = models.BooleanField(default=False)
    first_login = models.DateTimeField(blank=True, null=True)

    @property
    def solved_problems(self):
        problems = []

        for problem in self.division.problem_set.order_by('-id').all():
            qs = self.submission_set.filter(problem=problem)
            if qs.exists() and qs.latest('datetime').all_correct:
                problems.append((problem, qs.latest('datetime')))

        return problems

    @property
    def unsolved_problems(self):
        problems = []

        for problem in self.division.problem_set.order_by('-id').all():
            qs = self.submission_set.filter(problem=problem)
            if not qs.exists() or not qs.latest('datetime').all_correct:
                problems.append(problem)

        return problems

    @property
    def submission_set(self):
        settings = Settings.objects.get()

        if settings.mode == 'G':
            return self.gradedsubmission_set

        elif settings.mode == 'U':
            return self.uploadsubmission_set

        else:
            return Submission.objects.none()

    @property
    def all_submissions(self):
        return list(self.gradedsubmission_set.all()) + list(self.uploadsubmission_set.all())

    @property
    def submissions_map(self):
        graded = {problem: self.gradedsubmission_set.filter(problem=problem).all() for problem in
                  self.division.gradedproblem_set.all()}
        upload = {problem: self.uploadsubmission_set.filter(problem=problem).all() for problem in
                  self.division.uploadproblem_set.all()}

        both = graded.copy()
        both.update(upload)
        return both

    def get_submissions(self, problem):
        return self.submission_set.filter(problem=problem)

    @property
    def full_name(self):
        return 'Team {} ({})'.format(self.user.id, self.division)

    @property
    def short_name(self):
        return 'Team {}'.format(self.user.id)

    @property
    def score(self):
        score = 0

        for submission in self.gradedsubmission_set.all():
            if submission.all_correct:
                score += submission.problem.points

            elif submission.compiled:
                if self.division.id != 1:
                    score -= 0.5

        for submission in self.uploadsubmission_set.all():
            score += submission.scaled_run_score + submission.judge_score

        return score

    @property
    def is_special(self):
        return self.special or self.user.is_staff

    @property
    def ending_time(self):
        if self.division.preliminaries:
            return self.first_login + timedelta(minutes=45)

        else:
            settings = Settings.objects.get()

            # NOTE: The timedelta is because the server time is off and it messes up the countdown.

            if settings.mode == 'G':
                return settings.graded_ending + timedelta(hours=5)

            elif settings.mode == 'U':
                return settings.upload_ending + timedelta(hours=5)

            else:
                return timezone.now()

    @property
    def did_end(self):
        if self.is_special:
            return False

        elif self.division.preliminaries:
            return timezone.now() > self.ending_time

        else:
            settings = Settings.objects.get()

            if settings.mode == 'E':
                return True

            elif settings.mode == 'G':
                return timezone.now() > settings.graded_ending + timedelta(hours=5)

            elif settings.mode == 'U':
                return timezone.now() > settings.upload_ending + timedelta(hours=5)

            else:
                return False

    @property
    def starter_code(self):
        return static('startercode/' + str(self.division.id) + Settings.objects.get().mode.lower() + '.zip')

    def __str__(self):
        return self.full_name


class Problem(models.Model):
    class Meta:
        abstract = True

    name = models.CharField(max_length=64)
    divisions = models.ManyToManyField(Division)
    order = models.PositiveSmallIntegerField()
    widget = models.CharField(max_length=16)
    text = RichTextField()
    short_description = models.CharField(max_length=512, blank=True, null=True)

    @property
    def widget_template(self):
        return 'widgets/{}.html'.format(self.widget)

    @property
    def full_id(self):
        return ('g' if isinstance(self, GradedProblem) else 'u') + str(self.id)

    def __str__(self):
        return self.name


class GradedProblem(Problem):
    points = models.PositiveIntegerField()
    case_sensitive = models.BooleanField(default=True, help_text='If false, test case submissions will be compared '
                                                                 'ignoring case. This is useful for problems that '
                                                                 'involve booleans')

    solution = models.TextField(default='', blank=True)

    @property
    def visible_testcase_set(self):
        return self.testcase_set.filter(hidden=False)


class UploadProblem(Problem):
    def get_points_for_team(self, team):
        submissions = self.uploadsubmission_set.order_by('run_score').all()
        points = (4, 2, 1)

        for i in range(min(3, len(submissions))):
            if submissions[i].run_score > 0 and submissions[i].team == team:
                return points[i]

        return 0


class Submission(models.Model):
    class Meta:
        abstract = True

    team = models.ForeignKey(Team)
    datetime = models.DateTimeField(default=timezone.now)

    @property
    def full_id(self):
        return ('g' if isinstance(self, GradedSubmission) else 'u') + str(self.id)

    @property
    def all_correct(self):
        """
        This can be overridden by subclasses.
        """
        return True


class GradedSubmission(Submission):
    problem = models.ForeignKey(GradedProblem)
    code = models.TextField()
    language = models.CharField(choices=LANGUAGES, max_length=2)
    compile_error = models.TextField(blank=True, null=True)
    override_correct = models.BooleanField(default=False)

    @property
    def compiled(self):
        return self.testcasesubmission_set.count() > 0

    @property
    def all_correct(self):
        if self.override_correct:
            return True

        if not self.compiled:
            return False

        for test_case_submission in self.testcasesubmission_set.all():
            if not test_case_submission.correct:
                return False

        return True

    @property
    def percent_correct(self):
        return int(
            self.testcasesubmission_set.filter(result='correct').count() / self.testcasesubmission_set.count() * 100)

    def __str__(self):
        return str(self.team) + ' for ' + str(self.problem)


class UploadSubmission(Submission):
    problem = models.ForeignKey(UploadProblem)
    run_score = models.PositiveIntegerField(default=0)
    judge_score = models.PositiveIntegerField(default=0)

    @property
    def scaled_run_score(self):
        return self.problem.get_points_for_team(self.team)

    def __str__(self):
        return str(self.team) + ' for ' + str(self.problem)


class TestCase(models.Model):
    problem = models.ForeignKey(GradedProblem)
    input = models.TextField(blank=True)
    output = models.TextField()
    hidden = models.BooleanField(default=True)

    def __str__(self):
        return 'Test case ID {} for {}'.format(self.id, self.problem.name)


class TestCaseSubmission(models.Model):
    submission = models.ForeignKey(GradedSubmission)
    test_case = models.ForeignKey(TestCase)
    output = models.TextField()
    result = models.CharField(max_length=16)

    @property
    def correct(self):
        return self.result == 'correct'


class FileSubmission(models.Model):
    submission = models.ForeignKey(UploadSubmission)
    file_name = models.CharField(max_length=32)
    code = models.TextField()

    def __str__(self):
        return self.file_name


# For Django
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        profile, created = Team.objects.get_or_create(user=instance)
