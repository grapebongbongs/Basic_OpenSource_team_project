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
  const repList = document.getElementById('rep-list');
  const regionInfo = document.getElementById('region-info');
  const regionName = document.getElementById('region-name');
  const rectangle = document.querySelector('.rectangle');
  const regionNameTextWrapper = document.querySelector('.text-wrapper-2'); // 추가: 동적 지역명 변경용

  const menuButton = document.getElementById('menu-button');
  const dropdownMenu = document.getElementById('dropdown-menu');

  let partyData = {};
  let repData = {};
  let currentDaesu = slider.value;

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

  // Chart.js 파이 차트 그리기 함수
  function drawPartyPieChart(partyData) {
    let canvas = rectangle.querySelector('canvas#party-chart');
    if (!canvas) {
      canvas = document.createElement('canvas');
      canvas.id = 'party-chart';
      canvas.width = 300;
      canvas.height = 300;
      rectangle.innerHTML = '';
      rectangle.appendChild(canvas);
    }
    const ctx = canvas.getContext('2d');

    if(window.partyChart) {
      window.partyChart.destroy();
    }

    window.partyChart = new Chart(ctx, {
      type: 'pie',
      data: {
        labels: partyData.map(p => p.party),
        datasets: [{
          data: partyData.map(p => p.percentage),
          backgroundColor: partyData.map(p => partyColors[p.party] || '#cccccc'),
          borderWidth: 1,
          borderColor: '#fff',
        }]
      },
      options: {
        responsive: false,
        layout: {
          padding: {
            top: 20,
            bottom: 20,
            left: 10,
            right: 10
          }
        },
        plugins: {
          legend: {
            position: 'bottom',
            labels: {
              boxWidth: 12,
              padding: 25,
            }
          },
          tooltip: {
            callbacks: {
              label: context => `${context.label} - ${context.parsed}%`
            }
          },
          datalabels: {
            color: '#000',
            font: {
              size: 10,
              weight: 'bold',
            },
            formatter: (value, context) => {
              return value.toFixed(1) + '%';
            },
            anchor: 'end',
            align: 'end',
            offset: 5,
          }
        }
      },
      plugins: [ChartDataLabels],
    });
    
    }

  

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
      if (activeRegion) {
        activeRegion.click();
      }
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

      elem.addEventListener('mouseenter', () => {
        if (!elem.classList.contains('active-region')) {
          elem.style.stroke = '#000';
          elem.style.strokeWidth = '2';
        }
      });

      elem.addEventListener('mouseleave', () => {
        if (!elem.classList.contains('active-region')) {
          elem.style.stroke = '';
          elem.style.strokeWidth = '';
        }
      });
    });
  }
  
  function setupClickEvents() {
    const regions = document.querySelectorAll('g[region]');
    const svg = document.querySelector('svg');  // SVG 전체 영역 선택 (필요 시 변경)
    regions.forEach(elem => {
      elem.onclick = (e) => {
        e.stopPropagation();  // 이벤트 버블링 막기: 빈 공간 클릭과 구분
        
        if (activeRegion) {
          activeRegion.classList.remove('active-region');
          activeRegion.style.transform = '';
          activeRegion.style.transition = '';
        }
        
        elem.classList.add('active-region');
        activeRegion = elem;
        
        // 맨 앞으로 이동
        const parent = elem.parentNode;
        parent.appendChild(elem);
        
        elem.style.transition = 'transform 0.3s ease';
        elem.style.transform = 'translate(5px, -5px)';
        
        // 다른 지역 불투명도 조정
        regions.forEach(r => {
          r.style.opacity = (r === activeRegion) ? '1' : '0.4';
        });
        
        const region = elem.getAttribute('region');
        if(regionNameTextWrapper) {
          regionNameTextWrapper.textContent = region;
        }
        regionName.textContent = region;
        
        partyList.innerHTML = '';
        repList.innerHTML = '';
        
        const parties = partyData[region];
        const reps = repData[region];
        
        if (parties?.length > 0) {
          drawPartyPieChart(parties);
        } else {
          rectangle.innerHTML = '<p>정당 정보 없음</p>';
        }
        
        if (reps?.length > 0) {
          const repHeader = document.createElement('li');
          repHeader.innerHTML = '<strong>국회의원</strong>';
          repList.appendChild(repHeader);
          
          reps.forEach(r => {
            const li = document.createElement('li');
            li.textContent = `${r.name} (${r.party})`;
            repList.appendChild(li);
          });
        } else {
          const li = document.createElement('li');
          li.textContent = '국회의원 정보 없음';
          repList.appendChild(li);
        }
        
        regionInfo.classList.remove('hidden');
      };
      
      elem.addEventListener('mouseenter', () => {
        if (elem !== activeRegion) {
          const parent = elem.parentNode;
          parent.appendChild(elem);
          
          elem.style.transition = 'transform 0.3s ease';
          elem.style.transform = 'translate(5px, -5px)';
          elem.style.stroke = '#000';
          elem.style.strokeWidth = '2';
          
          // 선택된 지역이 있으면 나머지 지역 불투명도 조정
          if (activeRegion) {
            regions.forEach(r => {
              if (r !== activeRegion && r !== elem) {
                r.style.opacity = '0.3'; // 더 연하게
              } else {
                r.style.opacity = '1';
              }
            });
          }
        }
      });
      
      elem.addEventListener('mouseleave', () => {
        if (elem !== activeRegion) {
          elem.style.transition = 'transform 0.3s ease';
          elem.style.transform = '';
          elem.style.stroke = '';
          elem.style.strokeWidth = '';
          
          // 선택된 지역이 있으면 나머지는 불투명도 0.4, 없으면 모두 1
          if (activeRegion) {
            regions.forEach(r => {
              r.style.opacity = (r === activeRegion) ? '1' : '0.4';
            });
          } else {
            regions.forEach(r => {
              r.style.opacity = '1';
            });
          }
        }
      });
      if (svg) {
        svg.onclick = () => {
          if (activeRegion) {
            activeRegion.classList.remove('active-region');
            activeRegion.style.transform = '';
            activeRegion.style.transition = '';
            activeRegion = null;
    
            // 모든 지역 불투명도 원래대로
            regions.forEach(r => {
              r.style.opacity = '1';
            });
    
            // 지역명 텍스트 초기화 (필요 시)
            if(regionNameTextWrapper) {
              regionNameTextWrapper.textContent = '지역명';
            }
            regionName.textContent = '';
    
            // 정보 박스 숨기기
            regionInfo.classList.add('hidden');
    
            // 기타 필요한 초기화 작업 추가 가능
          }
        };
      }
    }
    );
    
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
