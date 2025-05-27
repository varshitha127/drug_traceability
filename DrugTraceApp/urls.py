from django.urls import path
from . import views

app_name = 'drugtrace'

urlpatterns = [
    # Public views
    path('', views.index, name='index'),
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    
    # Protected views
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.user_dashboard, name='user_dashboard'),
    path('admin/dashboard/', views.admin_dashboard, name='admin_dashboard'),
    
    # Drug management
    path('drugs/add/', views.add_product, name='add_product'),
    path('drugs/<uuid:drug_id>/update/', views.update_tracing, name='update_tracing'),
    path('drugs/<uuid:drug_id>/', views.view_tracing, name='view_tracing'),
    path('drugs/search/', views.search_drugs, name='search_drugs'),
    path('drugs/', views.drug_list, name='drug_list'),
    
    # API endpoints
    path('api/drugs/<uuid:drug_id>/', views.api_drug_details, name='api_drug_details'),
    
    # Legacy URLs (to be removed after migration)
    path('index.html', views.index, name='index_legacy'),
    path('Login.html', views.login_view, name='login_legacy'),
    path('Register.html', views.register_view, name='register_legacy'),
    path('Signup', views.register_view, name='signup_legacy'),
    path('UserLogin', views.login_view, name='user_login_legacy'),
    path('AddProduct.html', views.add_product, name='add_product_legacy'),
    path('AddProductAction', views.add_product, name='add_product_action_legacy'),
    path('UpdateTracing.html', views.update_tracing, name='update_tracing_legacy'),
    path('UpdateTracingAction', views.update_tracing, name='update_tracing_action_legacy'),
    path('ViewTracing.html', views.view_tracing, name='view_tracing_legacy'),
    path('AddTracingAction', views.update_tracing, name='add_tracing_action_legacy'),
    path('ViewUsers.html', views.admin_dashboard, name='view_users_legacy'),
]