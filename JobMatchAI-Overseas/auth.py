"""
JobMatchAI - 认证模块
JWT 登录/注册系统

功能：
- 用户注册 (bcrypt 密码加密)
- 用户登录 (JWT Token)
- 获取当前用户信息
- Token 刷新

Copyright © 2026 JobMatchAI. All rights reserved.
"""

import os
import sys
import hashlib
import uuid
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

# 导入数据库模块
sys.path.insert(0, os.path.dirname(__file__))
from database import (
    create_user, get_user_by_email, get_user_by_id, 
    verify_user_password, update_user, generate_id
)

# JWT 配置
import jwt

JWT_SECRET = os.getenv("JWT_SECRET", "jobmatchai_secret_key_change_in_production_2026")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24 * 7  # 7 天过期


def hash_password(password: str) -> str:
    """使用 SHA256 + salt 对密码进行哈希"""
    salt = os.getenv("PASSWORD_SALT", "jobmatchai_salt_2026")
    return hashlib.sha256(f"{salt}{password}".encode()).hexdigest()


def verify_password(password: str, password_hash: str) -> bool:
    """验证密码"""
    return hash_password(password) == password_hash


def create_access_token(user_id: str, email: str) -> str:
    """创建访问令牌"""
    now = datetime.utcnow()
    payload = {
        "user_id": user_id,
        "email": email,
        "iat": now,
        "exp": now + timedelta(hours=JWT_EXPIRATION_HOURS),
        "jti": str(uuid.uuid4())
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_token(token: str) -> Optional[Dict[str, Any]]:
    """解码并验证 Token"""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def get_user_from_token(token: str) -> Optional[Dict[str, Any]]:
    """从 Token 获取用户信息"""
    payload = decode_token(token)
    if not payload:
        return None
    
    user_id = payload.get("user_id")
    if not user_id:
        return None
    
    return get_user_by_id(user_id)


def register_user(
    email: str,
    password: str,
    name: str = "",
    phone: str = "",
    country: str = "",
    city: str = ""
) -> Dict[str, Any]:
    """注册新用户"""
    # 检查邮箱是否已存在
    existing_user = get_user_by_email(email)
    if existing_user:
        return {
            "success": False,
            "error": "Email already registered"
        }
    
    # 检查密码强度
    if len(password) < 6:
        return {
            "success": False,
            "error": "Password must be at least 6 characters"
        }
    
    # 生成用户ID
    user_id = generate_id("usr")
    
    # 加密密码
    password_hash = hash_password(password)
    
    # 创建用户
    user = create_user(
        user_id=user_id,
        email=email,
        password_hash=password_hash,
        name=name,
        phone=phone,
        country=country,
        city=city
    )
    
    if user:
        # 生成 Token
        token = create_access_token(user_id, email)
        return {
            "success": True,
            "user": {
                "user_id": user["user_id"],
                "email": user["email"],
                "name": user.get("name", ""),
                "country": user.get("country", ""),
                "city": user.get("city", ""),
                "preferred_language": user.get("preferred_language", "en"),
                "created_at": user["created_at"]
            },
            "access_token": token,
            "token_type": "bearer"
        }
    
    return {
        "success": False,
        "error": "Failed to create user"
    }


def login_user(email: str, password: str) -> Dict[str, Any]:
    """用户登录"""
    # 获取用户
    user = get_user_by_email(email)
    if not user:
        return {
            "success": False,
            "error": "Invalid email or password"
        }
    
    # 验证密码
    if not verify_password(password, user["password_hash"]):
        return {
            "success": False,
            "error": "Invalid email or password"
        }
    
    # 生成 Token
    token = create_access_token(user["user_id"], email)
    
    return {
        "success": True,
        "user": {
            "user_id": user["user_id"],
            "email": user["email"],
            "name": user.get("name", ""),
            "phone": user.get("phone", ""),
            "country": user.get("country", ""),
            "city": user.get("city", ""),
            "preferred_language": user.get("preferred_language", "en"),
            "subscription_plan": user.get("subscription_plan", "free"),
            "subscription_expires_at": user.get("subscription_expires_at", ""),
            "created_at": user["created_at"]
        },
        "access_token": token,
        "token_type": "bearer"
    }


def get_current_user(token: str) -> Dict[str, Any]:
    """获取当前用户信息"""
    user = get_user_from_token(token)
    if not user:
        return {
            "success": False,
            "error": "Invalid or expired token"
        }
    
    return {
        "success": True,
        "user": {
            "user_id": user["user_id"],
            "email": user["email"],
            "name": user.get("name", ""),
            "phone": user.get("phone", ""),
            "country": user.get("country", ""),
            "city": user.get("city", ""),
            "preferred_language": user.get("preferred_language", "en"),
            "subscription_plan": user.get("subscription_plan", "free"),
            "subscription_expires_at": user.get("subscription_expires_at", ""),
            "created_at": user["created_at"],
            "updated_at": user["updated_at"]
        }
    }


def update_user_profile(user_id: str, **kwargs) -> Dict[str, Any]:
    """更新用户资料"""
    # 不允许通过此接口更新密码和邮箱
    kwargs.pop("email", None)
    kwargs.pop("password", None)
    kwargs.pop("password_hash", None)
    
    user = update_user(user_id, **kwargs)
    if not user:
        return {
            "success": False,
            "error": "User not found"
        }
    
    return {
        "success": True,
        "user": {
            "user_id": user["user_id"],
            "email": user["email"],
            "name": user.get("name", ""),
            "phone": user.get("phone", ""),
            "country": user.get("country", ""),
            "city": user.get("city", ""),
            "preferred_language": user.get("preferred_language", "en"),
            "subscription_plan": user.get("subscription_plan", "free"),
            "subscription_expires_at": user.get("subscription_expires_at", ""),
            "updated_at": user["updated_at"]
        }
    }


def change_password(user_id: str, old_password: str, new_password: str) -> Dict[str, Any]:
    """修改密码"""
    user = get_user_by_id(user_id)
    if not user:
        return {
            "success": False,
            "error": "User not found"
        }
    
    # 验证旧密码
    if not verify_password(old_password, user["password_hash"]):
        return {
            "success": False,
            "error": "Current password is incorrect"
        }
    
    # 检查新密码强度
    if len(new_password) < 6:
        return {
            "success": False,
            "error": "New password must be at least 6 characters"
        }
    
    # 更新密码
    new_hash = hash_password(new_password)
    update_user(user_id, password_hash=new_hash)
    
    return {
        "success": True,
        "message": "Password changed successfully"
    }


def extract_token_from_header(authorization: str) -> Optional[str]:
    """从 Authorization header 中提取 Token"""
    if not authorization:
        return None
    
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        return None
    
    return parts[1]
