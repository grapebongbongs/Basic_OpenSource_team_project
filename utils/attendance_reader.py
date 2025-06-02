import pandas as pd

def get_member_attendance_from_424(filepath, name, party):
    df = pd.read_excel(filepath, skiprows=2)

    # 열 이름 재정의
    df = df.rename(columns={
        df.columns[0]: '의원명',
        df.columns[1]: '소속정당',
        df.columns[15]: '회의일수',
        df.columns[16]: '출석',
        df.columns[17]: '결석',
        df.columns[18]: '청가',
        df.columns[19]: '출장',
        df.columns[20]: '결석신고서',
    })

    # 숫자형으로 안전하게 변환
    for col in ['회의일수', '출석', '결석', '청가', '출장', '결석신고서']:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)

    row = df[(df['의원명'] == name) & (df['소속정당'] == party)]

    if row.empty:
        print(f"⚠️ 해당 의원 정보 없음: {name}, {party}")
        return None

    row = row.iloc[0]
    total = row['회의일수']
    if total == 0:
        return {
            'name': name,
            'party': party,
            '출석률': 0,
            '무단결석률': 0,
            '기타결석률': 0
        }

    attended = row['출석']
    unexcused = row['결석']
    etc = row['청가'] + row['출장'] + row['결석신고서']

    출석률 = round(attended / total * 100, 2)
    무단결석률 = round(unexcused / total * 100, 2)
    기타결석률 = round(etc / total * 100, 2)

    return {
        'name': name,
        'party': party,
        '출석률': float(출석률),
        '무단결석률': float(무단결석률),
        '기타결석률': float(기타결석률)
    }


def get_member_attendance_20(filepath, name, party):
    # ❶ 헤더가 4번째 행(0-index 3)에 있으므로 header=3
    df = pd.read_excel(filepath, header=3).rename(columns=str.strip)

    # ❷ 열 이름 매핑
    col = {
        "total": "본회의\n전체회의수",
        "attend": "출석 (횟수)",
        "absent": "무단결석 (횟수)",
        "leave": "청가 (횟수)",
        "trip": "출장 (횟수)",
        "district": "현재 선거구",
        "party": "정당",
        "name": "의원이름",
    }

    # ❸ 숫자 열 안전 변환
    num_cols = [col["total"], col["attend"], col["absent"],
                col["leave"], col["trip"]]
    df[num_cols] = df[num_cols].apply(
        lambda s: pd.to_numeric(s, errors="coerce").fillna(0).astype(int))

    row = df[(df[col["name"]] == name) & (df[col["party"]]  == party)]
    if row.empty:
        return None                 # 이름이 없으면 None
    

    row = row.iloc[0]
    total = row[col["total"]]

    if total == 0:                  # 회의일수가 0이면 모두 0
        return {
            "name": name,
            "party": row[col["party"]],
            "district": row[col["district"]],
            "출석률": 0,
            "무단결석률": 0,
            "기타결석률": 0,
        }

    attend = row[col["attend"]]
    absent = row[col["absent"]]
    etc = row[col["leave"]] + row[col["trip"]]  # 결석신고서는 청가에 이미 합산돼 있음

    return {
        "name": name,
        "party": row[col["party"]],
        "출석률": float(round(attend / total * 100, 2)),
        "무단결석률": float(round(absent / total * 100, 2)),
        "기타결석률": float(round(etc / total * 100, 2)),
    }




def get_member_attendance_21(filepath: str, name: str, party: str | None = None) -> dict | None:
    """
    (열려라국회) 21대 국회 본회의 출석부.xlsx  ➜
    · 출석률 · 무단결석률 · 기타결석률 · 현재 선거구  계산
    · 이름만, 또는 이름+정당으로 1 명의 행을 찾음
      └  party=None  →  이름만 비교
    · 열 표기가 달라도 (‘성명’ / ‘의원이름’ / ‘이름’ …) 자동 인식
    · 헤더 행을 자동으로 찾아서 누락 오류 방지
    """

    # ───────────────────────────────────────
    # 1) 헤더 행(0-based index) 자동 탐지
    # ───────────────────────────────────────
    probe = pd.read_excel(filepath, header=None, nrows=10)  # 처음 10행만
    header_row = None
    name_aliases  = {"성명", "의원이름", "이름"}
    for i, row in probe.iterrows():
        if any(str(cell).strip() in name_aliases for cell in row):
            header_row = i
            break
    if header_row is None:
        raise ValueError("⚠️ '성명/의원이름/이름' 열을 찾지 못했습니다 – 헤더 행 위치 불명")

    # ───────────────────────────────────────
    # 2) 본 데이터 로드 + 열 이름 문자열·strip
    # ───────────────────────────────────────
    df = pd.read_excel(filepath, header=header_row)
    df.columns = df.columns.map(lambda c: str(c).strip())

    # ───────────────────────────────────────
    # 3) 열 이름 후보 매핑 함수
    # ───────────────────────────────────────
    def pick(*cands):
        for c in cands:
            if c in df.columns:
                return c
        raise KeyError(f"열 이름 없음: {cands}")

    col = {
        "name"    : pick("성명", "의원이름", "이름"),
        "party"   : pick("정당", "소속정당"),
        "district": pick("현재 선거구", "현재선거구", "선거구"),
        "total"   : pick("본회의수(회)", "본회의전체회의수"),
        "attend"  : pick("출석(회)", "출석"),
        "absent"  : pick("무단결석(회)", "무단결석"),
        "leave"   : pick("청가(회)", "청가"),
        "trip"    : pick("출장(회)", "출장"),
        # notice 열은 있을 수도, 없을 수도
    }
    notice_col = next((c for c in df.columns if "결석신고서" in c), None)

    # ───────────────────────────────────────
    # 4) 숫자 열 안전 변환
    # ───────────────────────────────────────
    num_cols = [col[k] for k in ("total", "attend", "absent", "leave", "trip")]
    if notice_col:
        num_cols.append(notice_col)

    df[num_cols] = df[num_cols].apply(
        lambda s: pd.to_numeric(s, errors="coerce").fillna(0).astype(int)
    )

    # ───────────────────────────────────────
    # 5) 의원 행 찾기
    # ───────────────────────────────────────
    cond = df[col["name"]] == name
    if party is not None:
        cond &= df[col["party"]] == party
    row = df[cond]
    if row.empty:
        print(f"⚠️ 의원을 찾지 못했습니다: {name}{' / '+party if party else ''}")
        return None
    row = row.iloc[0]

    total   = row[col["total"]]
    attend  = row[col["attend"]]
    absent  = row[col["absent"]]
    etc     = row[col["leave"]] + row[col["trip"]]
    if notice_col:
        etc += row[notice_col]

    if total == 0:
        attend_rate = absent_rate = etc_rate = 0.0
    else:
        attend_rate = round(attend / total * 100, 2)
        absent_rate = round(absent / total * 100, 2)
        etc_rate    = round(etc / total * 100, 2)

    return {
        "name"        : row[col["name"]],
        "party"       : row[col["party"]],
        "출석률"       : float(attend_rate),
        "무단결석률"    : float(absent_rate),
        "기타결석률"    : float(etc_rate),
    }
