let activeRegion = null;

function loadRepresentativeData(daesu, region) {
  return fetch(`/api/representative-data/?daesu=${daesu}&region=${region}`)
    .then(res => res.json())
    .catch(err => {
      console.error('의원 API 오류:', err);
      return {};
    });
}

document.addEventListener('DOMContentLoaded', () => {
  const slider = document.getElementById('daesu-slider');
  const selectedDaesu = document.getElementById('selected-daesu');
  const partyList = document.getElementById('party-list');
  const regionInfo = document.getElementById('region-info'); // 중괄호 추가
  const regionName = document.getElementById('region-name');

  const menuButton = document.getElementById('menu-button');
  const dropdownMenu = document.getElementById('dropdown-menu');

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

  if (menuButton && dropdownMenu) {
    menuButton.addEventListener('click', (e) => {
      e.stopPropagation();
      dropdownMenu.classList.toggle('show');
    });

    document.addEventListener('click', (e) => {
      if (!menuButton.contains(e.target) && !dropdownMenu.contains(e.target)) {
        dropdownMenu.classList.remove('show');
      }
    });
  }
});
