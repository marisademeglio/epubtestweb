from django.views.generic import UpdateView
from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import HttpResponse

from testsuite_app.models import *
from testsuite_app.forms import *

from . import permissions

class EditEvaluationView(UpdateView):
    template_name = "edit_evaluation.html"

    def get(self, request, *args, **kwargs):
        try:
            evaluation = Evaluation.objects.get(id=kwargs['pk'])
        except Evaluation.DoesNotExist:
            return render(request, "404.html", {})

        if permissions.user_can_edit_evaluation(request.user, evaluation) == False:
            messages.add_message(request, messages.INFO, 'You do not have permission to edit this evaluation.')
            return redirect('/')

        # epubs in this testsuite
        epubs = Epub.objects.filter(testsuite = evaluation.testsuite).order_by("epubid")
        for epub in epubs:
            epub.percent_complete = evaluation.get_epub_percent_complete(epub)
            epub.flagged = evaluation.does_epub_have_flagged_results(epub)

        evaluation_form = EvaluationForm(instance = evaluation)

        atmeta_form = None
        if evaluation.testsuite.testsuite_type == common.TESTSUITE_TYPE_ACCESSIBILITY:
            atmeta = evaluation.get_metadata()
            if atmeta == None:
                atmeta = evaluation.add_metadata("", common.INPUT_TYPE_KEYBOARD, False, False)
            else:
                print(atmeta)
            atmeta_form = ATMetadataForm(instance = atmeta)


        # after this form, the next page is the evaluation form for the first epub
        next_url = "{}section/{}/".format(request.path, epubs[0].epubid)

        return_url = request.GET.get('return', '/manage/')

        return render(request, self.template_name,{"evaluation": evaluation, "epubs": epubs,
            "evaluation_form": evaluation_form, "assistive_technology_metadata_form": atmeta_form,
            "next_url": next_url, "return_url": return_url})

    def post(self, request, *args, **kwargs):
        try:
            evaluation = Evaluation.objects.get(id=kwargs['pk'])
        except Evaluation.DoesNotExist:
            return render(request, "404.html", {})

        if permissions.user_can_edit_evaluation(request.user, evaluation) == False:
            messages.add_message(request, messages.INFO, 'You do not have permission to edit this evaluation.')
            return redirect('/manage/')

        evaluation_form = EvaluationForm(request.POST, instance = evaluation)

        evaluation_form.save()
        
        if evaluation.testsuite.testsuite_type == common.TESTSUITE_TYPE_ACCESSIBILITY:
            atmeta_form = ATMetadataForm(request.POST, instance = evaluation.get_metadata())
            atmeta_form.save()

        if 'save_continue' in request.POST.keys() and 'next_url' in request.POST.keys():
            next_url = request.POST['next_url']
            return redirect(next_url)
        else:
            return redirect(request.POST.get('return_url', '/manage/'))
