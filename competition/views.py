import hashlib

from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import authenticate, login as django_login, logout as django_logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.shortcuts import resolve_url
from django.template import loader
from django.utils import timezone

from codelm.coderunner import JavaRunner, PythonRunner, File, CppRunner
from competition.models import GradedProblem, GradedSubmission, Division, TestCaseSubmission, LANGUAGE_DATA, \
    UploadProblem, Settings, UploadSubmission, FileSubmission
from competition.templatetags import tags
from competition.templatetags.tags import solved


def index(request):
    if Settings.objects.get().mode == 'E' and not request.user.is_staff:
        return end(request)

    if request.user.is_authenticated():
        if request.user.is_staff:
            return judge(request)

        else:
            return dashboard(request)

    else:
        return login(request)


def login(request):
    status = 'none'

    if request.method == 'POST':
        status = api_login(request)

        if status == 'success':
            return HttpResponseRedirect(resolve_url('index'))

    template = loader.get_template('login.html')
    context = {
        'settings': Settings.objects.get(),
        'status': status,
        'prelim_divisions': Division.objects.filter(preliminaries=True).all()
    }
    return HttpResponse(template.render(context, request))


@login_required
def dashboard(request):
    template = loader.get_template('dashboard.html')
    context = {
        'team': request.user.team,
        'problems': request.user.team.division.problems_sorted
    }
    return HttpResponse(template.render(context, request))


@login_required
def problem(request, problem_id):
    problem_type = problem_id[0].upper()
    problem_id = problem_id[1:]

    if problem_type == 'G':
        prob = GradedProblem.objects.get(id=problem_id)

    elif problem_type == 'U':
        prob = UploadProblem.objects.get(id=problem_id)

    else:
        return HttpResponseRedirect(resolve_url('index'))

    if problem_type != Settings.objects.get().mode:
        return HttpResponseRedirect(resolve_url('index'))

    if tags.solved(request.user.team, prob):
        return HttpResponseRedirect(resolve_url('index'))

    submissions = request.user.team.submission_set.filter(problem=prob).all()

    template = loader.get_template('graded-problem.html' if problem_type == 'G' else 'upload-problem.html')
    context = {
        'team': request.user.team,
        'problem': prob,
        'submissions': submissions,
        'latest_submission': submissions.latest('datetime') if submissions.count() > 0 else None
    }
    return HttpResponse(template.render(context, request))


@login_required
def judge(request):
    template = loader.get_template('judge.html')
    context = {
        'team': request.user.team,
        'divisions': Division.objects.filter(preliminaries=Settings.objects.get().mode == 'P').all()
    }
    return HttpResponse(template.render(context, request))


@login_required
def submission(request, submission_id):
    problem_type = submission_id[0].upper()
    submission_id = submission_id[1:]

    if problem_type == 'G':
        sub = GradedSubmission.objects.get(id=submission_id)

    elif problem_type == 'U':
        sub = UploadSubmission.objects.get(id=submission_id)

    else:
        return HttpResponseRedirect(resolve_url('index'))

    if not request.user.is_staff and (problem_type != Settings.objects.get().mode or sub.team != request.user.team):
        return HttpResponseRedirect(resolve_url('index'))

    template = loader.get_template('graded-submission.html' if problem_type == 'G' else 'upload-submission.html')
    context = {
        'team': request.user.team,
        'submission': sub,
    }
    return HttpResponse(template.render(context, request))


def end(request):
    template = loader.get_template('end.html')
    context = {
        'countdown': False,
        'divisions': Division.objects.filter(id__in=(1, 2, 3)).all()
    }
    return HttpResponse(template.render(context, request))

# APIs


def api_login(request):
    settings = Settings.objects.get()

    if request.POST['type'] == 'register':
        if settings.mode != 'P':
            return 'registration_closed'

        if User.objects.filter(username=request.POST['username']).exists():
            return 'username_taken'

        user = User.objects.create_user(username=request.POST['username'], password=request.POST['password'])

        team = user.team
        team.division = Division.objects.get(id=request.POST['division'])
        team.save()

    user = authenticate(username=request.POST['username'], password=request.POST['password'])

    if user:
        team = user.team

        if not team.is_special and not settings.open:
            return 'closed'

        django_login(request, user)

        if not team.first_login:
            team.first_login = timezone.now()
            team.save()

    return 'success' if request.user.is_authenticated() else 'failure'


@login_required
def api_logout(request):
    django_logout(request)
    return HttpResponseRedirect(resolve_url('index'))


