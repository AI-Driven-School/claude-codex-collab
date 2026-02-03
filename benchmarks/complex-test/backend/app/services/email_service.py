"""
メール送信サービス

smtplibを使用した基本的なメール送信機能と、
SendGrid/Mailgun対応のオプション実装を提供
"""
import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, List
from datetime import date
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class EmailProvider(str, Enum):
    """メール送信プロバイダー"""
    SMTP = "smtp"
    SENDGRID = "sendgrid"
    MAILGUN = "mailgun"
    RESEND = "resend"


@dataclass
class EmailConfig:
    """メール設定"""
    provider: EmailProvider = EmailProvider.SMTP
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""
    smtp_use_tls: bool = True
    from_email: str = ""
    from_name: str = "StressAgent Pro"
    api_key: str = ""
    mailgun_domain: str = ""

    @classmethod
    def from_env(cls) -> "EmailConfig":
        """環境変数から設定を読み込み"""
        provider = os.getenv("EMAIL_PROVIDER", "smtp").lower()
        return cls(
            provider=EmailProvider(provider),
            smtp_host=os.getenv("SMTP_HOST", "smtp.gmail.com"),
            smtp_port=int(os.getenv("SMTP_PORT", "587")),
            smtp_username=os.getenv("SMTP_USERNAME", ""),
            smtp_password=os.getenv("SMTP_PASSWORD", ""),
            smtp_use_tls=os.getenv("SMTP_USE_TLS", "true").lower() == "true",
            from_email=os.getenv("EMAIL_FROM", "noreply@stressagent.com"),
            from_name=os.getenv("EMAIL_FROM_NAME", "StressAgent Pro"),
            api_key=os.getenv("SENDGRID_API_KEY", "")
            or os.getenv("MAILGUN_API_KEY", "")
            or os.getenv("RESEND_API_KEY", ""),
            mailgun_domain=os.getenv("MAILGUN_DOMAIN", ""),
        )


