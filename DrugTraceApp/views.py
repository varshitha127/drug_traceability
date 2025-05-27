from django.shortcuts import render, redirect
from django.template import RequestContext
from django.contrib import messages
import pymysql
from django.http import HttpResponse, JsonResponse
from django.core.files.storage import FileSystemStorage
import os
from datetime import date
import json
from web3 import Web3, HTTPProvider
import pickle
import logging
from typing import Dict, Any
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_protect
from django.core.paginator import Paginator
from django.db.models import Q
from .models import User, Drug, DrugTrace
from .services.auth import AuthService
from .services.blockchain import BlockchainService
from .forms import DrugForm, DrugTraceForm

logger = logging.getLogger(__name__)

# Remove global service initialization
# Instead, create service instances when needed
def get_auth_service():
    return AuthService()

def get_blockchain_service():
    return BlockchainService()

# Remove global variables
# details = ''
# username = ''
# contract = None
# product_name = None

def readDetails(contract_type):
    try:
        blockchain_service = get_blockchain_service()
        if contract_type == 'signup':
            return blockchain_service.get_user_data()
        if contract_type == 'addproduct':
            return blockchain_service.get_tracing_data()
    except Exception as e:
        logger.error(f"Error reading blockchain details: {str(e)}")
        return None

def saveDataBlockChain(currentData, contract_type):
    try:
        blockchain_service = get_blockchain_service()
        if contract_type == 'signup':
            return blockchain_service.add_user_data(currentData)
        if contract_type == 'addproduct':
            return blockchain_service.add_tracing_data(currentData)
    except Exception as e:
        logger.error(f"Error saving to blockchain: {str(e)}")
        raise

def updateQuantityBlock(currentData):
    try:
        blockchain_service = get_blockchain_service()
        return blockchain_service.update_tracing_data(currentData)
    except Exception as e:
        logger.error(f"Error updating quantity: {str(e)}")
        raise

def index(request):
    """Home page view"""
    return render(request, 'index.html')

@require_http_methods(['GET', 'POST'])
@csrf_protect
def login_view(request):
    """Login view"""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        success, message, user = get_auth_service().login_user(request, username, password)
        
        if success:
            messages.success(request, message)
            if user.role == 'admin':
                return redirect('admin_dashboard')
            return redirect('user_dashboard')
        else:
            messages.error(request, message)
    
    return render(request, 'Login.html')

@require_http_methods(['GET', 'POST'])
@csrf_protect
def register_view(request):
    """Registration view"""
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        phone = request.POST.get('phone')
        address = request.POST.get('address')
        role = request.POST.get('role', 'consumer')
        blockchain_address = request.POST.get('blockchain_address')
        
        success, message, user = get_auth_service().register_user(
            username=username,
            email=email,
            password=password,
            phone=phone,
            address=address,
            role=role,
            blockchain_address=blockchain_address
        )
        
        if success:
            messages.success(request, message)
            return redirect('login')
        else:
            messages.error(request, message)
    
    return render(request, 'Register.html')

@login_required
def logout_view(request):
    """Logout view"""
    get_auth_service().logout_user(request)
    messages.success(request, "Logged out successfully")
    return redirect('index')

@login_required
def user_dashboard(request):
    """User dashboard view"""
    user = request.user
    drugs = Drug.objects.filter(manufacturer=user).order_by('-created_at')
    
    # Paginate drugs
    paginator = Paginator(drugs, 10)
    page = request.GET.get('page')
    drugs = paginator.get_page(page)
    
    context = {
        'user': user,
        'drugs': drugs,
        'total_drugs': drugs.paginator.count if drugs else 0
    }
    return render(request, 'UserScreen.html', context)

@login_required
def admin_dashboard(request):
    """Admin dashboard view"""
    if not request.user.is_staff:
        raise PermissionDenied
    
    users = User.objects.exclude(id=request.user.id).order_by('-date_joined')
    drugs = Drug.objects.all().order_by('-created_at')
    
    # Paginate users and drugs
    user_paginator = Paginator(users, 10)
    drug_paginator = Paginator(drugs, 10)
    
    user_page = request.GET.get('user_page')
    drug_page = request.GET.get('drug_page')
    
    users = user_paginator.get_page(user_page)
    drugs = drug_paginator.get_page(drug_page)
    
    context = {
        'users': users,
        'drugs': drugs,
        'total_users': users.paginator.count if users else 0,
        'total_drugs': drugs.paginator.count if drugs else 0
    }
    return render(request, 'AdminScreen.html', context)

