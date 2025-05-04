from django.db import models

class AssemblyMember(models.Model):
    name = models.CharField(max_length=20)  # 의원 이름름
    mona_cd = models.CharField(max_length=20, unique=True)  # 의원번호
    party = models.CharField(max_length=100, null=True)  # 정당당
    committee = models.CharField(max_length=100, null=True)  # 위원회 이름름
    elect_gbn = models.CharField(max_length=20, null=True)  # 초선 or 재선
    origin = models.CharField(max_length=100, null=True)  # 지역구구
    position = models.CharField(max_length=100, null=True)  # 위원회에서의 역할할
    email = models.EmailField(null=True)  # 이메일일
    phone = models.CharField(max_length=100, null=True)  # 사무실 전화번호
    homepage = models.URLField(null=True)  # 의원 홈페이지지
    unit = models.CharField(max_length=50, null=True)  # 국회의원 대수(몇 대인지지)
    title = models.TextField(null=True)  # 약력
    image_url = models.URLField(blank=True, null=True)  # 의원 사진 URL
    
    def __str__(self):
        return self.name