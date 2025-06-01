let activeRegion = null;

function loadRepresentativeData(daesu, region) {
  return fetch(`/api/representative-data/?daesu=${daesu}&region=${region}`)
    .then(res => res.json())
    .catch(err => {
      console.error('의원 API 오류:', err);
      return {};
    });
}


function loadRegionData(regionId) {
  const regionInfoBox = document.getElementById('region-info'); // 상세 정보 박스
  const regionName = document.getElementById('region-name');
  const partyList = document.getElementById('party-list');
  const repList = document.getElementById('rep-list');

  // 대수를 사용하여 API 호출
  fetch(`/api/representative-data/?daesu=${regionId}`)
    .then(res => res.json())
    .then(data => {
      // 지역 이름 업데이트
      regionName.textContent = data.regionName;

      // 정당 목록 업데이트
      partyList.innerHTML = '<li><strong>정당 분포</strong></li>';
      data.parties.forEach(party => {
        const li = document.createElement('li');
        li.textContent = `${party.name} - ${party.percentage}%`;
        partyList.appendChild(li);
      });

      // 국회의원 목록 업데이트
      repList.innerHTML = '<li><strong>국회의원</strong></li>';
      data.representatives.forEach(rep => {
        const li = document.createElement('li');
        li.textContent = `${rep.name} (${rep.party})`;
        repList.appendChild(li);
      });

      // 상세 정보 박스를 보여주기
      regionInfoBox.style.display = 'block';
    })
    .catch(err => {
      console.error('지역 데이터 로딩 오류:', err);
    });
}

// 페이지 로딩 후 지역 클릭 이벤트 설정
document.addEventListener('DOMContentLoaded', () => {
  const paths = document.querySelectorAll('#map svg path');
  
  paths.forEach(path => {
    path.addEventListener('click', () => {
      const regionId = path.id;  // 지역의 ID를 가져옵니다.
      console.log('Clicked region:', regionId);
      
      // 슬라이더 대수 값 가져오기
      const daesu = document.getElementById('daesu-slider').value;
      // 클릭한 지역의 정보 로딩
      loadRegionData(daesu, regionId);
    });
  });

  // 슬라이더 변경 시 대수 정보 업데이트
  const slider = document.getElementById('daesu-slider');
  const selectedDaesu = document.getElementById('selected-daesu');
  
  slider.addEventListener('input', () => {
    const daesu = slider.value;  // 슬라이더에서 대수를 가져옴
    selectedDaesu.textContent = `${daesu}대`;
    // 슬라이더 값에 따라 지역 데이터 로드
    const region = document.getElementById('region-name').textContent;
    loadRegionData(daesu, region);  // 대수와 지역을 전달하여 지역 데이터 로드
  });

  // 초기 데이터 로드
  selectedDaesu.textContent = `${slider.value}대`;
  loadRegionData(slider.value, '서울');  // 첫 페이지 로딩 시 기본 지역 '서울'에 대한 데이터 로드
});

