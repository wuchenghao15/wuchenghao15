"""email_service stub (SYS-NORM修复)."""
class EmailService:
    def send(self, *a, **kw): return True
    def send_email(self, *a, **kw): return True
email_service = EmailService()