@login_required
@require_http_methods(['GET', 'POST'])
@csrf_protect
def add_product(request):
    """Add product view"""
    if request.method == 'POST':
        form = DrugForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                drug = form.save(commit=False)
                drug.manufacturer = request.user
                
                # Add to blockchain
                drug_data = {
                    'name': drug.name,
                    'manufacturer': drug.manufacturer.username,
                    'batch_number': drug.batch_number,
                    'manufacturing_date': drug.manufacturing_date.isoformat(),
                    'expiry_date': drug.expiry_date.isoformat(),
                    'quantity': drug.quantity,
                    'description': drug.description,
                    'status': drug.status
                }
                
                tx_hash = get_blockchain_service().add_drug_trace(drug_data)
                drug.blockchain_hash = tx_hash
                drug.save()
                
                # Create initial trace
                DrugTrace.objects.create(
                    drug=drug,
                    actor=request.user,
                    action='manufactured',
                    location=request.user.address,
                    quantity=drug.quantity,
                    blockchain_hash=tx_hash
                )
                
                messages.success(request, "Product added successfully")
                return redirect('user_dashboard')
                
            except Exception as e:
                logger.error(f"Failed to add product: {str(e)}")
                messages.error(request, f"Failed to add product: {str(e)}")
        else:
            messages.error(request, "Please correct the errors below")
    else:
        form = DrugForm()
    
    return render(request, 'AddProduct.html', {'form': form})

@login_required
@require_http_methods(['GET', 'POST'])
@csrf_protect
def update_tracing(request, drug_id):
    """Update tracing view"""
    try:
        drug = Drug.objects.get(id=drug_id)
        
        # Check permissions
        if not (request.user.is_staff or drug.manufacturer == request.user):
            raise PermissionDenied
        
        if request.method == 'POST':
            form = DrugTraceForm(request.POST)
            if form.is_valid():
                try:
                    trace = form.save(commit=False)
                    trace.drug = drug
                    trace.actor = request.user
                    
                    # Update drug status
                    drug.status = trace.action
                    drug.save(update_fields=['status'])
                    
                    # Add to blockchain
                    trace_data = {
                        'drug_id': str(drug.id),
                        'action': trace.action,
                        'actor': trace.actor.username,
                        'location': trace.location,
                        'quantity': trace.quantity,
                        'notes': trace.notes
                    }
                    
                    tx_hash = get_blockchain_service().add_drug_trace(trace_data)
                    trace.blockchain_hash = tx_hash
                    trace.save()
                    
                    messages.success(request, "Tracing information updated successfully")
                    return redirect('view_tracing', drug_id=drug.id)
                    
                except Exception as e:
                    logger.error(f"Failed to update tracing: {str(e)}")
                    messages.error(request, f"Failed to update tracing: {str(e)}")
            else:
                messages.error(request, "Please correct the errors below")
        else:
            form = DrugTraceForm()
        
        context = {
            'form': form,
            'drug': drug,
            'traces': drug.traces.all().order_by('-created_at')
        }
        return render(request, 'UpdateTracing.html', context)
        
    except Drug.DoesNotExist:
        messages.error(request, "Product not found")
        return redirect('user_dashboard')

@login_required
def view_tracing(request, drug_id):
    """View tracing information"""
    try:
        drug = Drug.objects.get(id=drug_id)
        traces = drug.traces.all().order_by('-created_at')
        
        # Verify blockchain data
        is_verified = get_blockchain_service().verify_drug_trace(
            drug.blockchain_hash,
            {
                'name': drug.name,
                'manufacturer': drug.manufacturer.username,
                'batch_number': drug.batch_number,
                'manufacturing_date': drug.manufacturing_date.isoformat(),
                'expiry_date': drug.expiry_date.isoformat(),
                'quantity': drug.quantity,
                'description': drug.description,
                'status': drug.status
            }
        )
        
        context = {
            'drug': drug,
            'traces': traces,
            'is_verified': is_verified
        }
        return render(request, 'ViewTracingDetails.html', context)
        
    except Drug.DoesNotExist:
        messages.error(request, "Product not found")
        return redirect('user_dashboard')

