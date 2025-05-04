from django.db import models

class Bill(models.Model):
    bill_no = models.CharField(max_length=50, unique=True)
    bill_name = models.CharField(max_length=200)
    proposer = models.CharField(max_length=100, blank=True, null=True)
    propose_dt = models.CharField(max_length=20, blank=True, null=True)
    committee = models.CharField(max_length=100, blank=True, null=True)
    proc_result = models.CharField(max_length=100, blank=True, null=True)
    bill_kind = models.CharField(max_length=100, blank=True, null=True)
    age = models.CharField(max_length=10, blank=True, null=True)

    def __str__(self):
        return self.bill_name
