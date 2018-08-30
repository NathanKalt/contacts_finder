from django.shortcuts import render
from .forms import SignupForm
from .search import FindPerson

from django.shortcuts import (render_to_response)
from django.template import RequestContext

# Create your views here.
# HTTP Error 400
def error_404(request):
        data = {}
        return render(request,'400.html', data)

def error_500(request):
        data = {}
        return render(request,'400.html', data)

def signupform(request):
	#if form is submitted
	form = SignupForm(request.POST)
	if request.method == 'POST':
		form = SignupForm(request.POST)
	#will handle the request later
		
	if form.is_valid():		
		query =  {'name':form.cleaned_data['name'], 'keyword':form.cleaned_data['keyword'], 'location':form.cleaned_data['location']}
		find = FindPerson()
		find.query = query
		return render(request, 'getprofile.html', {	'content': find.get_data(find.query), 'form':form})
	else:
	#creating a new form
		form = SignupForm()
	#returning form 
		return render(request, 'getprofile.html', {'form':form})