class EmailTemplate:
    """メールテンプレート管理"""

    @staticmethod
    def reminder_email(
        employee_name: str,
        company_name: str,
        deadline: date,
        check_url: str
    ) -> tuple[str, str, str]:
        """リマインドメール（未受検者への通知）"""
        subject = f"【{company_name}】ストレスチェック受検のお願い"

        text_body = f"""
{employee_name} 様

お疲れ様です。
{company_name} の定期ストレスチェックの受検期間となっております。

まだ受検がお済みでない場合は、下記のリンクより受検をお願いいたします。

受検URL: {check_url}
受検期限: {deadline.strftime('%Y年%m月%d日')}

ストレスチェックは、労働安全衛生法に基づき実施しております。
皆様の心身の健康を守るための大切な取り組みですので、
ぜひご協力をお願いいたします。

※このメールは自動送信されています。
※ご不明な点がございましたら、人事部までお問い合わせください。

--
{company_name}
StressAgent Pro
"""

        html_body = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body {{ font-family: 'Hiragino Sans', 'Meiryo', sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background-color: #4F46E5; color: white; padding: 20px; text-align: center; border-radius: 8px 8px 0 0; }}
        .content {{ background-color: #f9fafb; padding: 30px; border: 1px solid #e5e7eb; }}
        .button {{ display: inline-block; background-color: #4F46E5; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; margin: 20px 0; }}
        .deadline {{ background-color: #FEF3C7; padding: 10px; border-left: 4px solid #F59E0B; margin: 15px 0; }}
        .footer {{ text-align: center; padding: 20px; color: #6b7280; font-size: 12px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>ストレスチェックのお願い</h1>
        </div>
        <div class="content">
            <p><strong>{employee_name}</strong> 様</p>
            <p>お疲れ様です。<br>{company_name} の定期ストレスチェックの受検期間となっております。</p>
            <p>まだ受検がお済みでない場合は、下記のボタンより受検をお願いいたします。</p>
            <p style="text-align: center;">
                <a href="{check_url}" class="button">ストレスチェックを受検する</a>
            </p>
            <div class="deadline">
                <strong>受検期限:</strong> {deadline.strftime('%Y年%m月%d日')}
            </div>
            <p>ストレスチェックは、労働安全衛生法に基づき実施しております。<br>
            皆様の心身の健康を守るための大切な取り組みですので、ぜひご協力をお願いいたします。</p>
        </div>
        <div class="footer">
            <p>このメールは自動送信されています。<br>
            ご不明な点がございましたら、人事部までお問い合わせください。</p>
            <p>{company_name} | StressAgent Pro</p>
        </div>
    </div>
</body>
</html>"""
        return subject, text_body, html_body

    @staticmethod
    def high_stress_followup_email(
        employee_name: str,
        company_name: str,
        consultation_url: str,
        support_email: str
    ) -> tuple[str, str, str]:
        """高ストレス者へのフォローアップメール"""
        subject = f"【{company_name}】ストレスチェック結果に関するご案内"

        text_body = f"""
{employee_name} 様

お疲れ様です。
先日はストレスチェックの受検にご協力いただき、ありがとうございました。

今回の結果を確認したところ、ストレスの負担が高まっている可能性がございます。
ご自身の心身の健康を守るため、以下のサポートをご用意しておりますので、
お気軽にご利用ください。

【ご利用いただけるサポート】

1. 産業医面談の申し込み
   専門の産業医による個別面談を受けることができます。
   面談内容は厳密に守秘されますので、安心してご相談ください。
   申し込みURL: {consultation_url}

2. 相談窓口へのご連絡
   メールでのご相談も承っております。
   連絡先: {support_email}

3. AIチャットサポート
   24時間いつでもご相談いただけます。
   アプリ内の「チャット」機能をご利用ください。

ご自身の健康を守ることは、とても大切なことです。
少しでも気になることがございましたら、遠慮なくご相談ください。

※このメールは個人情報保護のため、受検者本人のみに送信されています。
※結果の詳細は、ご本人の同意なく第三者に開示されることはありません。

--
{company_name}
StressAgent Pro
"""

        html_body = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body {{ font-family: 'Hiragino Sans', 'Meiryo', sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background-color: #7C3AED; color: white; padding: 20px; text-align: center; border-radius: 8px 8px 0 0; }}
        .content {{ background-color: #f9fafb; padding: 30px; border: 1px solid #e5e7eb; }}
        .support-box {{ background-color: white; padding: 20px; border-radius: 8px; margin: 15px 0; border: 1px solid #e5e7eb; }}
        .support-title {{ color: #7C3AED; font-weight: bold; margin-bottom: 10px; }}
        .button {{ display: inline-block; background-color: #7C3AED; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; }}
        .notice {{ background-color: #EDE9FE; padding: 15px; border-radius: 8px; margin-top: 20px; font-size: 14px; }}
        .footer {{ text-align: center; padding: 20px; color: #6b7280; font-size: 12px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>ストレスチェック結果のご案内</h1>
        </div>
        <div class="content">
            <p><strong>{employee_name}</strong> 様</p>
            <p>お疲れ様です。<br>先日はストレスチェックの受検にご協力いただき、ありがとうございました。</p>
            <p>今回の結果を確認したところ、ストレスの負担が高まっている可能性がございます。<br>
            ご自身の心身の健康を守るため、以下のサポートをご用意しておりますので、お気軽にご利用ください。</p>
            <div class="support-box">
                <div class="support-title">1. 産業医面談の申し込み</div>
                <p>専門の産業医による個別面談を受けることができます。<br>
                面談内容は厳密に守秘されますので、安心してご相談ください。</p>
                <a href="{consultation_url}" class="button">面談を申し込む</a>
            </div>
            <div class="support-box">
                <div class="support-title">2. 相談窓口へのご連絡</div>
                <p>メールでのご相談も承っております。</p>
                <p><strong>連絡先:</strong> <a href="mailto:{support_email}">{support_email}</a></p>
            </div>
            <div class="support-box">
                <div class="support-title">3. AIチャットサポート</div>
                <p>24時間いつでもご相談いただけます。<br>
                アプリ内の「チャット」機能をご利用ください。</p>
            </div>
            <div class="notice">
                <p><strong>ご安心ください</strong></p>
                <p>このメールは個人情報保護のため、受検者本人のみに送信されています。<br>
                結果の詳細は、ご本人の同意なく第三者に開示されることはありません。</p>
            </div>
        </div>
        <div class="footer">
            <p>ご自身の健康を守ることは、とても大切なことです。<br>
            少しでも気になることがございましたら、遠慮なくご相談ください。</p>
            <p>{company_name} | StressAgent Pro</p>
        </div>
    </div>
</body>
</html>"""
        return subject, text_body, html_body

    @staticmethod
    def completion_notification_email(
        employee_name: str,
        company_name: str,
        check_date: date,
        result_url: str,
        is_high_stress: bool = False
    ) -> tuple[str, str, str]:
        """ストレスチェック完了通知"""
        subject = f"【{company_name}】ストレスチェック完了のお知らせ"

        high_stress_notice = ""
        high_stress_html = ""
        if is_high_stress:
            high_stress_notice = """
【重要なお知らせ】
今回の結果から、ストレスの負担が高まっている可能性がございます。
別途、サポートに関するご案内をお送りいたしますので、ご確認ください。
"""
            high_stress_html = """
            <div style="background-color: #FEE2E2; padding: 15px; border-radius: 8px; margin: 15px 0; border-left: 4px solid #EF4444;">
                <p style="color: #991B1B; margin: 0;"><strong>重要なお知らせ</strong></p>
                <p style="margin: 10px 0 0 0;">今回の結果から、ストレスの負担が高まっている可能性がございます。<br>
                別途、サポートに関するご案内をお送りいたしますので、ご確認ください。</p>
            </div>"""

        text_body = f"""
{employee_name} 様

お疲れ様です。
ストレスチェックの受検が完了いたしました。ご協力ありがとうございました。

【受検情報】
受検日: {check_date.strftime('%Y年%m月%d日')}

結果は以下のURLからご確認いただけます。
結果URL: {result_url}
{high_stress_notice}
ストレスチェックの結果は、ご自身の健康管理にお役立てください。
日々のセルフケアとして、以下のことを心がけていただくと効果的です。

- 十分な睡眠をとる
- 適度な運動を行う
- 趣味やリラックスできる時間を確保する
- 悩みがあれば、信頼できる人に相談する

何かご不明な点がございましたら、お気軽にお問い合わせください。

--
{company_name}
StressAgent Pro
"""

        html_body = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body {{ font-family: 'Hiragino Sans', 'Meiryo', sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background-color: #10B981; color: white; padding: 20px; text-align: center; border-radius: 8px 8px 0 0; }}
        .content {{ background-color: #f9fafb; padding: 30px; border: 1px solid #e5e7eb; }}
        .info-box {{ background-color: white; padding: 15px; border-radius: 8px; margin: 15px 0; border: 1px solid #e5e7eb; }}
        .button {{ display: inline-block; background-color: #10B981; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; }}
        .tips {{ background-color: #ECFDF5; padding: 20px; border-radius: 8px; margin: 20px 0; }}
        .tips-title {{ color: #065F46; font-weight: bold; margin-bottom: 10px; }}
        .tips ul {{ margin: 0; padding-left: 20px; }}
        .footer {{ text-align: center; padding: 20px; color: #6b7280; font-size: 12px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>ストレスチェック完了</h1>
        </div>
        <div class="content">
            <p><strong>{employee_name}</strong> 様</p>
            <p>お疲れ様です。<br>ストレスチェックの受検が完了いたしました。ご協力ありがとうございました。</p>
            <div class="info-box">
                <p><strong>受検日:</strong> {check_date.strftime('%Y年%m月%d日')}</p>
            </div>
            <p style="text-align: center;">
                <a href="{result_url}" class="button">結果を確認する</a>
            </p>
            {high_stress_html}
            <div class="tips">
                <div class="tips-title">日々のセルフケアのヒント</div>
                <ul>
                    <li>十分な睡眠をとる</li>
                    <li>適度な運動を行う</li>
                    <li>趣味やリラックスできる時間を確保する</li>
                    <li>悩みがあれば、信頼できる人に相談する</li>
                </ul>
            </div>
        </div>
        <div class="footer">
            <p>何かご不明な点がございましたら、お気軽にお問い合わせください。</p>
            <p>{company_name} | StressAgent Pro</p>
        </div>
    </div>
</body>
</html>"""
        return subject, text_body, html_body


class EmailService:
    """メール送信サービス"""

    def __init__(self, config: Optional[EmailConfig] = None):
        self.config = config or EmailConfig.from_env()

    async def send_email(
        self,
        to_email: str,
        subject: str,
        text_body: str,
        html_body: Optional[str] = None
    ) -> bool:
        """メールを送信"""
        try:
            if self.config.provider == EmailProvider.SMTP:
                return await self._send_via_smtp(to_email, subject, text_body, html_body)
            elif self.config.provider == EmailProvider.SENDGRID:
                return await self._send_via_sendgrid(to_email, subject, text_body, html_body)
            elif self.config.provider == EmailProvider.MAILGUN:
                return await self._send_via_mailgun(to_email, subject, text_body, html_body)
            elif self.config.provider == EmailProvider.RESEND:
                return await self._send_via_resend(to_email, subject, text_body, html_body)
            else:
                logger.error(f"Unknown email provider: {self.config.provider}")
                return False
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {e}")
            return False

    async def _send_via_smtp(
        self,
        to_email: str,
        subject: str,
        text_body: str,
        html_body: Optional[str] = None
    ) -> bool:
        """SMTPでメール送信"""
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"{self.config.from_name} <{self.config.from_email}>"
        msg["To"] = to_email

        part1 = MIMEText(text_body, "plain", "utf-8")
        msg.attach(part1)

        if html_body:
            part2 = MIMEText(html_body, "html", "utf-8")
            msg.attach(part2)

        try:
            if self.config.smtp_use_tls:
                server = smtplib.SMTP(self.config.smtp_host, self.config.smtp_port)
                server.starttls()
            else:
                server = smtplib.SMTP_SSL(self.config.smtp_host, self.config.smtp_port)

            if self.config.smtp_username and self.config.smtp_password:
                server.login(self.config.smtp_username, self.config.smtp_password)

            server.sendmail(self.config.from_email, [to_email], msg.as_string())
            server.quit()
            logger.info(f"Email sent successfully to {to_email}")
            return True
        except smtplib.SMTPException as e:
            logger.error(f"SMTP error: {e}")
            return False

    async def _send_via_sendgrid(
        self,
        to_email: str,
        subject: str,
        text_body: str,
        html_body: Optional[str] = None
    ) -> bool:
        """SendGridでメール送信"""
        try:
            from sendgrid import SendGridAPIClient
            from sendgrid.helpers.mail import Mail, Content

            message = Mail(
                from_email=(self.config.from_email, self.config.from_name),
                to_emails=to_email,
                subject=subject,
            )
            message.add_content(Content("text/plain", text_body))
            if html_body:
                message.add_content(Content("text/html", html_body))

            sg = SendGridAPIClient(self.config.api_key)
            response = sg.send(message)

            if response.status_code in [200, 201, 202]:
                logger.info(f"Email sent via SendGrid to {to_email}")
                return True
            else:
                logger.error(f"SendGrid error: {response.status_code}")
                return False
        except ImportError:
            logger.error("sendgrid package not installed. Run: pip install sendgrid")
            return False
        except Exception as e:
            logger.error(f"SendGrid error: {e}")
            return False

    async def _send_via_mailgun(
        self,
        to_email: str,
        subject: str,
        text_body: str,
        html_body: Optional[str] = None
    ) -> bool:
        """Mailgunでメール送信"""
        try:
            import httpx

            data = {
                "from": f"{self.config.from_name} <{self.config.from_email}>",
                "to": to_email,
                "subject": subject,
                "text": text_body,
            }
            if html_body:
                data["html"] = html_body

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"https://api.mailgun.net/v3/{self.config.mailgun_domain}/messages",
                    auth=("api", self.config.api_key),
                    data=data,
                )

            if response.status_code == 200:
                logger.info(f"Email sent via Mailgun to {to_email}")
                return True
            else:
                logger.error(f"Mailgun error: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            logger.error(f"Mailgun error: {e}")
            return False

    async def _send_via_resend(
        self,
        to_email: str,
        subject: str,
        text_body: str,
        html_body: Optional[str] = None
    ) -> bool:
        """Resendでメール送信"""
        try:
            import httpx

            if not self.config.api_key:
                logger.error("Resend APIキーが設定されていません")
                return False

            payload = {
                "from": f"{self.config.from_name} <{self.config.from_email}>",
                "to": [to_email],
                "subject": subject,
                "text": text_body
            }
            if html_body:
                payload["html"] = html_body

            headers = {
                "Authorization": f"Bearer {self.config.api_key}",
                "Content-Type": "application/json"
            }

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://api.resend.com/emails",
                    json=payload,
                    headers=headers
                )

            if 200 <= response.status_code < 300:
                logger.info(f"Email sent via Resend to {to_email}")
                return True
            else:
                logger.error(f"Resend error: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            logger.error(f"Resend error: {e}")
            return False

    async def send_reminder_email(
        self,
        to_email: str,
        employee_name: str,
        company_name: str,
        deadline: date,
        check_url: str
    ) -> bool:
        """リマインドメール送信"""
        subject, text_body, html_body = EmailTemplate.reminder_email(
            employee_name, company_name, deadline, check_url
        )
        return await self.send_email(to_email, subject, text_body, html_body)

    async def send_high_stress_followup_email(
        self,
        to_email: str,
        employee_name: str,
        company_name: str,
        consultation_url: str,
        support_email: str
    ) -> bool:
        """高ストレス者フォローアップメール送信"""
        subject, text_body, html_body = EmailTemplate.high_stress_followup_email(
            employee_name, company_name, consultation_url, support_email
        )
        return await self.send_email(to_email, subject, text_body, html_body)

    async def send_completion_notification_email(
        self,
        to_email: str,
        employee_name: str,
        company_name: str,
        check_date: date,
        result_url: str,
        is_high_stress: bool = False
    ) -> bool:
        """ストレスチェック完了通知メール送信"""
        subject, text_body, html_body = EmailTemplate.completion_notification_email(
            employee_name, company_name, check_date, result_url, is_high_stress
        )
        return await self.send_email(to_email, subject, text_body, html_body)


# シングルトンインスタンス
email_service = EmailService()
