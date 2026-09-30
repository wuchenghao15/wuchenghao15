"""sms_service stub (SYS-NORM修复)."""
class SMSService:
    def send(self, *a, **kw): return True
sms_service = SMSService()