@staff_member_required
def api_edit_submission(request):
    if request.method != 'POST':
        return HttpResponseRedirect(resolve_url('submission', submission_id=request.POST['submission-id']))

    submission_id = request.POST['submission-id']
    problem_type = submission_id[0].upper()
    submission_id = submission_id[1:]

    if problem_type == 'G':
        sub = GradedSubmission.objects.get(id=submission_id)

    elif problem_type == 'U':
        sub = UploadSubmission.objects.get(id=submission_id)

    else:
        return HttpResponseRedirect(resolve_url('index'))

    if request.POST['action'] == 'delete':
        sub.delete()
        return HttpResponseRedirect(resolve_url('index'))

    elif request.POST['action'] == 'correct':
        sub.override_correct = True
        sub.save()
        return HttpResponseRedirect(resolve_url('submission', submission_id=sub.full_id))

    elif request.POST['action'] == 'score':
        sub.run_score = request.POST['run-score']
        sub.judge_score = request.POST['judge-score']
        sub.save()
        return HttpResponseRedirect(resolve_url('submission', submission_id=sub.full_id))

    else:
        raise Exception('Invalid action.')


@login_required
def api_widget(request):
    if request.method != 'POST':
        return HttpResponseRedirect(resolve_url('index'))

    post = request.POST.dict()
    post.pop('csrfmiddlewaretoken')

    team = request.user.team
    problem = GradedProblem.objects.get(id=post.pop('problem-id'))

    if not solved(team, problem):
        return HttpResponse('broken')

    runner = PythonRunner(folder_name=problem.id, files=[File(problem.name.replace(' ', '') + '.py', code=problem.solution)])
    data = runner.go('\n'.join([post[key] for key in sorted(post)]))[1]

    if not problem.case_sensitive:
        data = data.lower()

    return HttpResponse(data)


@login_required
def api_file(request, file_id):
    file = FileSubmission.objects.get(id=file_id)
    team = file.submission.team

    if not request.user.is_staff and team != request.user.team:
        return HttpResponseRedirect(resolve_url('index'))

    return HttpResponse(file.code)


@login_required
def api_submit(request, problem_id):
    if request.method != 'POST':
        return HttpResponseRedirect(resolve_url('problem', problem_id=problem_id))

    problem_type = problem_id[0].upper()
    problem_id = problem_id[1:]

    if problem_type == 'G':
        prob = GradedProblem.objects.get(id=problem_id)

    elif problem_type == 'U':
        prob = UploadProblem.objects.get(id=problem_id)

    else:
        return HttpResponseRedirect(resolve_url('index'))

    if problem_type != Settings.objects.get().mode:
        return HttpResponseRedirect(resolve_url('index'))

    if tags.solved(request.user.team, prob):
        return HttpResponseRedirect(resolve_url('index'))

    team = request.user.team

    if problem_type == 'G':
        submission = GradedSubmission(team=team, problem=prob, code=request.POST['code'],
                                      language=LANGUAGE_DATA[request.POST['language']]['short_name'])
        submission.save()

        if request.POST['code'].strip() == '':
            submission.compile_error = 'Empty file.'
            submission.save()

        else:
            if request.POST['language'] == 'java':
                runner = JavaRunner(folder_name=submission.id,
                                    files=[File(prob.name.replace(' ', '') + '.java', code=request.POST['code'])])

            elif request.POST['language'] == 'python':
                runner = PythonRunner(folder_name=submission.id,
                                      files=[File(prob.name.replace(' ', '') + '.py', code=request.POST['code'])])

            elif request.POST['language'] == 'cpp':
                runner = CppRunner(folder_name=submission.id,
                                   files=[File(prob.name.replace(' ', '') + '.cpp', code=request.POST['code'])])

            else:
                raise Exception('Invalid language {}.'.format(request.POST['language']))

            success, output = runner.setup()

            if not success:
                submission.compile_error = output
                submission.save()

            else:
                for test_case in prob.testcase_set.all():
                    success, output = runner.go(test_case.input)
                    output = '\n'.join([line.strip() for line in output.splitlines()])
                    test_case_output = '\n'.join([line.strip() for line in test_case.output.splitlines()])

                    if prob.case_sensitive:
                        correct = output == test_case_output

                    else:
                        correct = output.lower() == test_case_output.lower()

                    test_case_submission = TestCaseSubmission(submission=submission, test_case=test_case, output=output,
                                                              result='correct' if correct else 'incorrect')
                    test_case_submission.save()

    elif problem_type == 'U':
        submission = UploadSubmission(team=team, problem=prob)
        submission.save()

        for file in request.FILES.getlist('files'):
            file_submission = FileSubmission(submission=submission, file_name=file._name, code=''.join([chunk.decode() for chunk in file.chunks()]))
            file_submission.save()

    else:
        return HttpResponseRedirect(resolve_url('index'))

    return HttpResponseRedirect(resolve_url('submission', submission_id=submission.full_id))
