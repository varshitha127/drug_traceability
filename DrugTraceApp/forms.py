from django import forms
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from .models import Drug, DrugTrace

class DrugForm(forms.ModelForm):
    """Form for adding/editing drugs"""
    
    class Meta:
        model = Drug
        fields = [
            'name',
            'batch_number',
            'manufacturing_date',
            'expiry_date',
            'quantity',
            'description',
            'image'
        ]
        widgets = {
            'manufacturing_date': forms.DateInput(attrs={'type': 'date'}),
            'expiry_date': forms.DateInput(attrs={'type': 'date'}),
            'description': forms.Textarea(attrs={'rows': 4})
        }
    
    def clean(self):
        cleaned_data = super().clean()
        manufacturing_date = cleaned_data.get('manufacturing_date')
        expiry_date = cleaned_data.get('expiry_date')
        
        if manufacturing_date and expiry_date:
            if manufacturing_date > expiry_date:
                raise forms.ValidationError(
                    "Expiry date must be after manufacturing date"
                )
            
            if manufacturing_date > timezone.now().date():
                raise forms.ValidationError(
                    "Manufacturing date cannot be in the future"
                )
        
        return cleaned_data
    
    def clean_quantity(self):
        quantity = self.cleaned_data.get('quantity')
        if quantity is not None:
            if quantity < 1:
                raise forms.ValidationError(
                    "Quantity must be at least 1"
                )
            if quantity > 1000000:  # Reasonable upper limit
                raise forms.ValidationError(
                    "Quantity seems unreasonably high"
                )
        return quantity

class DrugTraceForm(forms.ModelForm):
    """Form for updating drug tracing information"""
    
    class Meta:
        model = DrugTrace
        fields = [
            'action',
            'location',
            'quantity',
            'notes'
        ]
        widgets = {
            'notes': forms.Textarea(attrs={'rows': 4})
        }
    
    def clean(self):
        cleaned_data = super().clean()
        action = cleaned_data.get('action')
        quantity = cleaned_data.get('quantity')
        
        if action and quantity is not None:
            if action in ['shipped', 'received', 'sold'] and quantity < 1:
                raise forms.ValidationError(
                    f"Quantity must be at least 1 for {action} action"
                )
        
        return cleaned_data
    
    def clean_quantity(self):
        quantity = self.cleaned_data.get('quantity')
        if quantity is not None:
            if quantity < 0:
                raise forms.ValidationError(
                    "Quantity cannot be negative"
                )
            if quantity > 1000000:  # Reasonable upper limit
                raise forms.ValidationError(
                    "Quantity seems unreasonably high"
                )
        return quantity

class SearchForm(forms.Form):
    """Form for searching drugs"""
    query = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': 'Search by name, batch number, or manufacturer...',
            'class': 'form-control'
        })
    )
    
    def clean_query(self):
        query = self.cleaned_data.get('query', '').strip()
        if len(query) < 2:
            raise forms.ValidationError(
                "Search query must be at least 2 characters long"
            )
        return query 