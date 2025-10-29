from django.forms import TextInput, EmailInput, Textarea, ModelForm

from django import forms
from main.models import ContactMessage, Author


class ContactForm(ModelForm):
    class Meta:
        model = ContactMessage
        fields = ['name', 'email', 'subject', 'message']
        widgets = {
            'name': TextInput(attrs={'class': 'form-control p-4', 'placeholder': 'Your Name'}),
            'email': EmailInput(attrs={'class': 'form-control p-4', 'placeholder': 'Your Email'}),
            'subject': TextInput(attrs={'class': 'form-control p-4', 'placeholder': 'Subject'}),
            'message': Textarea(attrs={'class': 'form-control p-4', 'placeholder': 'Message', 'rows': 6}),
        }


class MessageAuthorForm(forms.Form):
    authors = forms.ModelMultipleChoiceField(
        queryset=Author.objects.filter(is_active=True).order_by('last_name', 'first_name'),
        widget=forms.SelectMultiple(attrs={
            'size': '12',
            'class': 'block w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500'
        }),
        required=False,
        label="Select Specific Authors"
    )

    send_to_all = forms.BooleanField(
        required=False,
        label="Send to ALL active authors (overrides specific selection)",
        help_text="If checked, the message will be sent to all active authors.",
        widget=forms.CheckboxInput(attrs={
            'class': 'h-4 w-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500'
        })
    )

    subject = forms.CharField(
        max_length=255,
        widget=forms.TextInput(attrs={
            'placeholder': 'Subject of the message',
            'class': 'block w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500'
        })
    )

    message = forms.CharField(
        widget=forms.Textarea(attrs={
            'rows': 10,
            'placeholder': 'Your message content here...',
            'class': 'block w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500'
        }),
        help_text="The message will be sent to the selected authors' emails."
    )

    def clean(self):
        cleaned_data = super().clean()
        send_to_all = cleaned_data.get('send_to_all')
        authors = cleaned_data.get('authors')
        if not send_to_all and (not authors or authors.count() == 0):
            self.add_error(None, "Please select at least one author or check 'Send to ALL active authors'.")
        return cleaned_data
