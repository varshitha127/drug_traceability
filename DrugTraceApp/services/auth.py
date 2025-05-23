import logging
from typing import Optional, Tuple
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone
from .blockchain import BlockchainService
from ..models import User

logger = logging.getLogger(__name__)

class AuthService:
    """Service class for handling authentication operations"""
    
    def __init__(self):
        self.blockchain_service = BlockchainService()
    
    def register_user(
        self,
        username: str,
        email: str,
        password: str,
        phone: str,
        address: str,
        role: str,
        blockchain_address: Optional[str] = None
    ) -> Tuple[bool, str, Optional[User]]:
        """Register a new user"""
        try:
            # Validate password
            try:
                validate_password(password)
            except ValidationError as e:
                return False, f"Invalid password: {', '.join(e.messages)}", None
            
            # Check if username or email already exists
            if User.objects.filter(username=username).exists():
                return False, "Username already exists", None
            if User.objects.filter(email=email).exists():
                return False, "Email already exists", None
            
            with transaction.atomic():
                # Create user
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    password=password,
                    phone=phone,
                    address=address,
                    role=role,
                    blockchain_address=blockchain_address
                )
                
                # Add user to blockchain if blockchain address is provided
                if blockchain_address:
                    try:
                        user_data = {
                            'username': username,
                            'email': email,
                            'role': role,
                            'blockchain_address': blockchain_address,
                            'registered_at': timezone.now().isoformat()
                        }
                        tx_hash = self.blockchain_service.add_drug_trace(user_data)
                        user.blockchain_hash = tx_hash
                        user.save()
                    except Exception as e:
                        logger.error(f"Failed to add user to blockchain: {str(e)}")
                        # Don't raise the exception, just log it
                
                return True, "User registered successfully", user
                
        except Exception as e:
            logger.error(f"Failed to register user: {str(e)}")
            return False, f"Registration failed: {str(e)}", None
    
    def login_user(
        self,
        request,
        username: str,
        password: str
    ) -> Tuple[bool, str, Optional[User]]:
        """Authenticate and login a user"""
        try:
            # Authenticate user
            user = authenticate(request, username=username, password=password)
            if not user:
                return False, "Invalid username or password", None
            
            if not user.is_active:
                return False, "Account is disabled", None
            
            # Login user
            login(request, user)
            
            # Update last login
            user.last_login = timezone.now()
            user.save(update_fields=['last_login'])
            
            return True, "Login successful", user
            
        except Exception as e:
            logger.error(f"Failed to login user: {str(e)}")
            return False, f"Login failed: {str(e)}", None
    
    def logout_user(self, request) -> None:
        """Logout a user"""
        try:
            logout(request)
        except Exception as e:
            logger.error(f"Failed to logout user: {str(e)}")
            raise
    
    def change_password(
        self,
        user: User,
        current_password: str,
        new_password: str
    ) -> Tuple[bool, str]:
        """Change user password"""
        try:
            # Verify current password
            if not user.check_password(current_password):
                return False, "Current password is incorrect"
            
            # Validate new password
            try:
                validate_password(new_password, user)
            except ValidationError as e:
                return False, f"Invalid new password: {', '.join(e.messages)}"
            
            # Change password
            user.set_password(new_password)
            user.save(update_fields=['password'])
            
            return True, "Password changed successfully"
            
        except Exception as e:
            logger.error(f"Failed to change password: {str(e)}")
            return False, f"Password change failed: {str(e)}"
    
    def update_user_profile(
        self,
        user: User,
        phone: Optional[str] = None,
        address: Optional[str] = None,
        blockchain_address: Optional[str] = None
    ) -> Tuple[bool, str]:
        """Update user profile"""
        try:
            update_fields = []
            
            if phone is not None:
                user.phone = phone
                update_fields.append('phone')
            
            if address is not None:
                user.address = address
                update_fields.append('address')
            
            if blockchain_address is not None:
                user.blockchain_address = blockchain_address
                update_fields.append('blockchain_address')
            
            if update_fields:
                user.save(update_fields=update_fields)
                
                # Update blockchain if blockchain address changed
                if 'blockchain_address' in update_fields:
                    try:
                        user_data = {
                            'username': user.username,
                            'email': user.email,
                            'role': user.role,
                            'blockchain_address': blockchain_address,
                            'updated_at': timezone.now().isoformat()
                        }
                        tx_hash = self.blockchain_service.add_drug_trace(user_data)
                        user.blockchain_hash = tx_hash
                        user.save(update_fields=['blockchain_hash'])
                    except Exception as e:
                        logger.error(f"Failed to update user on blockchain: {str(e)}")
                        # Don't raise the exception, just log it
            
            return True, "Profile updated successfully"
            
        except Exception as e:
            logger.error(f"Failed to update profile: {str(e)}")
            return False, f"Profile update failed: {str(e)}" 