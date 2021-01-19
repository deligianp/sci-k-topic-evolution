from django import forms


class NewArticleForm(forms.Form):
    article_text_field = forms.CharField(widget=forms.Textarea(
        attrs={
            "class": "form-control",
            "placeholder": "Text to analyze to topics",
            "autocomplete": "off",
            "style": "resize:none"
        }
    ))