document.addEventListener('DOMContentLoaded', () => {
  const slider = document.getElementById('daesu-slider');
  const selectedDaesu = document.getElementById('selected-daesu');
  const partyList = document.getElementById('party-list');
  const regionInfo = document.getElementById('region-info'); // 중괄호 추가
  const regionName = document.getElementById('region-name');


  let partyData = {};
  let repData = {};

  const partyColors = {
    '더불어민주당': '#152484',
    '새정치민주연합': '#0082CD',
    '새누리당' : '#C9252B',
    '국민의힘': '#E61E2B',
    '통합진보당' : '#782B90',
    '자유한국당' : '#C9151E',
    '정의당': '#FFED00',
    '무소속': '#808080',
    '열린민주당': '#003E98',
    '미래통합당': '#EF426F',
    '미래한국당': '#EF426F',
    '열린우리당' :'#ffd918',
    '국민의당': '#EA5504',
    '한나라당' : '#0000A8',
    '평화민주당' : '#FADA5E',
    '민주정의당' : '#004C97',
    '신민주공화당' : '#59955E',
    '민주자유당' : '#003990',
    '통일민주당' : '#E60026',
    '신민당' : '#DC352A',
    '민주한국당' : '#ED2939',
    '신한민주당' : '#E6573B',
    '신정치개혁당': '#050099',
    '민주공화당' : '#835B38',
    '통일국민당' : '#22B14C',
    '새정치국민회의' : '#009A44',
    '14-민주당' : '#D82634',
    '자유민주연합' : '#1B5B40',
    '신한국당' : '#003990',
    '새천년민주당' : '#00AA7B',
    '통합민주당' : '#419639',
    '열린우리당' : '#ffd918',
    '민주당' : '#019E33',
    '자유선진당' : '#00529C',
    '통합민주당' : '#419639',
  };

  function loadAllData(daesu) {
    currentDaesu = daesu;
    console.log(`데이터 로딩 중, 대수: ${daesu}`);
    Promise.all([
      fetch(`/api/party-data/?daesu=${daesu}`).then(res => res.json()),
      loadRepresentativeData(daesu),
    ])
    .then(([party, reps]) => {
      partyData = party;
      repData = reps;
      updateMapColors();
      setupClickEvents();
    })
    .catch(err => {
      console.error('데이터 로딩 오류:', err);
    });
  }

  function updateMapColors() {
    document.querySelectorAll('[data-region]').forEach(elem => {
      const region = elem.getAttribute('data-region');
      const regionParties = partyData[region];

      if (regionParties && regionParties.length > 0) {
        const topParty = regionParties.sort((a, b) => b.percentage - a.percentage)[0];
        const partyKey = (currentDaesu === '14' && topParty.party === '민주당')
          ? '14-민주당'
          : topParty.party;

        elem.style.fill = partyColors[partyKey] || '#cccccc';
        elem.style.cursor = 'pointer';
        elem.style.pointerEvents = 'all';
      } else {
        elem.style.fill = '#eeeeee';
        elem.style.cursor = 'default';
        elem.style.pointerEvents = 'none';
      }

      // 마우스 오버 시 테두리 효과 추가
      elem.addEventListener('mouseenter', () => {
        if (!elem.classList.contains('active-region')) { // 클릭된 지역 제외
          elem.style.stroke = '#000'; // 테두리 색
          elem.style.strokeWidth = '2'; // 테두리 두께
        }
      });

      elem.addEventListener('mouseleave', () => {
        if (!elem.classList.contains('active-region')) { // 클릭된 지역 제외
          elem.style.stroke = ''; // 테두리 제거
          elem.style.strokeWidth = ''; // 테두리 두께 제거
        }
      });
    });
  }

  function setupClickEvents() {
    document.querySelectorAll('g[region]').forEach(elem => {
      elem.onclick = () => {
        // 1. 기존 강조 제거
        if (activeRegion) {
          activeRegion.classList.remove('active-region');
        }
  
        // 2. 새 강조 추가
        elem.classList.add('active-region');
        activeRegion = elem;
  
        const region = elem.getAttribute('region');
        regionName.textContent = region;
        partyList.innerHTML = '';
  
        const parties = partyData[region];
        const reps = repData[region];
  
        if (parties?.length > 0) {
          const header = document.createElement('li');
          header.innerHTML = '<strong>정당 분포</strong>';
          partyList.appendChild(header);
  
          parties.forEach(p => {
            const li = document.createElement('li');
            const percent = p.percentage?.toFixed(1) ?? 0;
            li.textContent = `${p.party} - ${percent}%`;
            partyList.appendChild(li);
          });
        } else {
          const li = document.createElement('li');
          li.textContent = '정당 정보 없음';
          partyList.appendChild(li);
        }
  
        if (reps?.length > 0) {
          const repHeader = document.createElement('li');
          repHeader.innerHTML = '<strong>국회의원</strong>';
          partyList.appendChild(repHeader);
  
          reps.forEach(r => {
            const li = document.createElement('li');
            li.textContent = `${r.name} (${r.party})`;
            partyList.appendChild(li);
          });
        } else {
          const li = document.createElement('li');
          li.textContent = '국회의원 정보 없음';
          partyList.appendChild(li);
        }
  
        regionInfo.classList.remove('hidden');
      };
    });
  }
  

  slider.addEventListener('input', () => {
    const daesu = slider.value;
    selectedDaesu.textContent = `${daesu}대`;
    loadAllData(daesu);
  });

  selectedDaesu.textContent = `${slider.value}대`;
  loadAllData(slider.value);


});
