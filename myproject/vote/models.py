from django.db import models
from members.models import AssemblyMember
from agendas.models import Bill  # 의안 모델도 가져온다고 가정

class Vote(models.Model):
    bill = models.ForeignKey(Bill, on_delete=models.CASCADE, related_name='votes')
    member = models.ForeignKey(AssemblyMember, on_delete=models.CASCADE, related_name='votes')
    vote_result = models.CharField(max_length=10)  # 예: 찬성 / 반대 / 기권