from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User

class RegistroClienteForm(UserCreationForm):
    first_name = forms.CharField(label="Nombres", required=True)
    last_name = forms.CharField(label="Apellidos", required=True)
    email = forms.EmailField(label="Correo Electrónico", required=True)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = UserCreationForm.Meta.fields + (
            'first_name', 'last_name', 'email', 'tipo_documento', 'identificacion', 'telefono'
        )

class EditarPerfilForm(forms.ModelForm):
    email = forms.EmailField(label="Correo Electrónico", required=False)
    
    password_actual = forms.CharField(
        label="Contraseña Actual",
        widget=forms.PasswordInput,
        required=False
    )
    password_nueva = forms.CharField(
        label="Nueva Contraseña",
        widget=forms.PasswordInput,
        required=False
    )
    password_confirmar = forms.CharField(
        label="Confirmar Nueva Contraseña",
        widget=forms.PasswordInput,
        required=False
    )

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'telefono']

    def __init__(self, *args, **kwargs):
        self.user = kwargs.get('instance')
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        password_actual = cleaned_data.get('password_actual')
        password_nueva = cleaned_data.get('password_nueva')
        password_confirmar = cleaned_data.get('password_confirmar')

        if password_actual or password_nueva or password_confirmar:
            if not self.user.check_password(password_actual):
                raise forms.ValidationError("La contraseña actual es incorrecta.")
            if password_nueva != password_confirmar:
                raise forms.ValidationError("Las contraseñas nuevas no coinciden.")
            if len(password_nueva) < 8:
                raise forms.ValidationError("La nueva contraseña debe tener al menos 8 caracteres.")

        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.rol = 'CLIENTE'
        password_nueva = self.cleaned_data.get('password_nueva')
        if password_nueva:
            user.set_password(password_nueva)
        if commit:
            user.save()
        return user


class UsuarioCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 
                    'identificacion', 'tipo_documento', 'telefono', 'rol']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'identificacion': forms.TextInput(attrs={'class': 'form-control'}),
            'tipo_documento': forms.Select(attrs={'class': 'form-control'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control'}),
            'rol': forms.Select(attrs={'class': 'form-control'}),
        }


class UsuarioUpdateForm(forms.ModelForm):
    password1 = forms.CharField(
        label="Contraseña",
        widget=forms.PasswordInput,
        required=False
    )
    password2 = forms.CharField(
        label="Confirmar contraseña",
        widget=forms.PasswordInput,
        required=False
    )

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 
                    'identificacion', 'tipo_documento', 'telefono', 'rol']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'identificacion': forms.TextInput(attrs={'class': 'form-control'}),
            'tipo_documento': forms.Select(attrs={'class': 'form-control'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control'}),
            'rol': forms.Select(attrs={'class': 'form-control'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')
        if password1 or password2:
            if password1 != password2:
                raise forms.ValidationError("Las contraseñas no coinciden.")
            if len(password1) < 8:
                raise forms.ValidationError("La contraseña debe tener al menos 8 caracteres.")
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        password1 = self.cleaned_data.get('password1')
        if password1:
            user.set_password(password1)
        if commit:
            user.save()
        return user

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.required = False