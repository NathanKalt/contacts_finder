#importing forms
from django import forms 
 
#creating our forms
class SignupForm(forms.Form):
 #django gives a number of predefined fields
 #CharField and EmailField are only two of them
 #go through the official docs for more field details
	name = forms.CharField(label='Enter person name ', max_length=100)
	keyword = forms.CharField(label='Company name or keyword ', max_length=100)
	location = forms.CharField(label='Location ', max_length=100)