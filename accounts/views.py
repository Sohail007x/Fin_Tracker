from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.conf import settings
from django.contrib import messages
from django.utils import timezone
from django.core.exceptions import ObjectDoesNotExist
from .forms import RegisterForm, LoginForm, OTPVerificationForm
from .models import CustomUser, OTP
import pyotp
from datetime import timedelta

def register_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False
            user.save()
            
            otp_code = OTP.generate_otp(user)
            
            try:
                send_mail(
                    'Your OTP for Account Verification',
                    f'Your OTP is: {otp_code}. It will expire in 5 minutes.',
                    settings.DEFAULT_FROM_EMAIL,
                    [user.email],
                    fail_silently=False,
                )
                messages.success(request, 'OTP sent to your email!')
            except Exception as e:
                messages.error(request, f'Failed to send OTP: {str(e)}')
                return redirect('register')
            
            request.session['otp_user_id'] = user.id
            request.session['otp_purpose'] = 'registration'
            request.session['otp_sent_time'] = str(timezone.now())
            return redirect('verify_otp')
    else:
        form = RegisterForm()
    
    return render(request, 'accounts/register.html', {'form': form})

def verify_otp_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    user_id = request.session.get('otp_user_id')
    purpose = request.session.get('otp_purpose')
    
    if not user_id or not purpose:
        messages.error(request, 'Invalid OTP verification request.')
        return redirect('register' if purpose == 'registration' else 'login')
    
    try:
        user = CustomUser.objects.get(id=user_id)
    except ObjectDoesNotExist:
        messages.error(request, 'User not found.')
        return redirect('register' if purpose == 'registration' else 'login')
    
    if request.method == 'POST':
        form = OTPVerificationForm(request.POST)
        if form.is_valid():
            otp_code = form.cleaned_data['otp']
            latest_otp = OTP.objects.filter(user=user).order_by('-created_at').first()
            
            if latest_otp and latest_otp.verify_otp(otp_code):
                if purpose == 'registration':
                    user.is_active = True
                    user.is_verified = True
                    user.save()
                
                login(request, user)
                del request.session['otp_user_id']
                del request.session['otp_purpose']
                del request.session['otp_sent_time']
                messages.success(request, 'Account verified successfully!')
                return redirect('dashboard')
            else:
                messages.error(request, 'Invalid or expired OTP.')
    else:
        form = OTPVerificationForm()
    
    return render(request, 'accounts/verify_otp.html', {
        'form': form,
        'email': user.email,
        'purpose': purpose
    })

def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            email = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(request, email=email, password=password)
            
            if user is not None:
                if user.is_verified:
                    login(request, user)
                    messages.success(request, f'Welcome back, {user.email}!')
                    return redirect('dashboard')
                else:
                    otp_code = OTP.generate_otp(user)
                    
                    try:
                        send_mail(
                            'Your OTP for Login Verification',
                            f'Your OTP is: {otp_code}. It will expire in 5 minutes.',
                            settings.DEFAULT_FROM_EMAIL,
                            [user.email],
                            fail_silently=False,
                        )
                        messages.success(request, 'OTP sent to your email!')
                    except Exception as e:
                        messages.error(request, f'Failed to send OTP: {str(e)}')
                        return redirect('login')
                    
                    request.session['otp_user_id'] = user.id
                    request.session['otp_purpose'] = 'login'
                    request.session['otp_sent_time'] = str(timezone.now())
                    return redirect('verify_otp')
            else:
                messages.error(request, 'Invalid email or password.')
    else:
        form = LoginForm()
    
    return render(request, 'accounts/login.html', {'form': form})

@login_required
def logout_view(request):
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('login')

def resend_otp_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    user_id = request.session.get('otp_user_id')
    purpose = request.session.get('otp_purpose')
    otp_sent_time = request.session.get('otp_sent_time')
    
    if not user_id or not purpose or not otp_sent_time:
        messages.error(request, 'Invalid OTP resend request.')
        return redirect('register' if purpose == 'registration' else 'login')
    
    try:
        user = CustomUser.objects.get(id=user_id)
    except ObjectDoesNotExist:
        messages.error(request, 'User not found.')
        return redirect('register' if purpose == 'registration' else 'login')
    
    # Prevent OTP spamming
    last_sent_time = timezone.datetime.fromisoformat(otp_sent_time)
    if timezone.now() - last_sent_time < timedelta(seconds=30):
        messages.warning(request, 'Please wait before requesting a new OTP.')
        return redirect('verify_otp')
    
    otp_code = OTP.generate_otp(user)
    
    try:
        subject = 'Your New OTP for Account Verification' if purpose == 'registration' else 'Your New OTP for Login Verification'
        send_mail(
            subject,
            f'Your new OTP is: {otp_code}. It will expire in 15 minutes.',
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=False,
        )
        messages.success(request, 'New OTP sent to your email!')
        request.session['otp_sent_time'] = str(timezone.now())
    except Exception as e:
        messages.error(request, f'Failed to resend OTP: {str(e)}')
    
    return redirect('verify_otp')