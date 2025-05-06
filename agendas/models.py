from django.db import models

class Bill(models.Model):
    bill_id = models.CharField(max_length=100, unique=True, null=True)  # 의안 ID
    bill_no = models.CharField(max_length=50, null=True)
    bill_name = models.CharField(max_length=200)
    proposer = models.CharField(max_length=100, blank=True, null=True)
    rgs_proc_dt = models.CharField(max_length=50, blank=True, null=True) # 의결일자자
    committee = models.CharField(max_length=100, blank=True, null=True)
    proc_result = models.CharField(max_length=100, blank=True, null=True)
    bill_kind = models.CharField(max_length=100, blank=True, null=True)
    age = models.CharField(max_length=10, blank=True, null=True)

    def __str__(self):
        return self.bill_name
