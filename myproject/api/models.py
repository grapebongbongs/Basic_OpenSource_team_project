from django.db import models

class Bill(models.Model):
    daesu = models.IntegerField(max_length=50, default='0', null=True)
    SCH_KIND = models.CharField(max_length=20)      # 일정종류
    SCH_CN = models.TextField()                      # 일정내용
    SCH_DT = models.CharField(max_length=100)        # 일자
    SCH_TM = models.CharField(max_length=50, default="0000-00-00", null=True)  # 시간
    CONF_DIV = models.CharField(max_length=50, default='0', null=True)         # 회의구분
    CMIT_NM = models.CharField(max_length=50, default='0', null=True)         # 위원회명
    CONF_SESS = models.CharField(max_length=50, default='0', null=True)       # 회의회기
    CONF_DGR = models.CharField(max_length=50, default='0', null=True)        # 회의차수
    EV_INST_NM = models.CharField(max_length=50, default='0', null=True)      # 행사주체자
    EV_PLC = models.CharField(max_length=50, default='0', null=True)          # 행사장소

    def save(self, *args, **kwargs):
        self.search_keyword = f"{self.CMIT_NM} {self.SCH_CN}"  # 검색 키워드 생성
        super().save(*args, **kwargs)
        
    def __str__(self):
        return f"[{self.SCH_KIND}] {self.SCH_CN}"

class PartyDistribution(models.Model):
    daesu = models.IntegerField()        # 국회의원 대수
    region = models.CharField(max_length=50)  # 지역 (시·도)
    party = models.CharField(max_length=50)   # 정당
    percentage = models.FloatField()         # 정당 비율
    count = models.IntegerField(default=0)   # 지역구에서 해당 정당의 후보 수

    def __str__(self):
        return f"{self.daesu}대 {self.region} - {self.party}: {self.percentage}% ({self.count}명)"
    
    # 정당 비율 계산 메소드
    def calculate_percentage(self, total_count):
        if total_count > 0:
            self.percentage = (self.count / total_count) * 100
        else:
            self.percentage = 0


class Representative(models.Model):
    name = models.CharField(max_length=100)
    party = models.CharField(max_length=100)
    region = models.CharField(max_length=100)
    year = models.IntegerField()

    def __str__(self):
        return f"{self.year}년 {self.name} ({self.party}) - {self.region}"