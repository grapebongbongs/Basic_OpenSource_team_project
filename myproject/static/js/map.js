document.addEventListener("DOMContentLoaded", () => {
  const slider     = document.getElementById("daesu-slider");
  const yearLabel  = document.getElementById("selected-daesu");
  const infoBox    = document.getElementById("region-info");
  const regionName = document.getElementById("region-name");
  const partyList  = document.getElementById("party-list");
  const svgObj     = document.getElementById("sk-obj");

  // 1) SVG 로드 완료 후 실행
  svgObj.addEventListener("load", () => {
    const svgDoc = svgObj.contentDocument;
    const regions = svgDoc.querySelectorAll("path[data-region]");

    // 2) 클릭 이벤트 등록
    regions.forEach(path => {
      path.addEventListener("click", () => {
        const region = path.getAttribute("data-region");
        fetchDataAndShow(region, slider.value); // 선택된 지역의 정보와 정당 비율 표시
      });
    });

    // 3) 슬라이더 변경 시 지도 색칠
    function repaint(year) {
      fetch(`/api/party-data/?year=${year}`)
        .then(res => res.json())
        .then(data => {
          console.log(data);  // 응답 데이터 확인
          yearLabel.textContent = year;

          regions.forEach(path => {
            const region = path.getAttribute("data-region");
            const parties = data[region] || [];
            if (parties.length) {
              const major = parties.reduce((a, b) => a.percentage > b.percentage ? a : b);
              path.setAttribute("fill", getPartyColor(major.party)); // 주요 정당 색상 적용
            } else {
              path.setAttribute("fill", "#ccc"); // 데이터가 없으면 회색으로 처리
            }
          });
        });
    }

    slider.addEventListener("input", () => repaint(slider.value)); // 슬라이더 값 변경 시 repaint 호출
    repaint(slider.value); // 초기 로드 시 repaint 호출

    // 4) 상세 정보 표시
    function fetchDataAndShow(region, year) {
      fetch(`/api/party-data/?year=${year}`)
        .then(res => res.json())
        .then(data => {
          const parties = data[region] || [];
          regionName.textContent = region;
          partyList.innerHTML = parties
            .map(p => `<li>${p.party}: ${p.percentage}%</li>`)
            .join("");
          infoBox.classList.remove("hidden");
        });
    }
  });
});

// 5) 정당별 색상 매핑 함수
function getPartyColor(partyName) {
  const colors = {
    "더불어민주당": "#1f77b4",
    "국민의힘":     "#d62728",
    "정의당":       "#ff7f0e",
    "기타":         "#999"
  };
  return colors[partyName] || "#ccc";  // 기본 색상 설정
}
