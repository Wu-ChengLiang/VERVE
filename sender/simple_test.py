#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简单的AI邮件发送测试
专门给 19357509506@163.com 发送一封AI生成的邮件
"""

import sys
import asyncio
import smtplib
import toml
from pathlib import Path
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr
from typing import Dict, Any

# 添加项目根目录到路径，以便导入 aiclient
current_dir = Path(__file__).parent
project_root = current_dir.parent
sys.path.insert(0, str(project_root))

# 导入 aiclient
from aiclient import AIClient


async def send_ai_email_to_target():
    """发送AI生成的邮件给目标邮箱"""
    
    print("🚀 开始AI邮件发送测试...")
    
    # 目标邮箱
    target_email = "19357509506@163.com"
    
    try:
        # 1. 加载邮件配置
        config_path = Path(__file__).parent / "config.toml"
        if not config_path.exists():
            raise FileNotFoundError(f"配置文件不存在: {config_path}")
        
        with open(config_path, 'r', encoding='utf-8') as f:
            config = toml.load(f)
        
        email_config = config['email']
        print(f"📧 发件邮箱: {email_config['sender_email']}")
        print(f"📬 目标邮箱: {target_email}")
        
        # 2. 初始化AI客户端
        print("🤖 初始化AI客户端...")
        ai_client = AIClient()
        
        # 3. 使用AI生成邮件内容
        print("✨ 正在使用AI生成邮件内容...")
        prompt = """
请生成一封专业的测试邮件：

主题：AI系统测试邮件
收件人：测试用户

要求：
1. 生成一个简洁明了的邮件主题
2. 生成礼貌、专业的邮件正文
3. 邮件正文应该包含问候语、说明这是一封测试邮件、结尾语
4. 语言风格要友好且正式

请按以下格式回复：
主题：[邮件主题]
正文：[邮件正文]
"""
        
        response = await ai_client.generate_customer_service_reply(prompt)
        ai_content = response.content
        print(f"🤖 AI生成的内容:\n{ai_content}\n")
        
        # 4. 解析AI回复
        subject = "AI系统测试邮件"  # 默认主题
        body = ai_content  # 默认使用整个AI回复作为正文
        
        # 尝试解析AI回复中的主题和正文
        lines = ai_content.strip().split('\n')
        current_section = None
        
        for line in lines:
            line = line.strip()
            if line.startswith('主题：'):
                subject = line[3:].strip()
                current_section = 'subject'
            elif line.startswith('正文：'):
                body = line[3:].strip()
                current_section = 'body'
            elif current_section == 'body' and line:
                body += '\n' + line
        
        print(f"📧 邮件主题: {subject}")
        print(f"📝 邮件正文预览: {body[:100]}...")
        
        # 5. 发送邮件
        print("📤 正在发送邮件...")
        
        sender_email = email_config['sender_email']
        smtp_password = email_config['smtp_password']
        smtp_server = email_config['smtp_server']
        server_port = email_config['server_port']
        
        # 创建邮件消息
        message = MIMEMultipart()
        message["From"] = formataddr(("AI测试系统", sender_email))
        message["To"] = formataddr(("测试用户", target_email))
        message["Subject"] = subject
        message.attach(MIMEText(body, "plain", "utf-8"))
        
        # 根据端口选择连接方式
        if server_port == 465:
            server = smtplib.SMTP_SSL(smtp_server, 465, timeout=15)
        elif server_port == 587:
            server = smtplib.SMTP(smtp_server, 587, timeout=15)
            server.ehlo()
            server.starttls()
            server.ehlo()
        elif server_port == 25:
            server = smtplib.SMTP(smtp_server, 25, timeout=15)
        else:
            raise ValueError(f"不支持的端口号: {server_port}")
        
        try:
            server.login(sender_email, smtp_password)
            server.sendmail(sender_email, target_email, message.as_string())
            print(f"✅ 邮件已成功发送至 {target_email}")
        except smtplib.SMTPAuthenticationError:
            raise ValueError("邮箱认证失败！请检查密码是否正确，并确认已开启SMTP服务。")
        finally:
            if 'server' in locals():
                server.quit()
        
        print("🎉 测试完成！")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


if __name__ == "__main__":
    print("=" * 60)
    print("🧪 AI邮件发送简单测试")
    print("目标邮箱: 19357509506@163.com")
    print("=" * 60)
    
    # 运行测试
    success = asyncio.run(send_ai_email_to_target())
    
    if success:
        print("\n🎉 测试成功完成！")
        sys.exit(0)
    else:
        print("\n❌ 测试失败！")
        sys.exit(1) 