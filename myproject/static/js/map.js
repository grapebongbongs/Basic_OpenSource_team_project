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
    '더불어민주당': '#3c9ee5',
    '국민의힘': '#e60026',
    '정의당': '#ffcb08',
    '무소속': '#999999',
    '열린민주당': '#4a9fdd',
    '미래통합당': '#d61f69',
    '미래한국당': '#ff7f50',
    '국민의당': '#ffa500',
  };

  function loadAllData(daesu) {
    console.log(`데이터 로딩 중, 대수: ${daesu}`); // 대수 값 확인
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
        elem.style.fill = partyColors[topParty.party] || '#cccccc';
        elem.style.cursor = 'pointer';
        elem.style.pointerEvents = 'all';
      } else {
        elem.style.fill = '#eeeeee';
        elem.style.cursor = 'default';
        elem.style.pointerEvents = 'none';
      }
    });
  }

  function setupClickEvents() {
    document.querySelectorAll('[data-region]').forEach(elem => {
      elem.onclick = () => {
        const region = elem.getAttribute('data-region');
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

  selectedDaesu.textContent = `${slider.value}대`; // 초기 대수 표시
  loadAllData(slider.value); // 초기 데이터 로드

  if (menuButton && dropdownMenu) {
    menuButton.addEventListener('click', (e) => {
      e.stopPropagation();
      dropdownMenu.classList.toggle('hidden');
    });

    document.addEventListener('click', (e) => {
      if (!menuButton.contains(e.target) && !dropdownMenu.contains(e.target)) {
        dropdownMenu.classList.add('hidden');
      }
    });
  }
});