@login_required
def search_drugs(request):
    """Search drugs"""
    query = request.GET.get('q', '')
    if query:
        drugs = Drug.objects.filter(
            Q(name__icontains=query) |
            Q(batch_number__icontains=query) |
            Q(manufacturer__username__icontains=query)
        ).order_by('-created_at')
    else:
        drugs = Drug.objects.none()
    
    # Paginate results
    paginator = Paginator(drugs, 10)
    page = request.GET.get('page')
    drugs = paginator.get_page(page)
    
    context = {
        'drugs': drugs,
        'query': query,
        'total_results': drugs.paginator.count if drugs else 0
    }
    return render(request, 'search_results.html', context)

@login_required
def api_drug_details(request, drug_id):
    """API endpoint for drug details"""
    try:
        drug = Drug.objects.get(id=drug_id)
        traces = drug.traces.all().order_by('-created_at')
        
        data = {
            'id': str(drug.id),
            'name': drug.name,
            'manufacturer': drug.manufacturer.username,
            'batch_number': drug.batch_number,
            'manufacturing_date': drug.manufacturing_date.isoformat(),
            'expiry_date': drug.expiry_date.isoformat(),
            'quantity': drug.quantity,
            'description': drug.description,
            'status': drug.status,
            'blockchain_hash': drug.blockchain_hash,
            'created_at': drug.created_at.isoformat(),
            'updated_at': drug.updated_at.isoformat(),
            'traces': [
                {
                    'action': trace.action,
                    'actor': trace.actor.username,
                    'location': trace.location,
                    'quantity': trace.quantity,
                    'notes': trace.notes,
                    'blockchain_hash': trace.blockchain_hash,
                    'created_at': trace.created_at.isoformat()
                }
                for trace in traces
            ]
        }
        return JsonResponse(data)
        
    except Drug.DoesNotExist:
        return JsonResponse({'error': 'Product not found'}, status=404)
    except Exception as e:
        logger.error(f"API error: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)

def Login(request):
    if request.method == 'GET':
       return render(request, 'Login.html', {})
    
def Register(request):
    if request.method == 'GET':
       return render(request, 'Register.html', {})

def AddProduct(request):
    if request.method == 'GET':
        return render(request, 'AddProduct.html', {})
    elif request.method == 'POST':
        drug_name = request.POST.get('drug_name', False)
        manufacturer = request.POST.get('manufacturer', False)
        batch_number = request.POST.get('batch_number', False)
        manufacturing_date = request.POST.get('manufacturing_date', False)
        expiry_date = request.POST.get('expiry_date', False)
        quantity = request.POST.get('quantity', False)
        description = request.POST.get('description', False)
        image = request.FILES['product_image']
        imagename = request.FILES['product_image'].name

        today = date.today()
        fs = FileSystemStorage()
        filename = fs.save('DrugTraceApp/static/products/'+imagename, image)
        
        # Format: addproduct#drug_name#manufacturer#batch_number#manufacturing_date#expiry_date#quantity#description#imagename#today#status
        data = f"addproduct#{drug_name}#{manufacturer}#{batch_number}#{manufacturing_date}#{expiry_date}#{quantity}#{description}#{imagename}#{str(today)}#Production State\n"
        saveDataBlockChain(data,"addproduct")
        messages.success(request, "Product details saved in Blockchain successfully!")
        return render(request, 'AddProduct.html', {})

def UpdateTracingAction(request):
    if request.method == 'GET':
        product_name = request.GET['pname']
        output = '<tr><td><font size="" color="black">Product&nbsp;Name</font></td>'
        output += '<td><input type="text" name="t1" style="font-family: Comic Sans MS" size="30" value='+product_name+' readonly/></td></tr>'
        context= {'data':output}
        return render(request, 'AddTracing.html', context)    

def UpdateTracing(request):
    if request.method == 'GET':
        output = '<table border=1 align=center>'
        output+='<tr><th><font size=3 color=black>Drug Name</font></th>'
        output+='<th><font size=3 color=black>Price</font></th>'
        output+='<th><font size=3 color=black>Quantity</font></th>'
        output+='<th><font size=3 color=black>Description</font></th>'
        output+='<th><font size=3 color=black>Image</font></th>'
        output+='<th><font size=3 color=black>Last Update Date</font></th>'
        output+='<th><font size=3 color=black>Current Tracing Info</font></th>'
        output+='<th><font size=3 color=black>Update New Tracing Info</font></th></tr>'
        details = readDetails("addproduct")
        rows = details.split("\n")
        for i in range(len(rows)-1):
            arr = rows[i].split("#")
            if arr[0] == 'addproduct':
                output+='<tr><td><font size=3 color=black>'+arr[1]+'</font></td>'
                output+='<td><font size=3 color=black>'+arr[2]+'</font></td>'
                output+='<td><font size=3 color=black>'+str(arr[3])+'</font></td>'
                output+='<td><font size=3 color=black>'+str(arr[4])+'</font></td>'
                output+='<td><img src="/static/products/'+arr[5]+'" width="200" height="200"></img></td>'
                output+='<td><font size=3 color=black>'+str(arr[6])+'</font></td>'
                output+='<td><font size=3 color=black>'+str(arr[7])+'</font></td>'
                output+='<td><a href=\'UpdateTracingAction?pname='+arr[1]+'\'><font size=3 color=black>Click Here</font></a></td></tr>'                    
        output+="</table><br/><br/><br/><br/><br/><br/>"
        context= {'data':output}
        return render(request, 'UpdateTracing.html', context)              
        
    
def AddTracingAction(request):
    if request.method == 'POST':
        product_name = request.POST.get('t1', False)
        tracing_type = request.POST.get('t2', False)
        tracing_status = request.POST.get('t3', False)
        index = 0
        record = ''
        details = readDetails("addproduct")
        rows = details.split("\n")
        tot_qty = 0
        for i in range(len(rows)-1):
            arr = rows[i].split("#")
            if arr[0] == "addproduct":
                if arr[1] == product_name:
                    today = date.today()
                    index = i
                    record = arr[0]+"#"+arr[1]+"#"+arr[2]+"#"+arr[3]+"#"+arr[4]+"#"+arr[5]+"#"+str(today)+"#"+tracing_type+"! "+tracing_status+"\n"
                    break
        for i in range(len(rows)-1):
            if i != index:
                record += rows[i]+"\n"
        updateQuantityBlock(record)
        context= {'data':"Tracing details updated"}
        return render(request, 'AdminScreen.html', context)
          
def AddProductAction(request):
    if request.method == 'POST':
        try:
            drug_name = request.POST.get('t1', '')
            quantity = request.POST.get('t2', '')
            price = request.POST.get('t3', '')
            description = request.POST.get('t4', '')
            image = request.FILES.get('t5')
            
            if not all([drug_name, quantity, price, description, image]):
                messages.error(request, "All fields are required")
                return render(request, 'AddProduct.html', {})

            # Save image
            fs = FileSystemStorage()
            imagename = image.name
            filename = fs.save('DrugTraceApp/static/products/'+imagename, image)
            
            # Prepare data for blockchain
            drug_data = {
                'name': drug_name,
                'price': price,
                'quantity': quantity,
                'description': description,
                'image': imagename,
                'date': str(date.today()),
                'status': 'Production State'
            }
            
            # Save to blockchain
            tx_hash = get_blockchain_service().add_drug_trace(drug_data)
            
            messages.success(request, "Product details saved in Blockchain successfully!")
            return render(request, 'AddProduct.html', {})
            
        except Exception as e:
            logger.error(f"Error adding product: {str(e)}")
            messages.error(request, f"Failed to add product: {str(e)}")
            return render(request, 'AddProduct.html', {})

def Signup(request):
    if request.method == 'POST':
        try:
            username = request.POST.get('username', '')
            password = request.POST.get('password', '')
            contact = request.POST.get('contact', '')
            email = request.POST.get('email', '')
            address = request.POST.get('address', '')
            
            if not all([username, password, contact, email, address]):
                messages.error(request, "All fields are required")
                return render(request, 'Register.html', {})
            
            # Check if username exists
            user_data = get_blockchain_service().get_user_data()
            if user_data and username in user_data:
                messages.error(request, f"Username '{username}' already exists")
                return render(request, 'Register.html', {})
            
            # Prepare user data
            user_data = {
                'username': username,
                'password': password,
                'contact': contact,
                'email': email,
                'address': address
            }
            
            # Save to blockchain
            tx_hash = get_blockchain_service().add_user_data(json.dumps(user_data))
            
            messages.success(request, "Signup process completed and record saved in Blockchain")
            return render(request, 'Register.html', {})
            
        except Exception as e:
            logger.error(f"Error during signup: {str(e)}")
            messages.error(request, f"Signup failed: {str(e)}")
            return render(request, 'Register.html', {})

def UserLogin(request):
    if request.method == 'POST':
        try:
            username = request.POST.get('username', '')
            password = request.POST.get('password', '')
            
            if not username or not password:
                messages.error(request, "Username and password are required")
                return render(request, 'Login.html', {})
            
            # Admin login
            if username == 'admin' and password == 'admin':
                messages.success(request, f"Welcome {username}")
                return render(request, 'AdminScreen.html', {})
            
            # Regular user login
            user_data = get_blockchain_service().get_user_data()
            if user_data:
                users = user_data.split('\n')
                for user in users:
                    if user.startswith('signup#'):
                        fields = user.split('#')
                        if len(fields) >= 3 and fields[1] == username and fields[2] == password:
                            messages.success(request, f"Welcome {username}")
                            # Store session
                            with open('session.txt', 'w') as file:
                                file.write(username)
                            return render(request, 'UserScreen.html', {})
            
            messages.error(request, "Invalid login details")
            return render(request, 'Login.html', {})
            
        except Exception as e:
            logger.error(f"Login error: {str(e)}")
            messages.error(request, "Login failed. Please try again.")
            return render(request, 'Login.html', {})

def ViewTracing(request):
    if request.method == 'GET':
        try:
            tracing_data = get_blockchain_service().get_tracing_data()
            if not tracing_data:
                messages.warning(request, "No tracing data available")
                return render(request, 'ViewTracing.html', {'data': ''})
            
            output = '<table class="table table-hover align-middle">'
            output += '<thead><tr>'
            output += '<th>Drug Name</th>'
            output += '<th>Manufacturer</th>'
            output += '<th>Batch Number</th>'
            output += '<th>Manufacturing Date</th>'
            output += '<th>Expiry Date</th>'
            output += '<th>Quantity</th>'
            output += '<th>Description</th>'
            output += '<th>Image</th>'
            output += '<th>Last Updated</th>'
            output += '<th>Status</th>'
            output += '</tr></thead><tbody>'
            
            rows = tracing_data.split("\n")
            for row in rows:
                if row.startswith('addproduct#'):
                    fields = row.split('#')
                    if len(fields) >= 11:
                        output += '<tr>'
                        output += f'<td>{fields[1]}</td>'  # Drug Name
                        output += f'<td>{fields[2]}</td>'  # Manufacturer
                        output += f'<td>{fields[3]}</td>'  # Batch Number
                        output += f'<td>{fields[4]}</td>'  # Manufacturing Date
                        output += f'<td>{fields[5]}</td>'  # Expiry Date
                        output += f'<td>{fields[6]}</td>'  # Quantity
                        output += f'<td>{fields[7]}</td>'  # Description
                        output += f'<td><img src="/static/products/{fields[8]}" width="100" height="100" class="img-thumbnail"></td>'  # Image
                        output += f'<td>{fields[9]}</td>'  # Last Updated
                        output += f'<td><span class="badge bg-success">{fields[10]}</span></td>'  # Status
                        output += '</tr>'
            
            output += '</tbody></table>'
            return render(request, 'ViewTracing.html', {'data': output})
            
        except Exception as e:
            logger.error(f"Error viewing tracing: {str(e)}")
            messages.error(request, "Failed to load tracing data")
            return render(request, 'ViewTracing.html', {'data': ''})

def ViewUsers(request):
    if request.method == 'GET':
        try:
            user_data = get_blockchain_service().get_user_data()
            if not user_data:
                messages.warning(request, "No user data available")
                return render(request, 'ViewUsers.html', {'data': ''})
            
            output = '<table class="table table-hover align-middle">'
            output += '<thead><tr>'
            output += '<th>Username</th>'
            output += '<th>Email</th>'
            output += '<th>Contact</th>'
            output += '<th>Address</th>'
            output += '<th>Status</th>'
            output += '</tr></thead><tbody>'
            
            rows = user_data.split("\n")
            for row in rows:
                if row.startswith('signup#'):
                    fields = row.split('#')
                    if len(fields) >= 6:
                        output += '<tr>'
                        output += f'<td>{fields[1]}</td>'  # Username
                        output += f'<td>{fields[4]}</td>'  # Email
                        output += f'<td>{fields[3]}</td>'  # Contact
                        output += f'<td>{fields[5]}</td>'  # Address
                        output += '<td><span class="badge bg-success">Active</span></td>'
                        output += '</tr>'
            
            output += '</tbody></table>'
            return render(request, 'ViewUsers.html', {'data': output})
            
        except Exception as e:
            logger.error(f"Error viewing users: {str(e)}")
            messages.error(request, "Failed to load user data")
            return render(request, 'ViewUsers.html', {'data': ''})

@login_required
def drug_list(request):
    drugs = Drug.objects.all().order_by('-created_at')
    return render(request, 'ViewTracing.html', {'drugs': drugs})
            
