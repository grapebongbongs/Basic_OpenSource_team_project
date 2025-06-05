function scaleUI() {
  const baseWidth = 2560;  // 기준 너비
  const currentWidth = window.innerWidth;
  const scale = currentWidth / baseWidth;

  const wrapper = document.querySelector('.div-wrapper');
  if (wrapper) {
    wrapper.style.transform = `scale(${scale})`;
  }
}

// 페이지 로드 시, 리사이즈 시 실행
window.addEventListener('load', scaleUI);
window.addEventListener('resize', scaleUI);




let activeRegion = null;

function loadRepresentativeData(daesu, region) {
  return fetch(`/api/representative-data/?daesu=${daesu}&region=${region}`)
    .then(res => res.json())
    .then(data => {
      console.log('후처리된 대표자 데이터:', data);
      // 해당 지역의 대표자 배열만 반환
      return data[region] || [];
    })
    .catch(err => {
      console.error('의원 API 오류:', err);
      return [];
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
  const regionNameTextWrapper = document.querySelector('.text-wrapper-2');
  const scrollBar = document.querySelector('.view-3');
  const scrollThumb = document.getElementById('scroll-thumb');
  
  let isDragging = false;
  let startY = 0;
  let startTop = 0;
  
  function updateThumbHeight() {
    const scrollBarHeight = scrollBar.clientHeight;
    const contentRatio = regionInfo.clientHeight / regionInfo.scrollHeight;
  
    if (contentRatio >= 1) {
      scrollThumb.style.display = 'none';
      return 0;
    } else {
      scrollThumb.style.display = 'block';
    }
  
    const thumbHeight = Math.max(scrollBarHeight * contentRatio, 30);
    scrollThumb.style.height = thumbHeight + 'px';
    return thumbHeight;
  }
  
  function getMaxScroll() {
    return regionInfo.scrollHeight - regionInfo.clientHeight;
  }
  
  function getMaxThumbTop(thumbHeight) {
    return scrollBar.clientHeight - thumbHeight;
  }
  
  function updateThumbPosition() {
    const thumbHeight = updateThumbHeight();
    if (thumbHeight === 0) return;
  
    const maxThumbTop = getMaxThumbTop(thumbHeight);
    const maxScroll = getMaxScroll();
  
    if (maxScroll <= 0) {
      scrollThumb.style.top = '0px';
      return;
    }
  
    const scrollRatio = regionInfo.scrollTop / maxScroll;
    scrollThumb.style.top = (scrollRatio * maxThumbTop) + 'px';
  }
  
  function checkScrollVisibility() {
    if (regionInfo.scrollHeight <= regionInfo.clientHeight) {
      scrollBar.style.display = 'none';
    } else {
      scrollBar.style.display = 'block';
    }
  }
  
  regionInfo.addEventListener('scroll', updateThumbPosition);
  
  window.addEventListener('resize', () => {
    updateThumbPosition();
    checkScrollVisibility();
  });
  
  scrollThumb.addEventListener('mousedown', (e) => {
    isDragging = true;
    startY = e.clientY;
    startTop = parseFloat(scrollThumb.style.top) || 0;
    e.preventDefault();
    e.stopPropagation();
  });
  
  document.addEventListener('mousemove', (e) => {
    if (!isDragging) return;
    const thumbHeight = updateThumbHeight();
    const maxThumbTop = getMaxThumbTop(thumbHeight);
  
    let deltaY = e.clientY - startY;
    let newTop = startTop + deltaY;
  
    if (newTop < 0) newTop = 0;
    if (newTop > maxThumbTop) newTop = maxThumbTop;
  
    scrollThumb.style.top = newTop + 'px';
  
    const scrollRatio = newTop / maxThumbTop;
    regionInfo.scrollTop = scrollRatio * getMaxScroll();
  });
  
  document.addEventListener('mouseup', () => {
    isDragging = false;
  });
  
  scrollBar.addEventListener('click', (e) => {
    if (isDragging) return;
    if (e.target === scrollThumb) return;
  
    const rect = scrollBar.getBoundingClientRect();
    const clickY = e.clientY - rect.top;
  
    const thumbHeight = updateThumbHeight();
    if (thumbHeight === 0) return;
  
    const maxThumbTop = getMaxThumbTop(thumbHeight);
  
    let newTop = clickY - (thumbHeight / 2);
  
    if (newTop < 0) newTop = 0;
    if (newTop > maxThumbTop) newTop = maxThumbTop;
  
    scrollThumb.style.top = newTop + 'px';
  
    const scrollRatio = newTop / maxThumbTop;
    regionInfo.scrollTop = scrollRatio * getMaxScroll();
  });
  
  // 초기화
  checkScrollVisibility();
  updateThumbPosition();

  let partyData = {};
  let repDataCache = {};  // region 단위 캐시
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
    repDataCache = {};  // 대수 변경 시 캐시 초기화
    console.log(`데이터 로딩 중, 대수: ${daesu}`);
    fetch(`/api/party-data/?daesu=${daesu}`)
      .then(res => res.json())
      .then(party => {
        partyData = party;
        updateMapColors();
        setupClickEvents();
        if (activeRegion) {
          activeRegion.click();
        }
      })
      .catch(err => {
        console.error('정당 데이터 로딩 오류:', err);
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
    const svg = document.querySelector('svg');
    regions.forEach(elem => {
      elem.onclick = async (e) => {
        e.stopPropagation();
        if (activeRegion) {
          activeRegion.classList.remove('active-region');
          activeRegion.style.transform = '';
          activeRegion.style.transition = '';
        }

        
        elem.classList.add('active-region');
        activeRegion = elem;

        elem.parentNode.appendChild(elem);
        elem.style.transition = 'transform 0.3s ease';
        elem.style.transform = 'translate(5px, -5px)';

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

        if (parties?.length > 0) {
          drawPartyPieChart(parties);
        } else {
          rectangle.innerHTML = '<p>정당 정보 없음</p>';
        }

        // 의원 데이터 비동기 로딩
        if (!repDataCache[region]) {
          repDataCache[region] = await loadRepresentativeData(currentDaesu, region);
        }
        const reps = repDataCache[region];

        if (reps?.length > 0) {
                // 정당별로 그룹화
                const grouped = {};
                reps.forEach(r => {
                  if (!grouped[r.party]) grouped[r.party] = [];
                  grouped[r.party].push(r.name);
                });

                // 리스트 초기화
                repList.innerHTML = '';
                // 정당별 반복
                Object.entries(grouped).forEach(([party, names]) => {
                  const divider = document.createElement('hr');
                  divider.style.border = 'none';
                  divider.style.borderTop = '1px solid #ccc';
                  divider.style.margin = '8px 0';
                  repList.appendChild(divider);
                
                  const partyColor = partyColors[party] || '#2c3e50'; // 여기서 색상 설정
                
                  const partyItem = document.createElement('li');
                  partyItem.innerHTML = `<span style="font-weight: bold; font-size: 1em; color: ${partyColor};">${party}</span>`;
                  partyItem.style.margin = '4px 0';
                  repList.appendChild(partyItem);
                
                  names.forEach(name => {
                    const li = document.createElement('li');
                    li.textContent = `- ${name}`;
                    li.style.marginLeft = '12px';
                    li.style.color = '#333';
                    li.style.fontSize = '0.95em';
                    repList.appendChild(li);
                  });
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
          elem.parentNode.appendChild(elem);
          elem.style.transition = 'transform 0.3s ease';
          elem.style.transform = 'translate(5px, -5px)';
          elem.style.stroke = '#000';
          elem.style.strokeWidth = '2';

          if (activeRegion) {
            regions.forEach(r => {
              if (r !== activeRegion && r !== elem) {
                r.style.opacity = '0.3';
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

            regions.forEach(r => {
              r.style.opacity = '1';
            });

            if(regionNameTextWrapper) {
              regionNameTextWrapper.textContent = '지역명';
            }
            regionName.textContent = '';
            regionInfo.classList.add('hidden');
          }
        };
      }
    });
  }

  slider.addEventListener('input', () => {
    const daesu = slider.value;
    selectedDaesu.textContent = `${daesu}대`;
    loadAllData(daesu);
  });

  selectedDaesu.textContent = `${slider.value}대`;
  loadAllData(slider.value);

  const menuBtn = document.getElementById('menu-button');
  const slideMenu = document.getElementById('slide-menu');

  menuBtn.addEventListener('click', function () {
    slideMenu.classList.toggle('active');
  });

});
